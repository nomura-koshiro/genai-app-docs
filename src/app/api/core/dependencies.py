"""FastAPI依存性注入（Dependency Injection）システムの定義。

このモジュールは、FastAPIのDepends機能を使用した依存性注入を提供します。
データベースセッション、各種サービス、認証ユーザーなどの依存性を
エンドポイント関数に注入するための関数とアノテーションを定義しています。

依存性の種類:
    1. データベース依存性:
       - DatabaseDep: 非同期データベースセッション

    2. サービス依存性:
       - UserServiceDep: ユーザーサービス

    3. 認証依存性:
       - CurrentUserDep: 認証済みアクティブユーザー（必須）
       - CurrentSuperuserDep: スーパーユーザー（必須）
       - CurrentUserOptionalDep: 認証ユーザー（オプション）

使用例:
    >>> from fastapi import APIRouter
    >>> from app.api.dependencies import CurrentUserDep, UserServiceDep
    >>>
    >>> @router.get("/profile")
    >>> async def get_profile(
    ...     current_user: CurrentUserDep,
    ...     user_service: UserServiceDep,
    ... ):
    ...     return {"email": current_user.email}
"""

from typing import TYPE_CHECKING, Annotated, NoReturn

__all__ = [
    # 型エイリアス
    "AuthUserType",
    # データベース依存性
    "DatabaseDep",
    "get_db",
    # サービス依存性
    "UserServiceDep",
    "AzureUserServiceDep",
    "AgentServiceDep",
    "FileServiceDep",
    "SessionServiceDep",
    "ProjectServiceDep",
    # サービスファクトリ関数
    "get_user_service",
    "get_azure_user_service",
    "get_agent_service",
    "get_file_service",
    "get_session_service",
    "get_project_service",
    # 認証依存性（型アノテーション）
    "CurrentUserDep",
    "CurrentSuperuserDep",
    "CurrentUserOptionalDep",
    "CurrentUserAzureDep",
    # 認証ファクトリ関数
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "get_current_user_optional",
    "get_authenticated_user_from_azure",
    "get_current_active_user_azure",
    # ヘルパー関数
    "verify_active_user",
]

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.models import SampleUser, User
from app.services import (
    ProjectService,
    SampleAgentService,
    SampleFileService,
    SampleSessionService,
    SampleUserService,
    UserService,
)

# ================================================================================
# Azure AD / 開発モード認証のインポート
# ================================================================================

# 認証モードに応じてインポート
if TYPE_CHECKING:
    from app.core.security.azure_ad import AzureUser as AuthUserType
    from app.core.security.azure_ad import get_current_azure_user
    from app.core.security.dev_auth import get_current_dev_user
elif settings.AUTH_MODE == "production":
    from app.core.security.azure_ad import AzureUser as AuthUserType
    from app.core.security.azure_ad import get_current_azure_user

    def get_current_dev_user() -> NoReturn:
        raise NotImplementedError("Dev auth not available in production mode")
else:
    from app.core.security.dev_auth import DevUser as AuthUserType  # type: ignore[assignment]
    from app.core.security.dev_auth import get_current_dev_user

    def get_current_azure_user() -> NoReturn:
        raise NotImplementedError("Azure auth not available in development mode")


# データベース依存性
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
"""データベースセッションの依存性型。

FastAPIのDependsを使用して、エンドポイント関数に非同期データベースセッションを
自動的に注入します。セッションのライフサイクルはリクエストごとに管理されます。
"""


# サービス依存性
def get_user_service(db: DatabaseDep) -> SampleUserService:
    """ユーザーサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        SampleUserService: 初期化されたユーザーサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
    """
    return SampleUserService(db)


UserServiceDep = Annotated[SampleUserService, Depends(get_user_service)]
"""ユーザーサービスの依存性型。"""


def get_azure_user_service(db: DatabaseDep) -> UserService:
    """Azure AD用ユーザーサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        UserService: 初期化されたAzure AD用ユーザーサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
        - Azure AD認証用の新しいUserモデルを使用します
    """
    return UserService(db)


AzureUserServiceDep = Annotated[UserService, Depends(get_azure_user_service)]
"""Azure AD用ユーザーサービスの依存性型。"""


