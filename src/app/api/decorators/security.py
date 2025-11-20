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


# ========================================================================
# Helper functions for validate_permissions
# ========================================================================


def _get_current_user_from_args(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """関数の引数から current_user を取得します。

    Args:
        func: 対象の関数
        args: 位置引数
        kwargs: キーワード引数

    Returns:
        current_user オブジェクト

    Raises:
        AuthenticationError: current_user が見つからない場合
    """
    # まずキーワード引数から探す
    current_user = kwargs.get("current_user")
    if current_user:
        return current_user

    # 位置引数から探す
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    for i, arg in enumerate(args):
        if i < len(param_names) and param_names[i] == "current_user":
            return arg

    # 見つからない場合はエラー
    raise AuthenticationError("認証が必要です", details={"hint": "current_user argument is required"})


def _get_resource_id_from_kwargs(
    resource_type: str,
    kwargs: dict[str, Any],
    get_resource_id: Callable[[dict[str, Any]], str | int] | None,
) -> str | int:
    """関数の引数からリソースIDを取得します。

    Args:
        resource_type: リソースタイプ（例: "file", "session"）
        kwargs: キーワード引数
        get_resource_id: カスタムリソースID取得関数（オプション）

    Returns:
        リソースID

    Raises:
        ValidationError: リソースIDが見つからない場合
    """
    if get_resource_id:
        return get_resource_id(kwargs)

    # デフォルト: {resource_type}_id
    resource_id_key = f"{resource_type}_id"
    resource_id_value = kwargs.get(resource_id_key)
    if not resource_id_value:
        raise ValidationError(
            f"リソースID（{resource_id_key}）が指定されていません",
            details={"resource_type": resource_type},
        )
    return cast(str | int, resource_id_value)


async def _get_resource_from_service(
    resource_type: str,
    resource_id: str | int,
    kwargs: dict[str, Any],
) -> Any:
    """サービスからリソースを取得します。

    Args:
        resource_type: リソースタイプ（例: "file", "session"）
        resource_id: リソースID
        kwargs: キーワード引数（サービスを含む）

    Returns:
        リソースオブジェクト

    Raises:
        ValidationError: サービスまたはメソッドが見つからない場合
        NotFoundError: リソースが存在しない場合
    """
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

    return resource


def _check_user_permission(
    resource_type: str,
    resource_id: str | int,
    resource: Any,
    current_user: Any,
    action: str,
) -> None:
    """ユーザーがリソースにアクセスする権限を持っているか検証します。

    Args:
        resource_type: リソースタイプ
        resource_id: リソースID
        resource: リソースオブジェクト
        current_user: 現在のユーザー
        action: アクション（例: "read", "delete"）

    Raises:
        AuthorizationError: 権限がない場合
    """
    # user_id=0 の場合も正しく処理するため、is not None チェックを使用
    resource_owner_id = getattr(resource, "user_id", None)
    if resource_owner_id is None:
        resource_owner_id = getattr(resource, "owner_id", None)

    if resource_owner_id is None:
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


# ========================================================================
# Main decorator
# ========================================================================


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
            # 1. current_user を取得
            current_user = _get_current_user_from_args(func, args, kwargs)

            # 2. リソースIDを取得
            resource_id = _get_resource_id_from_kwargs(resource_type, kwargs, get_resource_id)

            # 3. リソースを取得
            resource = await _get_resource_from_service(resource_type, resource_id, kwargs)

            # 4. 権限検証
            _check_user_permission(resource_type, resource_id, resource, current_user, action)

            # 権限検証成功、元の関数を実行
            return await func(*args, **kwargs)

        return wrapper

    return decorator


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
