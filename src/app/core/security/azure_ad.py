"""Azure AD Bearer Token検証モジュール。

本番環境でAzure ADのBearerトークンを検証します。

主な機能:
    - get_current_azure_user(): Azure ADユーザー認証
    - initialize_azure_scheme(): Azure AD認証スキーム初期化

セキュリティ:
    - fastapi-azure-authによる包括的なトークン検証
        - JWT署名検証（Azure AD公開鍵使用）
        - トークン有効期限チェック（`exp`クレーム自動検証）
        - 発行者検証（`iss`クレーム）
        - オーディエンス検証（`aud`クレーム）
        - スコープ検証（`scp`クレーム）
    - SingleTenantAzureAuthorizationCodeBearer使用
    - スコープベースのアクセス制御

トークン有効期限:
    fastapi-azure-authは、内部でpython-joseライブラリを使用してJWTトークンを
    検証しています。`exp`クレームの検証は自動的に実行され、期限切れのトークンは
    ExpiredSignatureErrorとしてHTTP 401エラーを返します。

    明示的な有効期限チェックの実装は不要です。

使用例:
    >>> from app.core.security.azure_ad import get_current_azure_user
    >>> from fastapi import Depends
    >>>
    >>> @router.get("/protected")
    >>> async def protected_route(
    ...     azure_user = Depends(get_current_azure_user)
    ... ):
    ...     return {"email": azure_user.email}

参考:
    - fastapi-azure-auth: https://github.com/Intility/fastapi-azure-auth
    - python-jose (JWT検証): https://github.com/mpdavis/python-jose
"""

from fastapi import HTTPException, Security, status

from app.core.config import settings

# fastapi-azure-authが必要（本番モードのみ）
try:
    from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer  # type: ignore[import-not-found]
    from fastapi_azure_auth.user import User as AzureUser  # type: ignore[import-not-found]

    AZURE_AUTH_AVAILABLE = True
except ImportError:
    AZURE_AUTH_AVAILABLE = False
    AzureUser = None  # type: ignore

# Azure AD認証スキーム（本番モードのみ初期化）
azure_scheme = None

if settings.AUTH_MODE == "production":
    if not AZURE_AUTH_AVAILABLE:
        raise ImportError(
            "AUTH_MODE=productionの場合、fastapi-azure-authが必要です。\n"
            "インストール: uv add fastapi-azure-auth"
        )

    azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=settings.AZURE_CLIENT_ID,
        tenant_id=settings.AZURE_TENANT_ID,
        scopes={
            f"api://{settings.AZURE_CLIENT_ID}/access_as_user": "Access API as user",
        },
        allow_guest_users=False,
    )


async def get_current_azure_user(
    user: AzureUser = Security(azure_scheme, scopes=["access_as_user"])
) -> AzureUser:
    """Azure ADから認証済みユーザーを取得（本番モードのみ）。

    この関数は、fastapi-azure-authライブラリを使用してAzure AD Bearerトークンを検証します。
    トークン検証には以下が含まれます：

    - **署名検証**: Azure ADの公開鍵による署名検証
    - **有効期限チェック**: JWTの`exp`クレームの自動検証（期限切れトークンは自動的に拒否）
    - **発行者検証**: `iss`クレームがAzure ADテナントと一致するか確認
    - **オーディエンス検証**: `aud`クレームがアプリケーションクライアントIDと一致するか確認
    - **スコープ検証**: 要求されたスコープ（access_as_user）が含まれているか確認

    トークンの有効期限チェックは、fastapi-azure-authが内部で使用している
    python-joseライブラリにより自動的に実行されます。期限切れのトークンは
    ExpiredSignatureError例外が発生し、HTTP 401エラーとして返されます。

    Args:
        user: Azure ADから取得されたユーザー情報
            - SingleTenantAzureAuthorizationCodeBearerにより既に検証済み

    Returns:
        AzureUser: Azure ADユーザー情報
            - oid: Azure Object ID（ユーザーの一意識別子）
            - email: メールアドレス
            - name: フルネーム
            - preferred_username: ユーザー名
            - roles: ロール一覧（オプション）

    Raises:
        HTTPException: 認証失敗時
            - 401 Unauthorized: トークンが無効、期限切れ、または欠落している場合
            - 403 Forbidden: トークンは有効だがスコープが不足している場合

    Security:
        トークン有効期限チェックはfastapi-azure-authが自動的に実行します。
        明示的な`exp`クレーム検証は不要です。

    Example:
        >>> from fastapi import Depends
        >>> from app.core.security.azure_ad import get_current_azure_user
        >>>
        >>> @router.get("/me")
        >>> async def get_me(azure_user = Depends(get_current_azure_user)):
        ...     return {
        ...         "email": azure_user.email,
        ...         "oid": azure_user.oid,
        ...         "name": azure_user.name
        ...     }
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Azure AD authentication failed"
        )
    return user


async def initialize_azure_scheme():
    """Azure AD認証スキームを初期化（アプリ起動時に実行）。

    この関数は、FastAPIアプリケーション起動時のlifespanイベントで呼び出されます。
    本番モード（AUTH_MODE=production）の場合、Azure ADのOpenID Connect設定を読み込みます。

    Example:
        >>> # app/core/lifespan.py
        >>> from app.core.security.azure_ad import initialize_azure_scheme
        >>>
        >>> @asynccontextmanager
        >>> async def lifespan(app: FastAPI):
        ...     # 起動時
        ...     if settings.AUTH_MODE == "production":
        ...         await initialize_azure_scheme()
        ...     yield
        ...     # 終了時
    """
    if settings.AUTH_MODE == "production" and azure_scheme:
        await azure_scheme.openid_config.load_config()
        print("✅ Azure AD authentication initialized")
    else:
        print("⚠️  Development authentication mode (Azure AD disabled)")
