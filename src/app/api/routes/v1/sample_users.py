"""サンプルユーザー管理APIエンドポイント。

このモジュールは、ユーザーのCRUD操作と認証機能を提供する
サンプルRESTful APIエンドポイントを定義します。

主な機能:
    - ユーザー登録（POST /api/v1/sample-users）
    - ユーザーログイン（POST /api/v1/sample-users/sample-login）
    - 現在のユーザー情報取得（GET /api/v1/sample-users/sample-me）
    - ユーザー一覧取得（GET /api/v1/sample-users - 管理者のみ）
    - 特定ユーザー取得（GET /api/v1/sample-users/{user_id} - 管理者のみ）

セキュリティ:
    - JWT Bearer認証
    - スーパーユーザー権限チェック（管理者専用エンドポイント）

使用例:
    >>> # ユーザー登録
    >>> POST /api/v1/sample-users
    >>> {
    ...     "email": "user@example.com",
    ...     "username": "testuser",
    ...     "password": "SecurePass123!"
    ... }
    >>>
    >>> # ログイン
    >>> POST /api/v1/sample-users/sample-login
    >>> {
    ...     "email": "user@example.com",
    ...     "password": "SecurePass123!"
    ... }
    >>> # レスポンス: {"access_token": "eyJ...", "token_type": "bearer"}
"""

from fastapi import APIRouter, Request, status