def get_agent_service(db: DatabaseDep) -> SampleAgentService:
    """エージェントサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        SampleAgentService: 初期化されたエージェントサービスインスタンス
    """
    return SampleAgentService(db)


AgentServiceDep = Annotated[SampleAgentService, Depends(get_agent_service)]
"""エージェントサービスの依存性型。"""


def get_file_service(db: DatabaseDep) -> SampleFileService:
    """ファイルサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        SampleFileService: 初期化されたファイルサービスインスタンス
    """
    return SampleFileService(db)


FileServiceDep = Annotated[SampleFileService, Depends(get_file_service)]
"""ファイルサービスの依存性型。"""


def get_session_service(db: DatabaseDep) -> SampleSessionService:
    """セッションサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        SampleSessionService: 初期化されたセッションサービスインスタンス
    """
    return SampleSessionService(db)


SessionServiceDep = Annotated[SampleSessionService, Depends(get_session_service)]
"""セッションサービスの依存性型。"""


def get_project_service(db: DatabaseDep) -> ProjectService:
    """プロジェクトサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        ProjectService: 初期化されたプロジェクトサービスインスタンス
    """
    return ProjectService(db)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
"""プロジェクトサービスの依存性型。"""


# ================================================================================
# ヘルパー関数
# ================================================================================


def verify_active_user[UserType: (SampleUser, User)](user: UserType) -> UserType:
    """ユーザーのアクティブ状態を検証します（DRY原則）。

    この関数は、SampleUserとUserの両方のモデルで使用できる汎用的な
    アクティブ状態検証ロジックを提供します。

    Args:
        user: 検証対象のユーザー（SampleUser または User）

    Returns:
        アクティブなユーザー（同じ型）

    Raises:
        HTTPException: ユーザーが無効化されている場合（403エラー）

    Example:
        >>> user = await get_current_user(...)
        >>> active_user = verify_active_user(user)

    Note:
        - is_active=Falseのユーザーはアクセスを拒否されます
        - 403 Forbidden を返す（権限不足を示す）
    """
    if not user.is_active:
        raise HTTPException(
            status_code=403,  # Forbidden（権限不足/アカウント無効化）
            detail="アカウントが無効化されています",
        )
    return user


# ================================================================================
# 認証依存性
# ================================================================================


