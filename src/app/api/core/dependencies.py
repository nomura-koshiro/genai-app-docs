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

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.models.sample_user import SampleUser
from app.services.sample_agent import SampleAgentService
from app.services.sample_file import SampleFileService
from app.services.sample_session import SampleSessionService
from app.services.sample_user import SampleUserService

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


# 認証依存性
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
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # "Bearer <token>"からトークンを抽出
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # トークンをデコード
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        # データベースからユーザーを取得
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await user_service.get_user(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed") from e


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
        HTTPException: ユーザーが無効化されている場合（400エラー）

    Example:
        >>> @router.get("/active-only")
        >>> async def active_only_endpoint(user: CurrentUserDep):
        ...     return {"message": "Active user access granted"}

    Note:
        - is_active=Falseのユーザーはアクセスを拒否されます
        - ほとんどのエンドポイントでこの依存性を使用することを推奨します
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


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
