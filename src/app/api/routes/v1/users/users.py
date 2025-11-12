"""Azure AD認証用ユーザー管理APIエンドポイント。

このモジュールは、Azure AD認証に対応したユーザー管理のRESTful APIエンドポイントを定義します。
パスワード認証は含まず、Azure AD Object IDをキーとしたユーザー管理に特化しています。

主な機能:
    - ユーザー一覧取得（GET /api/v1/users - 管理者のみ、ページネーション対応）
    - 現在のユーザー情報取得（GET /api/v1/users/me - 認証必須）
    - 特定ユーザー取得（GET /api/v1/users/{user_id} - 管理者のみ）
    - ユーザー情報更新（PATCH /api/v1/users/me）
    - ユーザー削除（DELETE /api/v1/users/{user_id} - 管理者のみ）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - ロールベースアクセス制御（RBAC）

使用例:
    >>> # 現在のユーザー情報取得
    >>> GET /api/v1/users/me
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

from app.api.core import AzureUserServiceDep, CurrentUserAzureDep
from app.api.decorators import handle_service_errors
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.schemas import UserListResponse, UserResponse, UserUpdate

logger = get_logger(__name__)

router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@router.get(
    "",
    response_model=UserListResponse,
    summary="ユーザー一覧取得",
    description="""
    登録されているすべてのユーザーの一覧を取得します。

    **管理者権限が必要です（SystemAdminロール）。**

    - **skip**: スキップするレコード数（デフォルト: 0）
    - **limit**: 取得する最大レコード数（デフォルト: 100、最大: 1000）

    ページネーション情報:
        - users: ユーザーリスト
        - total: 総件数
        - skip: スキップ数
        - limit: 取得件数
    """,
)
@handle_service_errors
async def list_users(
    user_service: AzureUserServiceDep,
    current_user: CurrentUserAzureDep,
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
) -> UserListResponse:
    """ユーザー一覧を取得します（管理者専用）。

    Args:
        user_service (UserService): ユーザーサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）
        skip (int): スキップするレコード数（ページネーション用）
            - デフォルト: 0
            - 範囲: 0以上
        limit (int): 取得する最大レコード数（ページサイズ）
            - デフォルト: 100
            - 範囲: 1-1000

    Returns:
        UserListResponse: ユーザー一覧とページネーション情報
            - users: ユーザーリスト
            - total: 総件数
            - skip: スキップ数
            - limit: 取得件数

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 管理者権限がない（SystemAdminロール必須）
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/users?skip=0&limit=10
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "users": [
        ...         {
        ...             "id": "12345678-1234-1234-1234-123456789abc",
        ...             "azure_oid": "azure-oid-12345",
        ...             "email": "user1@company.com",
        ...             "display_name": "User One",
        ...             "roles": ["User"],
        ...             "is_active": true,
        ...             "created_at": "2024-01-01T00:00:00Z",
        ...             "updated_at": "2024-01-01T00:00:00Z",
        ...             "last_login": "2024-01-15T10:30:00Z"
        ...         },
        ...         {
        ...             "id": "87654321-4321-4321-4321-cba987654321",
        ...             "azure_oid": "azure-oid-67890",
        ...             "email": "user2@company.com",
        ...             "display_name": "User Two",
        ...             "roles": ["SystemAdmin", "User"],
        ...             "is_active": true,
        ...             "created_at": "2024-01-02T00:00:00Z",
        ...             "updated_at": "2024-01-02T00:00:00Z",
        ...             "last_login": "2024-01-16T08:00:00Z"
        ...         }
        ...     ],
        ...     "total": 2,
        ...     "skip": 0,
        ...     "limit": 10
        ... }

    Note:
        - SystemAdminロールを持つユーザーのみアクセス可能です
        - ページネーションを使用して効率的にデータを取得できます
        - total フィールドにより全体の件数が把握できます
    """
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

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="現在のユーザー情報取得",
    description="""
    Azure AD認証されたユーザー自身の情報を取得します。

    このエンドポイントはAzure AD認証が必須です。
    `Authorization: Bearer <Azure_AD_Token>` ヘッダーが必要です。

    開発環境では、モックトークンを使用できます:
    `Authorization: Bearer mock-access-token-dev-12345`
    """,
)
@handle_service_errors
async def get_current_user(
    request: Request,
    current_user: CurrentUserAzureDep,
    user_service: AzureUserServiceDep,
) -> UserResponse:
    """現在の認証済みユーザーの情報を取得します。

    このエンドポイントは、Azure AD認証されたユーザー自身の情報を返します。
    同時に、最終ログイン情報を更新します。

    Args:
        request (Request): FastAPIリクエストオブジェクト（クライアントIP取得用）
        current_user (User): 認証済みユーザー（自動注入）
        user_service (UserService): ユーザーサービス（自動注入）

    Returns:
        UserResponse: 現在のユーザー情報
            - id: ユーザーID（UUID）
            - azure_oid: Azure AD Object ID
            - email: メールアドレス
            - display_name: 表示名
            - roles: システムレベルのロール
            - is_active: アクティブフラグ
            - created_at: 作成日時
            - updated_at: 更新日時
            - last_login: 最終ログイン日時（更新後）

    Example:
        >>> # リクエスト
        >>> GET /api/v1/users/me
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
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

    Note:
        - このエンドポイントを呼び出すたびに last_login が更新されます
        - クライアントIPアドレスは監査ログに記録されます（機密情報は含まない）
        - 開発環境では、モックトークンを使用できます
    """
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

    return UserResponse.model_validate(updated_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="特定ユーザー情報取得",
    description="""
    指定されたIDのユーザー情報を取得します。

    **管理者権限が必要です（SystemAdminロール）。**

    パスパラメータ:
        - user_id: ユーザーID（UUID形式）
    """,
)
@handle_service_errors
async def get_user(
    user_id: uuid.UUID,
    user_service: AzureUserServiceDep,
    current_user: CurrentUserAzureDep,
) -> UserResponse:
    """特定のユーザー情報を取得します（管理者専用）。

    Args:
        user_id (uuid.UUID): 取得するユーザーのUUID
        user_service (UserService): ユーザーサービス（自動注入）
        current_user (User): 認証済みユーザー（権限チェック用、自動注入）

    Returns:
        UserResponse: 指定されたユーザーの情報
            - すべてのユーザー属性を含む
            - リレーションシップは遅延ロードされます

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 管理者権限がない（SystemAdminロール必須）
            - 404: ユーザーが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/users/12345678-1234-1234-1234-123456789abc
        >>> Authorization: Bearer <Admin_Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
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

    Note:
        - SystemAdminロールを持つユーザーのみアクセス可能です
        - 自分以外のユーザー情報を取得する場合に使用します
        - 監査ログに記録されます
    """
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

    return UserResponse.model_validate(user)


# ================================================================================
# PATCH Endpoints
# ================================================================================


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="ユーザー情報更新",
    description="""
    現在のユーザー情報を更新します。

    更新可能なフィールド:
        - display_name: 表示名
        - roles: システムレベルのロール（管理者のみ）
        - is_active: アクティブフラグ（管理者のみ）

    注意:
        - email と azure_oid は更新できません
        - roles と is_active の更新にはSystemAdminロールが必要です
        - 指定されたフィールドのみが更新されます（PATCH）
    """,
)
@handle_service_errors
async def update_current_user(
    update_data: UserUpdate,
    current_user: CurrentUserAzureDep,
    user_service: AzureUserServiceDep,
) -> UserResponse:
    """現在のユーザー情報を更新します。

    このエンドポイントは、認証済みユーザー自身の情報を更新します。
    一部のフィールド（roles, is_active）の更新には管理者権限が必要です。

    Args:
        update_data (UserUpdate): 更新データ
            - display_name: 表示名（オプション）
            - roles: システムレベルのロール（オプション、管理者のみ）
            - is_active: アクティブフラグ（オプション、管理者のみ）
        current_user (User): 認証済みユーザー（自動注入）
        user_service (UserService): ユーザーサービス（自動注入）

    Returns:
        UserResponse: 更新されたユーザー情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 管理者権限が必要なフィールドの更新を試行
            - 422: バリデーションエラー
            - 500: 内部エラー

    Example:
        >>> # リクエスト（一般ユーザー: display_nameのみ更新）
        >>> PATCH /api/v1/users/me
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "display_name": "John Smith"
        ... }
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": "12345678-1234-1234-1234-123456789abc",
        ...     "azure_oid": "azure-oid-12345",
        ...     "email": "user@company.com",
        ...     "display_name": "John Smith",
        ...     "roles": ["User"],
        ...     "is_active": true,
        ...     "created_at": "2024-01-01T00:00:00Z",
        ...     "updated_at": "2024-01-15T10:30:00Z",
        ...     "last_login": "2024-01-15T10:30:00Z"
        ... }

    Note:
        - 管理者権限を持たないユーザーが roles や is_active を更新しようとすると403エラー
        - email と azure_oid は更新できません（Azure ADで管理）
        - 指定されたフィールドのみが更新されます（部分更新）
    """
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
        return UserResponse.model_validate(current_user)

    # サービス層を使用してユーザー情報を更新
    # サービス層で権限チェック、バリデーション、ビジネスロジックを実行
    updated_user = await user_service.update_user(
        user_id=current_user.id,
        update_data=update_dict,
        current_user_roles=current_user.roles,
    )

    return UserResponse.model_validate(updated_user)


# ================================================================================
# DELETE Endpoints
# ================================================================================


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ユーザー削除",
    description="""
    指定されたIDのユーザーを削除します。

    **管理者権限が必要です（SystemAdminロール）。**

    パスパラメータ:
        - user_id: ユーザーID（UUID形式）

    注意:
        - 削除は物理削除です（データベースから完全に削除されます）
        - CASCADE設定により、関連する ProjectMember も自動削除されます
        - 自分自身を削除することはできません
        - この操作は取り消せません
    """,
)
@handle_service_errors
async def delete_user(
    user_id: uuid.UUID,
    user_service: AzureUserServiceDep,
    current_user: CurrentUserAzureDep,
) -> None:
    """ユーザーを削除します（管理者専用）。

    Args:
        user_id (uuid.UUID): 削除するユーザーのUUID
        user_service (UserService): ユーザーサービス（自動注入）
        current_user (User): 認証済みユーザー（権限チェック用、自動注入）

    Returns:
        None: 204 No Content（削除成功）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 管理者権限がない（SystemAdminロール必須）
            - 404: ユーザーが見つからない
            - 422: 自分自身を削除しようとした
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> DELETE /api/v1/users/12345678-1234-1234-1234-123456789abc
        >>> Authorization: Bearer <Admin_Azure_AD_Token>
        >>>
        >>> # レスポンス (204 No Content)
        >>> # レスポンスボディなし

    Note:
        - SystemAdminロールを持つユーザーのみアクセス可能です
        - 自分自身を削除することはできません
        - CASCADE設定により、関連する ProjectMember も自動削除されます
        - 削除操作は監査ログに記録されます
        - この操作は取り消せません（物理削除）
    """
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

    # ユーザーを取得
    user = await user_service.get_user(user_id)
    if not user:
        logger.warning(
            "削除対象のユーザーが見つかりません",
            admin_user_id=str(current_user.id),
            target_user_id=str(user_id),
        )
        raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

    # ユーザーを削除（リポジトリ経由）
    await user_service.repository.delete(user_id)

    # データベースに反映
    await user_service.db.flush()

    logger.info(
        "ユーザーを削除しました",
        admin_user_id=str(current_user.id),
        deleted_user_id=str(user_id),
        deleted_user_email=user.email,
    )
