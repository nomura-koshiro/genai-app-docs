"""Azure AD認証用ユーザー管理APIエンドポイント。

このモジュールは、Azure AD認証に対応したユーザー管理のRESTful APIエンドポイントを定義します。
パスワード認証は含まず、Azure AD Object IDをキーとしたユーザー管理に特化しています。

主な機能:
    - ユーザー一覧取得（GET /api/v1/user_accounts - 管理者のみ、ページネーション対応）
    - 現在のユーザー情報取得（GET /api/v1/user_accounts/me - 認証必須）
    - 特定ユーザー取得（GET /api/v1/user_accounts/{user_id} - 管理者のみ）
    - ユーザー情報更新（PATCH /api/v1/user_accounts/me）
    - ユーザー削除（DELETE /api/v1/user_accounts/{user_id} - 管理者のみ）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - ロールベースアクセス制御（RBAC）

使用例:
    >>> # 現在のユーザー情報取得
    >>> GET /api/v1/user_accounts/me
    >>> Authorization: Bearer <Azure_AD_Token>
    >>> {
    ...     "id": "12345678-1234-1234-1234-123456789abc",
    ...     "azure_oid": "azure-oid-12345",
    ...     "email": "user@company.com",
    ...     "display_name": "John Doe",
    ...     "roles": ["User"],
    ...     "is_active": true,
    ...     "created_at": "2024-01-01T00:00:00Z",
    ...     "updated_at": "2024-01-01T00:00:00Z",
    ...     "last_login": "2024-01-15T10:30:00Z"
    ... }
"""

import uuid

from fastapi import APIRouter, Query, Request, status

from app.api.core import CurrentUserAccountDep, UserServiceDep
from app.api.decorators import handle_service_errors
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.schemas import UserAccountListResponse, UserAccountResponse, UserAccountUpdate

logger = get_logger(__name__)

user_accounts_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@user_accounts_router.get(
    "/user_account",
    response_model=UserAccountListResponse,
    summary="ユーザー一覧取得",
    description="""
    ユーザー一覧を取得します（管理者専用）。

    **認証が必要です。**

    クエリパラメータ:
        - skip: int - スキップ数（デフォルト: 0）
        - limit: int - 取得件数（デフォルト: 100）

    レスポンス:
        - UserAccountListResponse: ユーザー一覧レスポンス
            - users: list[UserAccountResponse] - ユーザーリスト
            - total: int - 総件数
            - skip: int - スキップ数
            - limit: int - 取得件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def list_users(
    user_service: UserServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
) -> UserAccountListResponse:
    """ユーザー一覧を取得します（管理者専用）。"""
    # ロールチェック: SystemAdminが必要
    if "SystemAdmin" not in current_user.roles:
        logger.warning(
            "管理者権限がないユーザーがユーザー一覧取得を試行",
            user_id=str(current_user.id),
            email=current_user.email,
            roles=current_user.roles,
        )
        raise ValidationError(
            "管理者権限が必要です",
            details={"required_role": "SystemAdmin", "user_roles": current_user.roles},
        )

    logger.info(
        "ユーザー一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        action="list_users",
    )

    # ユーザー一覧を取得
    users = await user_service.list_users(skip=skip, limit=limit)

    # 総件数を正確に取得
    total = await user_service.count_users()

    logger.info(
        "ユーザー一覧を取得しました",
        admin_user_id=str(current_user.id),
        count=len(users),
        total=total,
        skip=skip,
        limit=limit,
    )

    return UserAccountListResponse(
        users=[UserAccountResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@user_accounts_router.get(
    "/user_account/me",
    response_model=UserAccountResponse,
    summary="現在のユーザー情報取得",
    description="""
    現在の認証済みユーザーの情報を取得します。

    **認証が必要です。**

    レスポンス:
        - UserAccountResponse: ユーザー情報
            - id: uuid - ユーザーID
            - azure_oid: str - Azure AD Object ID
            - email: str - メールアドレス
            - display_name: str - 表示名
            - roles: list[str] - システムロール
            - is_active: bool - アクティブフラグ
            - created_at: datetime - 作成日時
            - updated_at: datetime - 更新日時
            - last_login: datetime - 最終ログイン日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def get_current_user(
    request: Request,
    current_user: CurrentUserAccountDep,
    user_service: UserServiceDep,
) -> UserAccountResponse:
    """現在の認証済みユーザーの情報を取得します。"""
    # クライアントIPアドレスを取得
    client_ip = request.client.host if request.client else None

    logger.info(
        "現在のユーザー情報取得",
        user_id=str(current_user.id),
        email=current_user.email,
        client_ip=client_ip,
        action="get_current_user",
    )

    # 最終ログイン情報を更新
    updated_user = await user_service.update_last_login(
        user_id=current_user.id,
        client_ip=client_ip,
    )

    return UserAccountResponse.model_validate(updated_user)


@user_accounts_router.get(
    "/user_account/{user_id}",
    response_model=UserAccountResponse,
    summary="特定ユーザー情報取得",
    description="""
    特定のユーザー情報を取得します（管理者専用）。

    **認証が必要です。**

    パスパラメータ:
        - user_id: uuid - ユーザーID（必須）

    レスポンス:
        - UserAccountResponse: ユーザー情報
            - id: uuid - ユーザーID
            - azure_oid: str - Azure AD Object ID
            - email: str - メールアドレス
            - display_name: str - 表示名
            - roles: list[str] - システムロール
            - is_active: bool - アクティブフラグ
            - created_at: datetime - 作成日時
            - updated_at: datetime - 更新日時
            - last_login: datetime - 最終ログイン日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def get_user(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
    current_user: CurrentUserAccountDep,
) -> UserAccountResponse:
    """特定のユーザー情報を取得します（管理者専用）。"""
    # ロールチェック: SystemAdminが必要
    if "SystemAdmin" not in current_user.roles:
        logger.warning(
            "管理者権限がないユーザーが特定ユーザー取得を試行",
            admin_user_id=str(current_user.id),
            target_user_id=str(user_id),
            roles=current_user.roles,
        )
        raise ValidationError(
            "管理者権限が必要です",
            details={"required_role": "SystemAdmin", "user_roles": current_user.roles},
        )

    logger.info(
        "特定ユーザー情報取得",
        admin_user_id=str(current_user.id),
        target_user_id=str(user_id),
        action="get_user",
    )

    user = await user_service.get_user(user_id)
    if not user:
        logger.warning(
            "ユーザーが見つかりません",
            admin_user_id=str(current_user.id),
            target_user_id=str(user_id),
        )
        raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

    logger.info(
        "特定ユーザー情報を取得しました",
        admin_user_id=str(current_user.id),
        target_user_id=str(user.id),
        email=user.email,
    )

    return UserAccountResponse.model_validate(user)


# ================================================================================
# PATCH Endpoints
# ================================================================================


@user_accounts_router.patch(
    "/user_account/me",
    response_model=UserAccountResponse,
    summary="ユーザー情報更新",
    description="""
    現在のユーザー情報を更新します。

    **認証が必要です。**

    リクエストボディ:
        - UserAccountUpdate: ユーザー更新データ
            - display_name: str - 表示名（オプション）
            - roles: list[str] - システムレベルのロール（オプション、管理者のみ）
            - is_active: bool - アクティブフラグ（オプション、管理者のみ）

    レスポンス:
        - UserAccountResponse: ユーザー情報
            - id: uuid - ユーザーID
            - azure_oid: str - Azure AD Object ID
            - email: str - メールアドレス
            - display_name: str - 表示名
            - roles: list[str] - システムロール
            - is_active: bool - アクティブフラグ
            - created_at: datetime - 作成日時
            - updated_at: datetime - 更新日時
            - last_login: datetime - 最終ログイン日時

    ステータスコード:
        - 200: 更新成功
        - 401: 認証されていない
        - 404: リソースが見つからない
    """,
)
@handle_service_errors
async def update_current_user(
    update_data: UserAccountUpdate,
    current_user: CurrentUserAccountDep,
    user_service: UserServiceDep,
) -> UserAccountResponse:
    """現在のユーザー情報を更新します。"""
    logger.info(
        "ユーザー情報更新",
        user_id=str(current_user.id),
        email=current_user.email,
        update_fields=update_data.model_dump(exclude_unset=True),
        action="update_current_user",
    )

    # 更新データを取得
    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        logger.info("更新フィールドが指定されていません", user_id=str(current_user.id))
        return UserAccountResponse.model_validate(current_user)

    # サービス層を使用してユーザー情報を更新
    # サービス層で権限チェック、バリデーション、ビジネスロジックを実行
    updated_user = await user_service.update_user(
        user_id=current_user.id,
        update_data=update_dict,
        current_user_roles=current_user.roles,
    )

    return UserAccountResponse.model_validate(updated_user)


# ================================================================================
# DELETE Endpoints
# ================================================================================


@user_accounts_router.delete(
    "/user_account/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ユーザー削除",
    description="""
    ユーザーを削除します（管理者専用）。

    **認証が必要です。**

    パスパラメータ:
        - user_id: uuid - ユーザーID（必須）

    レスポンス:
        - None（204 No Content）

    ステータスコード:
        - 204: 削除成功
        - 401: 認証されていない
        - 404: リソースが見つからない
    """,
)
@handle_service_errors
async def delete_user(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """ユーザーを削除します（管理者専用）。"""
    # ロールチェック: SystemAdminが必要
    if "SystemAdmin" not in current_user.roles:
        logger.warning(
            "管理者権限がないユーザーがユーザー削除を試行",
            admin_user_id=str(current_user.id),
            target_user_id=str(user_id),
            roles=current_user.roles,
        )
        raise ValidationError(
            "管理者権限が必要です",
            details={"required_role": "SystemAdmin", "user_roles": current_user.roles},
        )

    # 自己削除チェック
    if current_user.id == user_id:
        logger.warning(
            "ユーザーが自分自身を削除しようとしました",
            user_id=str(current_user.id),
            email=current_user.email,
        )
        raise ValidationError(
            "自分自身を削除することはできません",
            details={"user_id": str(user_id)},
        )

    logger.info(
        "ユーザー削除",
        admin_user_id=str(current_user.id),
        target_user_id=str(user_id),
        action="delete_user",
    )

    # ユーザーを削除（サービス経由）
    await user_service.delete_user(user_id)

    logger.info(
        "ユーザーを削除しました",
        admin_user_id=str(current_user.id),
        deleted_user_id=str(user_id),
    )
