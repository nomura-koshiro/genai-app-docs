"""信頼性向上デコレータ。

リトライ処理など、システムの信頼性を向上させる
横断的関心事を扱うデコレータを提供します。
"""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """エラー時に自動リトライするデコレータ。

    外部API呼び出し、ネットワークエラー、一時的なデータベース接続エラーなど、
    リトライで回復可能なエラーに対して自動的に再試行を行います。

    リトライ戦略:
        - Exponential Backoff: リトライごとに待機時間が指数的に増加
        - デフォルト: 1秒 → 2秒 → 4秒 → 8秒...

    リトライ対象外の例外:
        - ValidationError: バリデーションエラーは再試行不要
        - AuthenticationError: 認証エラーは再試行不要
        - NotFoundError: リソース不在は再試行不要

    Args:
        max_retries (int): 最大リトライ回数
            - デフォルト: 3回
            - 0: リトライなし(デコレータ無効)
        delay (float): 初回リトライまでの待機時間(秒)
            - デフォルト: 1.0秒
        backoff (float): リトライごとの待機時間の倍率
            - デフォルト: 2.0(2倍ずつ増加)
            - 1.0: 固定間隔
        exceptions (tuple): リトライ対象の例外タプル
            - デフォルト: (Exception,) すべての例外
            - 推奨: (ConnectionError, TimeoutError) など具体的な例外

    Returns:
        Callable: リトライ機能が適用されたデコレータ

    Example:
        >>> @retry_on_error(
        ...     max_retries=3,
        ...     delay=1.0,
        ...     backoff=2.0,
        ...     exceptions=(ConnectionError, TimeoutError)
        ... )
        >>> async def call_external_api(url: str):
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get(url, timeout=5.0)
        ...         return response.json()

    Note:
        - すべてのリトライが失敗すると最後の例外が再送出される
        - リトライごとにWARNINGログが記録される
        - 最終失敗時にERRORログが記録される
        - asyncio.sleep() による非ブロッキング待機

    Warning:
        - 冪等性のない操作(決済処理など)には使用しない
        - リトライ回数が多いと全体のレスポンス時間が大幅に増加
        - バリデーションエラーなどリトライ不要な例外は対象外にする
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: BaseException | None = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            next_delay=current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "all_retries_failed",
                            function=func.__name__,
                            max_retries=max_retries,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            exc_info=True,
                        )

            # 全てのリトライが失敗した場合、必ず例外が保存されている
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator
