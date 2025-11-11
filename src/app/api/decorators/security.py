"""セキュリティ関連デコレータ。

権限検証、エラーハンドリングなど、セキュリティに関する
横断的関心事を扱うデコレータを提供します。
"""

import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, cast

from fastapi import HTTPException

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def validate_permissions(
    resource_type: str,
    action: str,
    get_resource_id: Callable[[dict[str, Any]], str | int] | None = None,
):
    """リソースベースの権限検証デコレータ。

    ユーザーが特定のリソース（ファイル、セッション等）に対して
    指定されたアクション（読取、削除等）を実行する権限を持っているかを検証します。

    権限検証ルール:
        1. current_user が存在する（認証済み）
        2. リソースの所有者である（owner_id == user.id）
        3. または、スーパーユーザーである（is_superuser == True）

    Args:
        resource_type (str): リソースタイプ
            - 例: "file", "session", "user"
        action (str): アクション
            - 例: "read", "delete", "update"
        get_resource_id (Callable | None): リソースIDを取得する関数
            - 引数: kwargs（関数のキーワード引数辞書）
            - 戻り値: リソースID
            - None の場合、{resource_type}_id をキーワード引数から取得

    Returns:
        Callable: 権限検証が適用されたデコレータ

    Example:
        >>> # ファイル削除の権限検証
        >>> @validate_permissions("file", "delete")
        >>> async def delete_file(
        ...     file_id: str,
        ...     file_service: FileServiceDep,
        ...     current_user: User,
        ... ):
        ...     # ここに到達する時点で権限検証済み
        ...     await file_service.delete_file(file_id)
        >>>
        >>> # カスタムリソースID取得
        >>> @validate_permissions(
        ...     "session",
        ...     "read",
        ...     get_resource_id=lambda kwargs: kwargs["session_id"]
        ... )
        >>> async def get_session(session_id: str, current_user: User):
        ...     # セッション所有権を検証済み
        ...     return await session_service.get(session_id)

    Raises:
        AuthenticationError: current_user が存在しない場合
        AuthorizationError: 権限がない場合（所有者でもスーパーユーザーでもない）
        NotFoundError: リソースが存在しない場合

    Note:
        - current_user は関数の引数に含まれている必要がある
        - リソースは user_id または owner_id 属性を持つ必要がある
        - スーパーユーザーは常にアクセス可能
        - ログは structlog 形式で出力される

    Warning:
        - リソースタイプに対応するサービスが必要（例: file_service）
        - サービスは get_{resource_type}() メソッドを実装している必要がある
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # current_user を取得
            current_user = kwargs.get("current_user")
            if not current_user:
                # 引数から探す
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                for i, arg in enumerate(args):
                    if i < len(param_names) and param_names[i] == "current_user":
                        current_user = arg
                        break

            if not current_user:
                raise AuthenticationError(
                    "認証が必要です",
                    details={"resource_type": resource_type, "action": action},
                )

            # リソースIDを取得
            resource_id: str | int
            if get_resource_id:
                resource_id = get_resource_id(kwargs)
            else:
                # デフォルト: {resource_type}_id
                resource_id_key = f"{resource_type}_id"
                resource_id_value = kwargs.get(resource_id_key)
                if not resource_id_value:
                    raise ValidationError(
                        f"リソースID（{resource_id_key}）が指定されていません",
                        details={"resource_type": resource_type},
                    )
                resource_id = cast(str | int, resource_id_value)

            # リソースサービスを取得
            service_key = f"{resource_type}_service"
            service = kwargs.get(service_key)
            if not service:
                raise ValidationError(
                    f"サービス（{service_key}）が見つかりません",
                    details={"resource_type": resource_type},
                )

            # リソースを取得
            get_method_name = f"get_{resource_type}"
            if not hasattr(service, get_method_name):
                raise ValidationError(
                    f"サービスに {get_method_name}() メソッドが存在しません",
                    details={"resource_type": resource_type, "service": service_key},
                )

            get_method = getattr(service, get_method_name)
            resource = await get_method(resource_id)

            if not resource:
                raise NotFoundError(
                    f"{resource_type} が見つかりません: {resource_id}",
                    details={"resource_type": resource_type, "resource_id": resource_id},
                )

            # 権限検証: 所有者またはスーパーユーザー
            resource_owner_id = getattr(resource, "user_id", None) or getattr(resource, "owner_id", None)

            if not resource_owner_id:
                logger.warning(
                    "resource_missing_owner_attributes",
                    resource_type=resource_type,
                    resource_id=resource_id,
                )

            is_owner = resource_owner_id == current_user.id
            is_superuser = getattr(current_user, "is_superuser", False)

            if not (is_owner or is_superuser):
                raise AuthorizationError(
                    f"{resource_type} へのアクセス権限がありません",
                    details={
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "action": action,
                        "user_id": current_user.id,
                    },
                )

            logger.info(
                "permission_validated",
                user_id=current_user.id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                is_owner=is_owner,
                is_superuser=is_superuser,
            )

            # 権限検証成功、元の関数を実行
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def handle_service_errors[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """サービス層のエラーを統一的にHTTPExceptionに変換するデコレータ。

    このデコレータは、サービス層から発生するカスタム例外を
    適切なHTTPステータスコードとメッセージを持つHTTPExceptionに
    自動的に変換します。

    変換ルール:
        - ValidationError → 400 Bad Request
        - AuthenticationError → 401 Unauthorized
        - AuthorizationError → 403 Forbidden
        - NotFoundError → 404 Not Found
        - その他のException → 500 Internal Server Error

    Args:
        func: デコレート対象の非同期関数

    Returns:
        Callable: エラーハンドリングが適用された関数

    Example:
        >>> @router.post("/users", response_model=UserResponse)
        >>> @handle_service_errors
        >>> async def create_user(
        ...     user_data: UserCreate,
        ...     service: UserServiceDep,
        ... ) -> UserResponse:
        ...     user = await service.create_user(user_data)
        ...     return UserResponse.model_validate(user)

    Note:
        - このデコレータは非同期関数専用です
        - ログレベルは例外の種類に応じて自動調整されます
        - 本番環境では内部エラーの詳細を隠蔽します
        - ログは structlog 形式で出力される
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
            raise HTTPException(
                status_code=422,
                detail={
                    "error": e.message,
                    "details": e.details,
                },
            ) from e
        except AuthenticationError as e:
            logger.warning(
                "authentication_error",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise HTTPException(
                status_code=401,
                detail={
                    "error": e.message,
                    "details": e.details,
                },
            ) from e
        except AuthorizationError as e:
            logger.warning(
                "authorization_error",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": e.message,
                    "details": e.details,
                },
            ) from e
        except NotFoundError as e:
            logger.info(
                "resource_not_found",
                function=func.__name__,
                error_message=e.message,
                details=e.details,
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": e.message,
                    "details": e.details,
                },
            ) from e
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
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "details": None,  # セキュリティのため詳細は隠蔽
                },
            ) from e

    return wrapper