async def get_current_user(
    user_service: UserServiceDep,
    authorization: str | None = Header(None),
) -> SampleUser:
    """Authorizationヘッダー（Bearer token）からJWTトークンを検証し、認証ユーザーを取得します。

    このDI関数は以下の処理を実行します：
    1. AuthorizationヘッダーからBearerトークンを抽出
    2. JWTトークンをデコードして検証
    3. トークンペイロードからuser_idを抽出
    4. データベースからユーザー情報を取得

    Args:
        user_service (SampleUserService): ユーザーサービス（自動注入）
        authorization (str | None): Authorizationヘッダー
            フォーマット: "Bearer <JWT_TOKEN>"

    Returns:
        SampleUser: 認証されたユーザーモデルインスタンス

    Raises:
        HTTPException: 以下の場合に401エラーを返す
            - Authorizationヘッダーが存在しない
            - Bearer形式でない
            - JWTトークンが無効または期限切れ
            - トークンペイロードにuser_idが含まれない
            - ユーザーが存在しない

    Example:
        >>> @router.get("/protected")
        >>> async def protected_endpoint(user: Annotated[SampleUser, Depends(get_current_user)]):
        ...     return {"user_id": user.id, "email": user.email}

    Note:
        - トークンの有効期限は自動的に検証されます
        - ユーザーの is_active フィールドは検証されません
        - アクティブユーザーのみを許可する場合は get_current_active_user を使用してください
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="認証ヘッダーが必要です",
            headers={"WWW-Authenticate": 'Bearer realm="API"'},
        )

    try:
        # "Bearer <token>"からトークンを抽出
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Bearer認証スキームが必要です",
                headers={"WWW-Authenticate": 'Bearer realm="API"'},
            )

        # トークンをデコード
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="トークンが無効です",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # データベースからユーザーを取得
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="トークンペイロードが不正です",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        user = await user_service.get_user(int(user_id))
        if not user:
            raise HTTPException(
                status_code=401,
                detail="ユーザーが見つかりません",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        return user

    except HTTPException:
        # すでに適切に処理されたHTTPExceptionは再度raiseする
        raise
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=f"認証エラー: {str(e)}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=f"トークン形式が不正です: {str(e)}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from e
    except Exception as e:
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.exception("予期しない認証エラー", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="認証処理中にエラーが発生しました",
        ) from e


async def get_current_active_user(
    current_user: Annotated[SampleUser, Depends(get_current_user)],
) -> SampleUser:
    """認証されたユーザーのアクティブ状態を検証します。

    この関数は get_current_user に加えて、ユーザーの is_active フィールドを検証します。
    無効化されたアカウントへのアクセスを防止します。

    Args:
        current_user (SampleUser): 認証済みユーザー（get_current_userから自動注入）

    Returns:
        SampleUser: アクティブな認証済みユーザー

    Raises:
        HTTPException: ユーザーが無効化されている場合（403エラー）

    Example:
        >>> @router.get("/active-only")
        >>> async def active_only_endpoint(user: CurrentUserDep):
        ...     return {"message": "Active user access granted"}

    Note:
        - is_active=Falseのユーザーはアクセスを拒否されます（403 Forbidden）
        - ほとんどのエンドポイントでこの依存性を使用することを推奨します
    """
    return verify_active_user(current_user)


async def get_current_superuser(
    current_user: Annotated[SampleUser, Depends(get_current_active_user)],
) -> SampleUser:
    """スーパーユーザー権限を検証します。

    この関数は get_current_active_user に加えて、ユーザーの is_superuser フィールドを
    検証します。管理者専用エンドポイントへのアクセスを制限します。

    Args:
        current_user (SampleUser): アクティブな認証済みユーザー
            （get_current_active_userから自動注入）

    Returns:
        SampleUser: スーパーユーザー権限を持つユーザー

    Raises:
        HTTPException: ユーザーがスーパーユーザーでない場合（403エラー）

    Example:
        >>> @router.delete("/admin/users/{user_id}")
        >>> async def delete_user(
        ...     user_id: int,
        ...     superuser: CurrentSuperuserDep
        ... ):
        ...     return {"message": "User deleted"}

    Note:
        - is_superuser=Falseのユーザーはアクセスを拒否されます
        - 管理者専用の危険な操作には必ずこの依存性を使用してください
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


# ================================================================================
# ✨ 新規: Azure AD / 開発モード認証
# ================================================================================