from app.api.core import (
    CurrentSuperuserDep,
    CurrentUserDep,
    DatabaseDep,
    UserServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token
from app.schemas.sample_user import (
    SampleAPIKeyResponse,
    SampleRefreshTokenRequest,
    SampleToken,
    SampleTokenWithRefresh,
    SampleUserCreate,
    SampleUserLogin,
    SampleUserResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=SampleUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新しいサンプルユーザーを作成",
    description="""
    新しいサンプルユーザーアカウントを作成します。

    - **email**: ユーザーのメールアドレス（一意制約）
    - **username**: ユーザー名（一意制約、最大50文字）
    - **password**: パスワード（bcryptでハッシュ化されて保存）

    作成されたユーザーはデフォルトでアクティブ状態（is_active=True）です。
    """,
)
@handle_service_errors
async def create_user(
    user_data: SampleUserCreate,
    user_service: UserServiceDep,
) -> SampleUserResponse:
    """新しいユーザーアカウントを作成します。

    Args:
        user_data (UserCreate): ユーザー作成用のPydanticスキーマ
            - email: メールアドレス（一意）
            - username: ユーザー名（一意）
            - password: パスワード（平文、ハッシュ化されて保存）
        user_service (UserService): ユーザーサービス（自動注入）

    Returns:
        UserResponse: 作成されたユーザー情報
            - id: 自動生成されたユーザーID
            - email, username: 入力値
            - is_active: True
            - is_superuser: False
            - created_at, updated_at: タイムスタンプ

    Raises:
        HTTPException:
            - 400: メールアドレスまたはユーザー名が既に使用されている
            - 500: データベースエラーなどの内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/users
        >>> {
        ...     "email": "newuser@example.com",
        ...     "username": "newuser",
        ...     "password": "SecurePass123!"
        ... }
        >>>
        >>> # レスポンス (201 Created)
        >>> {
        ...     "id": 1,
        ...     "email": "newuser@example.com",
        ...     "username": "newuser",
        ...     "is_active": true,
        ...     "is_superuser": false,
        ...     "created_at": "2024-01-01T00:00:00Z",
        ...     "updated_at": "2024-01-01T00:00:00Z"
        ... }
    """
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(user)


@router.post(
    "/sample-login",
    response_model=SampleTokenWithRefresh,
    summary="サンプルユーザーログイン",
    description="""
    サンプルユーザーのメールアドレスとパスワードで認証し、
    JWT アクセストークンとリフレッシュトークンを発行します。

    - **email**: ユーザーのメールアドレス
    - **password**: ユーザーのパスワード

    発行されたトークンは、`Authorization: Bearer <token>` ヘッダーで認証に使用できます。
    """,
)
@handle_service_errors
async def login(
    request: Request,
    user_credentials: SampleUserLogin,
    user_service: UserServiceDep,
    db: DatabaseDep,
) -> SampleTokenWithRefresh:
    """ユーザーログインしてJWTアクセストークンを発行します。

    Args:
        request (Request): FastAPIリクエストオブジェクト（クライアントIP取得用）
        user_credentials (UserLogin): ログイン情報
            - email: メールアドレス
            - password: パスワード（平文）
        user_service (UserService): ユーザーサービス（自動注入）

    Returns:
        Token: JWTアクセストークンとトークンタイプ
            - access_token: JWT文字列
            - token_type: "bearer"

    Raises:
        HTTPException:
            - 401: 認証失敗（メールアドレスまたはパスワードが間違っている）
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/users/login
        >>> {
        ...     "email": "user@example.com",
        ...     "password": "SecurePass123!"
        ... }
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     "token_type": "bearer"
        ... }
        >>>
        >>> # 使用方法
        >>> # Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    # クライアントIPアドレスを取得
    client_ip = request.client.host if request.client else None

    # ユーザー認証
    user = await user_service.authenticate(
        email=user_credentials.email,
        password=user_credentials.password,
        client_ip=client_ip,
    )

    # JWTトークンを生成
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # リフレッシュトークンをハッシュ化してデータベースに保存
    from datetime import UTC, datetime, timedelta

    from app.core.security import hash_password

    user.refresh_token_hash = hash_password(refresh_token)
    user.refresh_token_expires_at = datetime.now(UTC) + timedelta(days=7)
    await db.commit()

    return SampleTokenWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get(
    "/sample-me",
    response_model=SampleUserResponse,
    summary="現在のサンプルユーザー情報取得",
    description="""
    認証されたサンプルユーザー自身の情報を取得します。

    このエンドポイントはJWT認証が必須です。
    `Authorization: Bearer <token>` ヘッダーが必要です。
    """,
)
@handle_service_errors
async def get_current_user(
    current_user: CurrentUserDep,
) -> SampleUserResponse:
    """現在の認証済みユーザーの情報を取得します。

    Args:
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        UserResponse: 現在のユーザー情報
            - id, email, username, is_active, is_superuser
            - created_at, updated_at

    Example:
        >>> # リクエスト
        >>> GET /api/v1/users/me
        >>> Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": 1,
        ...     "email": "user@example.com",
        ...     "username": "testuser",
        ...     "is_active": true,
        ...     "is_superuser": false,
        ...     "created_at": "2024-01-01T00:00:00Z",
        ...     "updated_at": "2024-01-01T00:00:00Z"
        ... }
    """
    return SampleUserResponse.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=SampleUserResponse,
    summary="特定サンプルユーザー情報取得",
    description="""
    指定されたIDのサンプルユーザー情報を取得します。

    **スーパーユーザー権限が必要です。**
    """,
)
@handle_service_errors
async def get_user(
    user_id: int,
    user_service: UserServiceDep,
    _superuser: CurrentSuperuserDep,
) -> SampleUserResponse:
    """特定のユーザー情報を取得します（管理者専用）。

    Args:
        user_id (int): 取得するユーザーのID
        user_service (UserService): ユーザーサービス（自動注入）
        _superuser (User): スーパーユーザー（権限チェック用、自動注入）

    Returns:
        UserResponse: 指定されたユーザーの情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: スーパーユーザー権限がない
            - 404: ユーザーが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/users/123
        >>> Authorization: Bearer <superuser_token>
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": 123,
        ...     "email": "user@example.com",
        ...     "username": "testuser",
        ...     "is_active": true,
        ...     "is_superuser": false,
        ...     "created_at": "2024-01-01T00:00:00Z",
        ...     "updated_at": "2024-01-01T00:00:00Z"
        ... }
    """
    user = await user_service.get_user(user_id)
    if not user:
        raise NotFoundError("ユーザーが見つかりません", details={"user_id": user_id})
    return SampleUserResponse.model_validate(user)


@router.get(
    "",
    response_model=list[SampleUserResponse],
    summary="サンプルユーザー一覧取得",
    description="""
    登録されているすべてのサンプルユーザーの一覧を取得します。

    **スーパーユーザー権限が必要です。**

    - **skip**: スキップするレコード数（デフォルト: 0）
    - **limit**: 取得する最大レコード数（デフォルト: 100）
    """,
)
@handle_service_errors
async def list_users(
    user_service: UserServiceDep,
    _superuser: CurrentSuperuserDep,
    skip: int = 0,
    limit: int = 100,
) -> list[SampleUserResponse]:
    """ユーザー一覧を取得します（管理者専用）。

    Args:
        user_service (UserService): ユーザーサービス（自動注入）
        _superuser (User): スーパーユーザー（権限チェック用、自動注入）
        skip (int): スキップするレコード数（ページネーション用）
        limit (int): 取得する最大レコード数（最大100）

    Returns:
        list[UserResponse]: ユーザー情報のリスト

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: スーパーユーザー権限がない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/users?skip=0&limit=10
        >>> Authorization: Bearer <superuser_token>
        >>>
        >>> # レスポンス (200 OK)
        >>> [
        ...     {
        ...         "id": 1,
        ...         "email": "user1@example.com",
        ...         "username": "user1",
        ...         "is_active": true,
        ...         "is_superuser": false,
        ...         "created_at": "2024-01-01T00:00:00Z",
        ...         "updated_at": "2024-01-01T00:00:00Z"
        ...     },
        ...     {
        ...         "id": 2,
        ...         "email": "user2@example.com",
        ...         "username": "user2",
        ...         "is_active": true,
        ...         "is_superuser": false,
        ...         "created_at": "2024-01-02T00:00:00Z",
        ...         "updated_at": "2024-01-02T00:00:00Z"
        ...     }
        ... ]
    """
    users = await user_service.list_users(skip=skip, limit=limit)
    return [SampleUserResponse.model_validate(user) for user in users]


@router.post(
    "/sample-refresh",
    response_model=SampleToken,
    summary="サンプルトークンリフレッシュ",
    description="""
    リフレッシュトークンを使用して新しいサンプルアクセストークンを取得します。
    """,
)
@handle_service_errors
async def refresh_token(
    request_data: SampleRefreshTokenRequest,
    user_service: UserServiceDep,
) -> SampleToken:
    """リフレッシュトークンから新しいアクセストークンを取得します。"""
    from datetime import UTC, datetime

    from app.core.security import create_access_token, decode_refresh_token, verify_password

    # リフレッシュトークンをデコード
    payload = decode_refresh_token(request_data.refresh_token)
    if not payload:
        raise AuthenticationError("無効なリフレッシュトークンです")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("トークンにユーザーIDが含まれていません")

    user_id = int(user_id_str)
    user = await user_service.get_user(user_id)
    if not user:
        raise AuthenticationError("ユーザーが見つかりません")

    # ハッシュ化されたリフレッシュトークンと照合
    if not user.refresh_token_hash or not verify_password(request_data.refresh_token, user.refresh_token_hash):
        raise AuthenticationError("リフレッシュトークンが一致しません")

    # 有効期限チェック
    if user.refresh_token_expires_at and user.refresh_token_expires_at < datetime.now(UTC):
        raise AuthenticationError("リフレッシュトークンの有効期限が切れています")

    # 新しいアクセストークンを生成
    access_token = create_access_token(data={"sub": str(user.id)})

    return SampleToken(access_token=access_token, token_type="bearer")


@router.post(
    "/sample-api-key",
    response_model=SampleAPIKeyResponse,
    summary="サンプルAPIキー生成",
    description="""
    認証済みサンプルユーザーのAPIキーを生成します。

    既存のAPIキーがある場合は上書きされます。
    """,
)
@handle_service_errors
async def generate_user_api_key(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
    db: DatabaseDep,
) -> SampleAPIKeyResponse:
    """ユーザーのAPIキーを生成します。"""
    from datetime import UTC, datetime

    from app.core.security import generate_api_key, hash_password

    # APIキー生成
    api_key = generate_api_key()
    created_at = datetime.now(UTC)

    # ハッシュ化してデータベースに保存
    current_user.api_key_hash = hash_password(api_key)
    current_user.api_key_created_at = created_at
    await db.commit()

    logger.info(
        "APIキー生成完了",
        user_id=current_user.id,
        api_key_hashed=True,
    )

    return SampleAPIKeyResponse(
        api_key=api_key,
        created_at=created_at,
        message="APIキーは一度しか表示されません。安全に保管してください。",
    )
