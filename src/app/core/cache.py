"""Redisを使用したアプリケーションキャッシュ管理システム。

このモジュールは、Redisをバックエンドとしたキャッシュシステムを提供します。
データベースクエリ結果やAPI応答のキャッシュにより、アプリケーションの
パフォーマンスを向上させます。グレースフルデグラデーション設計により、
Redis接続エラー時もアプリケーションは正常に動作します。

主な機能:
    キャッシュ操作:
        - get(): データ取得
        - set(): データ保存（TTL設定可能）
        - delete(): データ削除
        - exists(): 存在チェック
        - clear(): パターン一致削除

    接続管理:
        - connect(): Redis接続確立
        - disconnect(): Redis接続切断

    キー管理:
        - 自動プレフィックス付与（APP_NAME:ENVIRONMENT:key_prefix:key）
        - 環境別キー分離（開発・ステージング・本番）

グレースフルデグラデーション:
    Redis接続エラー時の動作:
        - get(): None を返す（キャッシュミス扱い）
        - set(): False を返す（データベースから直接取得）
        - delete(), exists(), clear(): False を返す
        - アプリケーションは正常動作を継続

キープレフィックス構造:
    {APP_NAME}:{ENVIRONMENT}:{key_prefix}:{key}

    例（開発環境）:
        - APP_NAME: training-tracker
        - ENVIRONMENT: development
        - key_prefix: user
        - key: 123
        → 完全キー: "training-tracker:development:user:123"

使用方法:
    >>> from app.core.cache import cache_manager
    >>>
    >>> # アプリケーション起動時（main.py）
    >>> await cache_manager.connect()
    >>>
    >>> # データのキャッシュ
    >>> user_data = {"id": 123, "name": "John"}
    >>> await cache_manager.set("user:123", user_data, expire=3600)  # 1時間
    >>>
    >>> # キャッシュからの取得
    >>> cached_user = await cache_manager.get("user:123")
    >>> if cached_user:
    ...     print(f"Cache hit: {cached_user}")
    ... else:
    ...     # データベースから取得
    ...     cached_user = await db.get_user(123)
    ...     await cache_manager.set("user:123", cached_user, expire=3600)
    >>>
    >>> # キャッシュ削除（データ更新時）
    >>> await cache_manager.delete("user:123")
    >>>
    >>> # パターン一致削除
    >>> await cache_manager.clear("user:*")  # 全ユーザーキャッシュ削除

キャッシュ戦略:
    - 短TTL（60秒）: 頻繁に更新されるデータ（統計情報等）
    - 中TTL（3600秒 = 1時間）: 比較的安定したデータ（ユーザー情報等）
    - 長TTL（86400秒 = 24時間）: ほぼ不変のデータ（マスターデータ等）
    - 無期限: 明示的に削除されるまで保持（TTL=0）

データシリアライゼーション:
    - JSON形式で保存（json.dumps/json.loads）
    - ensure_ascii=False で日本語もそのまま保存
    - datetime等はdefault=strで文字列に変換

Note:
    - REDIS_URLが設定されていない場合、キャッシュは無効化されます
    - 本番環境では必ずREDIS_URLを設定してください
    - キャッシュ無効時もアプリケーションは正常動作します（グレースフルデグラデーション）
    - シャットダウン時は必ず disconnect() を呼び出してください
"""

import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Redisベースのキャッシュ管理クラス。

    このクラスは、Redisを使用したキャッシュシステムの管理を担当します。
    自動プレフィックス付与、TTL管理、グレースフルデグラデーションを実装し、
    アプリケーション全体で一貫したキャッシュ操作を提供します。

    機能:
        - CRUD操作（get, set, delete）
        - 存在チェック（exists）
        - パターン一致削除（clear）
        - 自動キープレフィックス付与
        - TTL（Time To Live）管理
        - エラーハンドリング（グレースフルデグラデーション）

    Attributes:
        _redis (Redis[str] | None): Redisクライアントインスタンス
            - None: 未接続またはREDIS_URL未設定
            - Redis[str]: 接続済み (decode_responses=True)
        key_prefix (str): キャッシュキーのプレフィックス
            フォーマット: "{APP_NAME}:{ENVIRONMENT}:{key_prefix}"

    使用方法:
        >>> # グローバルインスタンス（推奨）
        >>> from app.core.cache import cache_manager
        >>> await cache_manager.connect()
        >>> await cache_manager.set("key", "value", expire=3600)
        >>> value = await cache_manager.get("key")
        >>>
        >>> # カスタムプレフィックス
        >>> custom_cache = CacheManager(key_prefix="session")
        >>> await custom_cache.connect()
        >>> await custom_cache.set("user:123", session_data)

    Note:
        - グローバルインスタンス cache_manager を使用することを推奨
        - カスタムプレフィックスは機能別キャッシュ分離に有効
        - Redis接続エラーは自動的にハンドリングされます
    """

    def __init__(self, key_prefix: str = "app"):
        """CacheManagerを初期化します。

        キープレフィックスを設定し、Redisクライアントインスタンスを初期化します。
        実際のRedis接続は connect() メソッドで確立します。

        Args:
            key_prefix (str): キャッシュキーのプレフィックス（デフォルト: "app"）
                - 機能別にキャッシュを分離する場合に指定
                - 例: "user", "session", "api"
                - 完全プレフィックス: "{APP_NAME}:{ENVIRONMENT}:{key_prefix}"

        Example:
            >>> # デフォルトプレフィックス
            >>> cache = CacheManager()
            >>> # key_prefix = "training-tracker:development:app"
            >>>
            >>> # カスタムプレフィックス
            >>> user_cache = CacheManager(key_prefix="user")
            >>> # key_prefix = "training-tracker:development:user"
            >>>
            >>> session_cache = CacheManager(key_prefix="session")
            >>> # key_prefix = "training-tracker:development:session"

        Note:
            - プレフィックスには環境情報が自動的に含まれます
            - 開発・ステージング・本番環境でキーが自動的に分離されます
            - Redis接続は __init__ では確立されません（connect() を呼び出す必要があります）
        """
        self._redis: Redis[str] | None = None
        self.key_prefix = f"{settings.APP_NAME}:{settings.ENVIRONMENT}:{key_prefix}"

    def _make_key(self, key: str) -> str:
        """キープレフィックスを元のキーに付与して完全なキーを生成します。

        このメソッドは、環境別・機能別にキャッシュを分離するために、
        すべてのキーに自動的にプレフィックスを付与します。

        Args:
            key (str): 元のキー
                例: "user:123", "session:abc", "data"

        Returns:
            str: プレフィックスを含む完全なキー
                フォーマット: "{key_prefix}:{key}"
                例: "training-tracker:development:app:user:123"

        Example:
            >>> cache = CacheManager(key_prefix="user")
            >>> full_key = cache._make_key("123")
            >>> print(full_key)
            training-tracker:development:user:123
            >>>
            >>> # ネストされたキー
            >>> full_key = cache._make_key("profile:123")
            >>> print(full_key)
            training-tracker:development:user:profile:123

        Note:
            - このメソッドは内部使用のみを想定（private method）
            - プレフィックスにより、環境・機能別にキーが自動分離されます
            - キー衝突を防ぐため、意味のあるキー名を使用してください
        """
        return f"{self.key_prefix}:{key}"

    async def connect(self) -> None:
        """Redisサーバーへの接続を確立します。

        このメソッドは、アプリケーション起動時に呼び出され、Redis接続を初期化します。
        REDIS_URLが設定されていない場合、接続は確立されず、キャッシュは無効化されます
        （グレースフルデグラデーション）。

        接続設定:
            - encoding: utf-8（日本語対応）
            - decode_responses: True（自動デコード）
            - 接続プール: 自動管理（redis.asyncio）

        Example:
            >>> from app.core.cache import cache_manager
            >>>
            >>> # アプリケーション起動時（main.py）
            >>> await cache_manager.connect()
            >>> # 以降、キャッシュ操作が可能
            >>>
            >>> # 接続確認
            >>> if cache_manager._redis:
            ...     print("Redis connected")

        Note:
            - この関数はアプリケーション起動時に1回だけ呼び出してください
            - REDIS_URLが未設定の場合、接続はスキップされます（エラーなし）
            - 接続エラーは例外として伝播されます（アプリケーション起動失敗）
            - 非同期関数なので await が必要です

        Raises:
            ConnectionError: Redis接続に失敗した場合
            ValueError: REDIS_URLの形式が不正な場合
        """
        if settings.REDIS_URL:
            self._redis = await Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Redisサーバーへの接続を切断します。

        このメソッドは、アプリケーションシャットダウン時に呼び出され、
        Redis接続を正常にクローズします。接続プールのクリーンアップも実行されます。

        Example:
            >>> from app.core.cache import cache_manager
            >>>
            >>> # アプリケーションシャットダウン時（main.py）
            >>> await cache_manager.disconnect()
            >>> # Redis接続がクリーンに切断される
            >>>
            >>> # 手動での切断
            >>> if cache_manager._redis:
            ...     await cache_manager.disconnect()

        Note:
            - この関数はアプリケーション終了時に1回だけ呼び出してください
            - 接続が存在しない場合（_redis=None）、何もしません
            - 非同期関数なので await が必要です
            - 切断後はキャッシュ操作ができなくなります（再度connect()が必要）
        """
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Any | None:
        """キャッシュからデータを取得します。

        指定されたキーに対応するキャッシュデータを取得します。
        データが存在しない場合やRedis接続エラー時はNoneを返します
        （グレースフルデグラデーション）。

        Args:
            key (str): キャッシュキー
                例: "user:123", "session:abc"
                完全キー: "{key_prefix}:{key}" に自動変換

        Returns:
            Any | None: キャッシュされたデータ
                - キャッシュヒット: デシリアライズされたPythonオブジェクト
                - キャッシュミス: None
                - Redis未接続: None
                - エラー時: None（ログに記録）

        Example:
            >>> # ユーザーデータ取得
            >>> user = await cache_manager.get("user:123")
            >>> if user:
            ...     print(f"Cache hit: {user['name']}")
            ... else:
            ...     # データベースから取得
            ...     user = await db.get_user(123)
            ...     await cache_manager.set("user:123", user, expire=3600)
            >>>
            >>> # セッションデータ取得
            >>> session = await cache_manager.get("session:abc123")
            >>> if session:
            ...     print(f"Session found: {session}")

        Note:
            - データはJSON形式でRedisに保存されています
            - 取得時に自動的にPythonオブジェクトにデシリアライズされます
            - Redis接続エラーはログに記録され、Noneを返します
            - アプリケーションは正常に動作を継続します（キャッシュなしモード）
        """
        if not self._redis:
            return None

        full_key = self._make_key(key)
        try:
            value = await self._redis.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.exception(
                "キャッシュ取得エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return None  # エラー時はキャッシュなしとして動作

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """データをキャッシュに保存します。

        指定されたキーにデータを保存し、オプションでTTL（有効期限）を設定します。
        データはJSON形式でシリアライズされてRedisに保存されます。

        Args:
            key (str): キャッシュキー
                例: "user:123", "session:abc"
                完全キー: "{key_prefix}:{key}" に自動変換
            value (Any): キャッシュするデータ
                - dict, list, str, int, float等、JSON変換可能な型
                - datetime等は自動的にstr変換されます
            expire (int | None): 有効期限（秒）
                - None: デフォルトTTL（settings.CACHE_TTL）を使用
                - 0: 無期限（明示的削除まで保持）
                - 正の整数: 指定秒数後に自動削除

        Returns:
            bool: 成功時True、失敗時False
                - True: データ保存成功
                - False: Redis未接続またはエラー

        Example:
            >>> # デフォルトTTLで保存
            >>> user_data = {"id": 123, "name": "John", "email": "john@example.com"}
            >>> success = await cache_manager.set("user:123", user_data)
            >>>
            >>> # カスタムTTL（1時間）で保存
            >>> await cache_manager.set("user:123", user_data, expire=3600)
            >>>
            >>> # 無期限保存
            >>> await cache_manager.set("config", config_data, expire=0)
            >>>
            >>> # datetimeを含むデータ
            >>> from datetime import datetime, UTC
            >>> log_data = {"timestamp": datetime.now(UTC), "event": "login"}
            >>> await cache_manager.set("log:123", log_data, expire=60)

        Note:
            - データはJSON形式でシリアライズされます
            - ensure_ascii=Falseで日本語も正しく保存されます
            - datetime等の非JSON型はdefault=strで自動変換されます
            - Redis接続エラーはログに記録され、Falseを返します
            - エラー時もアプリケーションは正常に動作を継続します
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            ttl = expire if expire is not None else settings.CACHE_TTL

            if ttl > 0:
                await self._redis.setex(full_key, ttl, serialized)
            else:
                await self._redis.set(full_key, serialized)
            return True
        except Exception as e:
            logger.exception(
                "キャッシュ設定エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False

    async def delete(self, key: str) -> bool:
        """キャッシュからデータを削除します。

        指定されたキーに対応するキャッシュデータを削除します。
        データ更新時やユーザーログアウト時にキャッシュを無効化する際に使用します。

        Args:
            key (str): キャッシュキー
                例: "user:123", "session:abc"
                完全キー: "{key_prefix}:{key}" に自動変換

        Returns:
            bool: 成功時True、失敗時False
                - True: データ削除成功（キーが存在しない場合も含む）
                - False: Redis未接続またはエラー

        Example:
            >>> # ユーザーデータ更新時にキャッシュ削除
            >>> await db.update_user(123, new_data)
            >>> await cache_manager.delete("user:123")
            >>>
            >>> # ログアウト時にセッションキャッシュ削除
            >>> await cache_manager.delete("session:abc123")
            >>>
            >>> # 複数キー削除
            >>> for user_id in [123, 456, 789]:
            ...     await cache_manager.delete(f"user:{user_id}")

        Note:
            - キーが存在しない場合でもTrueを返します
            - Redis接続エラーはログに記録され、Falseを返します
            - データ更新時は必ずキャッシュを削除してください（整合性維持）
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            await self._redis.delete(full_key)
            return True
        except Exception as e:
            logger.exception(
                "キャッシュ削除エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False

    async def exists(self, key: str) -> bool:
        """キャッシュキーが存在するかチェックします。

        指定されたキーがキャッシュ内に存在するかを確認します。
        データ取得前の存在確認や、キャッシュヒット率の計測に使用します。

        Args:
            key (str): キャッシュキー
                例: "user:123", "session:abc"
                完全キー: "{key_prefix}:{key}" に自動変換

        Returns:
            bool: 存在する場合True、存在しない場合またはエラー時False
                - True: キーが存在する
                - False: キーが存在しない、Redis未接続、またはエラー

        Example:
            >>> # キャッシュ存在確認
            >>> if await cache_manager.exists("user:123"):
            ...     user = await cache_manager.get("user:123")
            ... else:
            ...     user = await db.get_user(123)
            ...     await cache_manager.set("user:123", user, expire=3600)
            >>>
            >>> # キャッシュヒット率計測
            >>> total_requests = 100
            >>> cache_hits = 0
            >>> for user_id in range(1, total_requests + 1):
            ...     if await cache_manager.exists(f"user:{user_id}"):
            ...         cache_hits += 1
            >>> hit_rate = cache_hits / total_requests * 100
            >>> print(f"Cache hit rate: {hit_rate}%")

        Note:
            - exists()とget()を連続で呼ぶより、get()だけを呼ぶ方が効率的です
            - Redis接続エラーはログに記録され、Falseを返します
            - TTL切れの直前にTrue判定される場合があります（競合状態）
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            return await self._redis.exists(full_key) > 0
        except Exception as e:
            logger.exception(
                "キャッシュ存在確認エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False

    async def clear(self, pattern: str = "*") -> bool:
        """パターンに一致するキャッシュをすべて削除します。

        指定されたパターンに一致するすべてのキーを削除します。
        ユーザーの全キャッシュ削除や、機能別キャッシュのクリアに使用します。

        Args:
            pattern (str): キーパターン（デフォルト: "*" すべて）
                - "*": すべてのキー
                - "user:*": user:で始まるすべてのキー
                - "*:profile": :profileで終わるすべてのキー
                - 完全パターン: "{key_prefix}:{pattern}" に自動変換

        Returns:
            bool: 成功時True、失敗時False
                - True: 削除成功（一致するキーがない場合も含む）
                - False: Redis未接続またはエラー

        Example:
            >>> # 特定ユーザーの全キャッシュ削除
            >>> await cache_manager.clear("user:123:*")
            >>>
            >>> # 全ユーザーキャッシュ削除
            >>> await cache_manager.clear("user:*")
            >>>
            >>> # すべてのキャッシュクリア（危険）
            >>> await cache_manager.clear("*")
            >>>
            >>> # セッションキャッシュのみクリア
            >>> await cache_manager.clear("session:*")

        Note:
            - SCAN操作により、大量のキーでもブロッキングしません
            - パターンマッチングはRedis標準のglob形式です
            - "*" パターンは全キャッシュを削除するため、本番環境では注意してください
            - Redis接続エラーはログに記録され、Falseを返します
            - 削除は非トランザクションで行われます（途中でエラーが発生する可能性）

        Warning:
            - 大量のキー削除はRedisサーバーに負荷をかけます
            - 本番環境での全キャッシュクリア（"*"）は慎重に実行してください
        """
        if not self._redis:
            return False

        full_pattern = self._make_key(pattern)
        try:
            async for key in self._redis.scan_iter(match=full_pattern):
                await self._redis.delete(key)
            return True
        except Exception as e:
            logger.exception(
                "キャッシュクリアエラー",
                pattern=full_pattern,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False

    # ========================================================================
    # Public API for advanced Redis operations (レート制限等で使用)
    # ========================================================================

    def is_redis_available(self) -> bool:
        """Redis接続が利用可能かを確認します。

        Returns:
            bool: Redis接続が確立されている場合True、それ以外False
        """
        return self._redis is not None

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Sorted Setから指定スコア範囲の要素を削除します（レート制限用）。

        Args:
            key (str): Sorted Setのキー
            min_score (float): 最小スコア
            max_score (float): 最大スコア

        Returns:
            int: 削除された要素数（Redis未接続時は0）
        """
        if not self._redis:
            return 0

        full_key = self._make_key(key)
        try:
            return await self._redis.zremrangebyscore(full_key, min_score, max_score)
        except Exception as e:
            logger.exception(
                "Sorted Set範囲削除エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return 0

    async def zcard(self, key: str) -> int:
        """Sorted Setの要素数を取得します（レート制限用）。

        Args:
            key (str): Sorted Setのキー

        Returns:
            int: 要素数（Redis未接続時は0）
        """
        if not self._redis:
            return 0

        full_key = self._make_key(key)
        try:
            return await self._redis.zcard(full_key)
        except Exception as e:
            logger.exception(
                "Sorted Setカウントエラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return 0

    async def zadd(self, key: str, mapping: dict[str | bytes, float]) -> int:
        """Sorted Setに要素を追加します（レート制限用）。

        Args:
            key (str): Sorted Setのキー
            mapping (dict[str, float]): {要素: スコア} の辞書

        Returns:
            int: 追加された要素数（Redis未接続時は0）
        """
        if not self._redis:
            return 0

        full_key = self._make_key(key)
        try:
            return await self._redis.zadd(full_key, mapping)
        except Exception as e:
            logger.exception(
                "Sorted Set追加エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return 0

    async def expire_key(self, key: str, seconds: int) -> bool:
        """キーにTTLを設定します（レート制限用）。

        Args:
            key (str): キー
            seconds (int): TTL（秒）

        Returns:
            bool: 成功時True、失敗時False
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        try:
            return await self._redis.expire(full_key, seconds)
        except Exception as e:
            logger.exception(
                "TTL設定エラー",
                cache_key=full_key,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False


# グローバルキャッシュマネージャーインスタンス
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """グローバルキャッシュマネージャーインスタンスを取得します。

    この関数は、FastAPIの依存性注入（Dependency Injection）で使用するための
    ヘルパー関数です。グローバルに定義された cache_manager インスタンスを返します。

    Returns:
        CacheManager: グローバルキャッシュマネージャーインスタンス
            - 接続済み（connect()呼び出し後）のインスタンス
            - アプリケーション全体で共有されるシングルトン

    Example:
        >>> # FastAPI依存性注入での使用
        >>> from fastapi import Depends
        >>> from app.core.cache import get_cache_manager, CacheManager
        >>>
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(
        ...     user_id: int,
        ...     cache: CacheManager = Depends(get_cache_manager)
        ... ):
        ...     # キャッシュから取得
        ...     cached_user = await cache.get(f"user:{user_id}")
        ...     if cached_user:
        ...         return cached_user
        ...
        ...     # データベースから取得
        ...     user = await db.get_user(user_id)
        ...     await cache.set(f"user:{user_id}", user, expire=3600)
        ...     return user
        >>>
        >>> # 直接使用（非推奨、依存性注入を推奨）
        >>> cache = await get_cache_manager()
        >>> await cache.set("key", "value")

    Note:
        - FastAPI の Depends() での使用を推奨します
        - 直接 cache_manager をインポートして使用することも可能です
        - この関数は非同期ですが、実際には同期的に動作します（互換性のため）
        - アプリケーション起動時に cache_manager.connect() を呼び出してください
    """
    return cache_manager