async def get_authenticated_user_from_azure(
    user_service: AzureUserServiceDep,
    azure_user: AuthUserType = Depends(get_current_azure_user if settings.AUTH_MODE == "production" else get_current_dev_user),
) -> User:
    """Azure AD または開発モードから認証されたユーザーを取得し、DBのUserモデルと紐付け。

    環境変数AUTH_MODEに応じて以下を切り替え:
    - production: Azure ADトークン検証
    - development: モックトークン検証

    Args:
        user_service: Azure AD用ユーザーサービス（自動注入）
        azure_user: Azure ADまたはDevユーザー（自動注入）

    Returns:
        User: データベースのユーザーモデル（新しいAzure AD対応モデル）

    Raises:
        HTTPException: ユーザーが見つからない、または作成できない場合（404エラー）

    Example:
        >>> # 開発モード
        >>> # Authorization: Bearer mock-access-token-dev-12345
        >>> user = await get_authenticated_user_from_azure(user_service, dev_user)
        >>> print(user.email)
        'dev.user@example.com'
        >>>
        >>> # 本番モード
        >>> # Authorization: Bearer <Azure_AD_Token>
        >>> user = await get_authenticated_user_from_azure(user_service, azure_user)
        >>> print(user.email)
        'user@company.com'

    Note:
        - Azure OIDでユーザーを検索、存在しない場合は自動作成します
        - 既存ユーザーの場合、メール/表示名が変わっていれば更新します
        - この関数は既存のJWT認証（get_current_user）と並行して使用できます
        - 新しいUserモデル（UUID主キー、azure_oid）を使用します
    """
    # Azure OIDでユーザーを検索（または作成）
    user = await user_service.get_or_create_by_azure_oid(
        azure_oid=azure_user.oid,
        email=azure_user.email or azure_user.preferred_username,
        display_name=getattr(azure_user, "name", None),
        roles=getattr(azure_user, "roles", []),
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found or could not be created")

    return user


async def get_current_active_user_azure(
    current_user: Annotated[User, Depends(get_authenticated_user_from_azure)],
) -> User:
    """Azure AD認証されたユーザーのアクティブ状態を検証します。

    Args:
        current_user: 認証済みユーザー（get_authenticated_user_from_azureから自動注入）

    Returns:
        User: アクティブな認証済みユーザー（新しいAzure AD対応モデル）

    Raises:
        HTTPException: ユーザーが無効化されている場合（403エラー）

    Example:
        >>> @router.get("/azure-protected")
        >>> async def azure_protected(user: CurrentUserAzureDep):
        ...     return {"message": f"Hello, {user.email}"}

    Note:
        - is_active=Falseのユーザーはアクセスを拒否されます（403 Forbidden）
    """
    return verify_active_user(current_user)


# オプション認証（認証あり/なし両対応のエンドポイント用）
async def get_current_user_optional(
    user_service: UserServiceDep,
    authorization: str | None = Header(None),
) -> SampleUser | None:
    """認証ユーザーを取得しますが、認証なしでもエラーを発生させません。

    この関数は get_current_user と同じ処理を実行しますが、認証が失敗した場合や
    Authorizationヘッダーが存在しない場合に例外を発生させず、Noneを返します。
    認証済みユーザーとゲストユーザーの両方に対応するエンドポイントで使用します。

    Args:
        user_service (SampleUserService): ユーザーサービス（自動注入）
        authorization (str | None): Authorizationヘッダー
            フォーマット: "Bearer <JWT_TOKEN>"

    Returns:
        SampleUser | None: 認証されたユーザー、または None（認証失敗/未認証）

    Example:
        >>> @router.get("/optional-auth")
        >>> async def optional_auth_endpoint(user: CurrentUserOptionalDep):
        ...     if user:
        ...         return {"message": f"Hello, {user.username}"}
        ...     return {"message": "Hello, guest"}

    Note:
        - 認証エラーは例外として発生せず、Noneが返されます
        - エンドポイント内でuserがNoneかどうかをチェックする必要があります
        - セッション管理やファイル管理などで使用されています
    """
    if not authorization:
        return None

    try:
        return await get_current_user(user_service, authorization)
    except HTTPException:
        return None


CurrentUserDep = Annotated[SampleUser, Depends(get_current_active_user)]
"""認証済みアクティブユーザーの依存性型。

この依存性を使用すると、エンドポイントは認証とアクティブ状態の検証を自動的に実行します。
未認証ユーザーや無効化されたユーザーはアクセスを拒否されます。
"""

CurrentSuperuserDep = Annotated[SampleUser, Depends(get_current_superuser)]
"""スーパーユーザーの依存性型。

この依存性を使用すると、エンドポイントは管理者権限を自動的に検証します。
スーパーユーザーでないユーザーはアクセスを拒否されます（403エラー）。
"""

CurrentUserOptionalDep = Annotated[SampleUser | None, Depends(get_current_user_optional)]
"""オプション認証ユーザーの依存性型。

この依存性を使用すると、エンドポイントは認証済みユーザーとゲストユーザーの
両方に対応します。認証失敗時に例外を発生させず、Noneを返します。
"""

# ✨ 新規: Azure AD認証用依存性型
CurrentUserAzureDep = Annotated[User, Depends(get_current_active_user_azure)]
"""Azure AD認証済みアクティブユーザーの依存性型。

この依存性を使用すると、エンドポイントはAzure AD認証（本番）またはモック認証（開発）を
自動的に実行します。環境変数AUTH_MODEで切り替えます。

注意: このUserモデルはSampleUserとは異なる新しいAzure AD対応モデルです。
- プライマリキーがUUID型
- azure_oidフィールドを持つ
- パスワード認証は含まない（Azure ADのみ）

使用例:
    >>> @router.get("/profile")
    >>> async def get_profile(user: CurrentUserAzureDep):
    ...     return {"email": user.email, "azure_oid": user.azure_oid, "display_name": user.display_name}
"""
