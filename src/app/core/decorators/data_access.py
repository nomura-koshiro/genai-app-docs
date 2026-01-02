"""データアクセス関連デコレータ。

トランザクション管理、キャッシュ管理など、データアクセスに関する
横断的関心事を扱うデコレータを提供します。
"""

import hashlib
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from app.core.cache import cache_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


def transactional[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """データベーストランザクションを自動管理するデコレータ。

    関数が正常終了した場合は自動的にコミット、例外が発生した場合は
    自動的にロールバックすることで、トランザクション管理を簡素化します。

    トランザクション処理フロー:
        1. 関数を実行
        2. 成功: db.commit() を自動実行
        3. 失敗: db.rollback() を自動実行 → 例外を再送出

    対象オブジェクト:
        - 関数の第1引数（self）が db または _db 属性を持つ必要がある
        - db属性が存在しない場合は通常の関数として実行（デコレータ無効）

    Args:
        func: デコレート対象の非同期関数
            - サービスクラスのメソッドを想定
            - selfにdbセッション属性が必要

    Returns:
        Callable: トランザクション管理が適用された関数

    Example:
        >>> class UserService:
        ...     def __init__(self, db: AsyncSession):
        ...         self.db = db
        ...
        ...     @transactional
        ...     async def create_user(self, user_data: UserCreate):
        ...         user = await self.repository.create(user_data)
        ...         # 成功時: 自動コミット
        ...         # 失敗時: 自動ロールバック
        ...         return user

    Note:
        - サービス層のCRUD操作に推奨
        - db属性が見つからない場合は通常実行（エラーなし）
        - ネストされたトランザクションには対応していない
        - ロールバック時はERRORログが記録される（structlog形式）

    Warning:
        - 長時間実行される処理には使用しない（ロック競合のリスク）
        - 既にコミット済みのトランザクションを再度コミットしないよう注意
        - データベースセッションのライフサイクルはFastAPIのDependsで管理を推奨
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        # 最初の引数がselfで、dbセッションを持っていると仮定
        instance = args[0] if args else None
        db = getattr(instance, "db", None)
        if db is None:
            db = getattr(instance, "_db", None)

        if db is None:
            # dbがない場合は通常実行（トランザクション管理なし）
            logger.debug(
                "transactional_decorator_skipped",
                function=func.__name__,
                reason="no_db_attribute",
                hint="Instance should have 'db' or '_db' attribute for transaction management",
            )
            return await func(*args, **kwargs)

        try:
            result = await func(*args, **kwargs)
            await db.commit()
            logger.debug(
                "transaction_committed",
                function=func.__name__,
            )
            return result
        except Exception as e:
            await db.rollback()
            logger.error(
                "transaction_rolled_back",
                function=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise

    return wrapper


def cache_result(ttl: int = 300, key_prefix: str = "func"):
    """関数の結果をRedisにキャッシュするデコレータ。

    頻繁にアクセスされる読み取り専用データ（ユーザー情報、設定情報など）に
    キャッシュを適用し、データベースクエリやAPI呼び出しを削減します。

    キャッシュキーの生成:
        - 関数名と引数からハッシュを生成して一意性を保証
        - プレフィックスにより機能別にキャッシュを分離

    キャッシュ戦略:
        - Cache-Aside パターン
        - キャッシュヒット: Redisから即座に返却
        - キャッシュミス: 関数実行後にRedisに保存

    Args:
        ttl (int): キャッシュの有効期限（秒）
            - デフォルト: 300秒（5分）
            - 0: 無期限（非推奨、明示的削除が必要）
        key_prefix (str): キャッシュキーのプレフィックス
            - デフォルト: "func"
            - 例: "user", "config", "api_response"

    Returns:
        Callable: キャッシュ機能が適用されたデコレータ

    Example:
        >>> @cache_result(ttl=3600, key_prefix="user")
        >>> async def get_user_profile(user_id: int):
        ...     return await db.get_user(user_id)
        >>>
        >>> # 1回目: データベースから取得 → キャッシュに保存
        >>> user = await get_user_profile(123)
        >>> # 2回目以降（1時間以内）: キャッシュから即座に返却
        >>> user = await get_user_profile(123)

    Note:
        - Redis未接続時は通常の関数として動作（グレースフルデグラデーション）
        - 引数が変わると別のキャッシュキーが生成される
        - データ更新時は cache_manager.delete() で手動削除が必要
        - キャッシュキーはSHA256ハッシュの先頭16文字を使用
          （衝突確率: 約 1/2^64 ≈ 5.4×10^-20、実用上問題なし）
        - より高い安全性が必要な場合は、ハッシュ長を32文字に拡張可能
        - ログは structlog 形式で出力される

    Warning:
        - 頻繁に更新されるデータには使用しない（データ不整合のリスク）
        - 大きなデータのキャッシュはメモリ使用量に注意
        - データ更新時のキャッシュ無効化を忘れずに実装
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # キャッシュキーを生成（関数名 + 引数のハッシュ）
            args_str = f"{args}:{kwargs}"
            args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:16]
            cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"

            # キャッシュから取得試行
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(
                    "cache_hit",
                    function=func.__name__,
                    cache_key=cache_key,
                    key_prefix=key_prefix,
                )
                return cached

            # キャッシュミスの場合は実行
            logger.debug(
                "cache_miss",
                function=func.__name__,
                cache_key=cache_key,
                key_prefix=key_prefix,
            )
            result = await func(*args, **kwargs)

            # 結果をキャッシュに保存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
