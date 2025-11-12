"""基本機能デコレータ。

ログ記録、パフォーマンス測定、タイムアウト制御など、
基本的な横断的関心事を扱うデコレータを提供します。
"""

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def log_execution(
    level: str = "info",
    include_args: bool = False,
    include_result: bool = False,
):
    """関数の実行をログに記録するデコレータ。

    関数の開始と終了を自動的にログに記録し、デバッグやトレーシングを簡素化します。
    オプションで引数や戻り値もログに含めることができます。

    ログ記録内容:
        - 関数名とモジュール名
        - 実行開始/終了のタイムスタンプ（自動）
        - 引数情報（オプション）
        - 戻り値情報（オプション）

    Args:
        level (str): ログレベル
            - "debug": デバッグ情報（開発環境）
            - "info": 通常情報（本番環境推奨）
            - "warning": 警告
            - "error": エラー
        include_args (bool): 引数をログに含めるか
            - デフォルト: False（self引数は自動除外）
            - True: 引数の文字列表現をログに記録
        include_result (bool): 戻り値をログに含めるか
            - デフォルト: False
            - True: 戻り値の文字列表現をログに記録

    Returns:
        Callable: ログ記録機能が適用されたデコレータ

    Example:
        >>> @log_execution(level="info", include_args=True)
        >>> async def process_payment(user_id: int, amount: float):
        ...     # 決済処理
        ...     return {"status": "success", "transaction_id": "12345"}
        >>>
        >>> # ログ出力:
        >>> # INFO: Executing: process_payment
        >>> #       extra={'function': 'process_payment', 'args': '(123, 100.0)', ...}
        >>> # INFO: Completed: process_payment

    Note:
        - 構造化ログ（extra）にメタデータを記録
        - self引数は自動的にログから除外
        - 大量のデータを含む引数/戻り値はパフォーマンスに影響
        - 本番環境では include_args=False を推奨（機密情報保護）

    Warning:
        - パスワードやトークンを含む引数には使用しない（include_args=True時）
        - 大きなオブジェクトの文字列化はパフォーマンス低下の原因
        - 本番環境でのdebugレベルログは最小限に
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_func = getattr(logger, level)

            extra_data: dict[str, Any] = {
                "function": func.__name__,
                "module": func.__module__,
            }

            if include_args:
                # メソッドの場合のみself引数を除外
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                is_method = len(params) > 0 and params[0] in ("self", "cls")

                if is_method and len(args) > 0:
                    extra_data["args"] = str(args[1:])  # self/cls を除外
                else:
                    extra_data["args"] = str(args)  # 通常の関数はそのまま
                extra_data["kwargs"] = str(kwargs)

            log_func(f"Executing: {func.__name__}", extra=extra_data)

            result = await func(*args, **kwargs)

            if include_result:
                extra_data["result"] = str(result)

            log_func(f"Completed: {func.__name__}", extra=extra_data)

            return result

        return wrapper

    return decorator


def measure_performance[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """非同期関数の実行時間を測定するデコレータ。

    パフォーマンスボトルネックの特定やレスポンス時間の監視に使用します。
    実行時間は構造化ログに記録され、メトリクス収集システムと統合できます。

    実行時間のログ記録内容:
        - 関数名とモジュール名
        - 実行時間（秒、小数点以下4桁）
        - 関数の引数情報（オプション）

    Args:
        func: デコレート対象の非同期関数

    Returns:
        Callable: パフォーマンス測定が適用された関数

    Example:
        >>> @measure_performance
        >>> async def fetch_user_data(user_id: int):
        ...     user = await db.get_user(user_id)
        ...     return user
        >>>
        >>> # ログ出力（structlog形式）:
        >>> # {"event": "performance_measurement", "function": "fetch_user_data",
        >>> #  "duration_seconds": 0.0234, "module": "...", "performance_metric": true}

    Note:
        - time.perf_counter() を使用して高精度な時間測定を実行
        - エラー発生時も実行時間をログに記録（finallyブロック）
        - 他のデコレータと組み合わせて使用可能
        - ログレベル: INFO（パフォーマンス監視用）
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(
                "performance_measurement",
                function=func.__name__,
                duration_seconds=elapsed,
                module=func.__module__,
                performance_metric=True,
            )

    return wrapper


def async_timeout(seconds: float):
    """非同期関数にタイムアウトを設定するデコレータ。

    長時間実行される処理（AIエージェント、外部API、ファイルアップロード等）に
    タイムアウトを設定し、ハングアップを防ぎます。

    タイムアウト時の動作:
        - asyncio.TimeoutError が発生
        - ValidationError に変換されてユーザーに通知
        - ワーカープロセスは解放される

    Args:
        seconds (float): タイムアウト時間（秒）
            - 例: 5.0 = 5秒, 300.0 = 5分

    Returns:
        Callable: タイムアウト機能が適用されたデコレータ

    Example:
        >>> # AIエージェント実行に5分のタイムアウト
        >>> @async_timeout(300.0)
        >>> async def execute_agent(self, prompt: str):
        ...     return await self.agent.ainvoke(prompt)
        >>>
        >>> # ファイルアップロードに30秒のタイムアウト
        >>> @async_timeout(30.0)
        >>> async def upload_to_blob(self, file_data: bytes):
        ...     return await self.storage.upload(file_data)

    Raises:
        ValidationError: タイムアウト時（ユーザー向けエラーメッセージ）

    Note:
        - asyncio.wait_for() を使用
        - タイムアウト時はリソースが適切に解放される
        - ログにタイムアウト情報を記録（structlog形式）

    Warning:
        - タイムアウト値は処理内容に応じて適切に設定
        - 短すぎると正常な処理が中断される
        - 長すぎるとハングアップ防止効果が薄い

    推奨タイムアウト値:
        - AIエージェント実行: 300秒（5分）
        - ファイルアップロード: 30秒
        - 外部API呼び出し: 10秒
        - データベースクエリ: 5秒
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except TimeoutError:
                logger.error(
                    "async_timeout_exceeded",
                    function=func.__name__,
                    timeout_seconds=seconds,
                    module=func.__module__,
                )
                raise ValidationError(
                    f"処理がタイムアウトしました（{seconds}秒）。後でもう一度お試しください。",
                    details={"timeout_seconds": seconds, "function": func.__name__},
                ) from None

        return wrapper

    return decorator
