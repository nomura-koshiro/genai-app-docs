"""エラーハンドリングデコレータ。

サービス層から発生する例外のログ記録と再送出を行うデコレータを提供します。

Note:
    権限検証（認可）は app.api.core.dependencies.authorization で
    FastAPI Dependency方式で提供されています。
"""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def handle_service_errors[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """サービス層のエラーをログに記録して再送出するデコレータ。

    このデコレータは、サービス層から発生するカスタム例外をログに記録してから
    そのまま再送出します。実際のHTTPレスポンス変換は、app.api.core.exception_handlers
    のRFC 9457準拠ハンドラーで統一的に処理されます。

    ログ記録の役割:
        - ValidationError: WARNING レベルでログ記録
        - AuthenticationError: WARNING レベルでログ記録
        - AuthorizationError: WARNING レベルでログ記録
        - NotFoundError: INFO レベルでログ記録
        - その他のException: ERROR レベルでログ記録

    Args:
        func: デコレート対象の非同期関数

    Returns:
        Callable: エラーハンドリングが適用された関数

    Example:
        >>> @router.post("/users", response_model=UserAccountResponse)
        >>> @handle_service_errors
        >>> async def create_user(
        ...     user_data: UserCreate,
        ...     service: UserServiceDep,
        ... ) -> UserAccountResponse:
        ...     user = await service.create_user(user_data)
        ...     return UserAccountResponse.model_validate(user)

    Note:
        - このデコレータは非同期関数専用です
        - AppExceptionサブクラスはそのまま再送出され、
          app.api.core.exception_handlers.app_exception_handler で
          RFC 9457形式に変換されます
        - HTTPExceptionもそのまま再送出されます
        - ログは structlog 形式で出力されます

    Reference:
        RFC 9457: https://www.rfc-editor.org/rfc/rfc9457.html
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(
                "validation_error",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise  # RFC 9457ハンドラーで処理
        except AuthenticationError as e:
            logger.warning(
                "authentication_error",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise  # RFC 9457ハンドラーで処理
        except AuthorizationError as e:
            logger.warning(
                "authorization_error",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise  # RFC 9457ハンドラーで処理
        except NotFoundError as e:
            logger.info(
                "resource_not_found",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise  # RFC 9457ハンドラーで処理
        except HTTPException:
            # FastAPIのHTTPExceptionはそのまま再送出
            raise
        except Exception as e:
            logger.error(
                "unexpected_error",
                function=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise  # global_exception_handlerで処理

    return wrapper
