"""認証依存性。

認証モードに応じた認証関数とユーザー検証機能を提供します。

依存性の種類:
    - CurrentUserAccountDep: 認証済みアクティブユーザー（必須）
    - SuperuserAccountDep: スーパーユーザー（必須）
    - CurrentUserAccountOptionalDep: 認証ユーザー（オプション）
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Any, NoReturn

from fastapi import Depends, HTTPException

from app.api.core.dependencies.user_account import UserServiceDep
from app.core.config import settings
from app.models import UserAccount

__all__ = [
    # 型エイリアス
    "AuthUserType",
    # 依存性型
    "CurrentUserAccountDep",
    "SuperuserAccountDep",
    "CurrentUserAccountOptionalDep",
    # ファクトリ関数
    "get_current_user_account",
    "get_current_active_user_account",
    "get_current_superuser_account",
    "get_current_user_account_optional",
    # ヘルパー関数
    "verify_active_user",
]

# ================================================================================
# 認証モジュールのインポート
# ================================================================================

if TYPE_CHECKING:
    from app.core.security.azure_ad import AzureUser as AuthUserType
    from app.core.security.azure_ad import get_current_azure_user
    from app.core.security.dev_auth import get_current_dev_user
elif settings.AUTH_MODE == "production":
    from app.core.security.azure_ad import AzureUser as AuthUserType
    from app.core.security.azure_ad import get_current_azure_user

    def get_current_dev_user() -> NoReturn:
        raise NotImplementedError("本番モードでは開発用認証は利用できません")
else:
    from app.core.security.dev_auth import DevUser as AuthUserType  # type: ignore[assignment]
    from app.core.security.dev_auth import get_current_dev_user

    def get_current_azure_user() -> NoReturn:
        raise NotImplementedError("開発モードではAzure認証は利用できません")


# ================================================================================
# ヘルパー関数
# ================================================================================


def verify_active_user(user: UserAccount) -> UserAccount:
    """ユーザーのアクティブ状態を検証します。

    Args:
        user: 検証対象のユーザー（UserAccount）

    Returns:
        UserAccount: アクティブなユーザー

    Raises:
        HTTPException: ユーザーが無効化されている場合（403エラー）

    Note:
        - is_active=Falseのユーザーはアクセスを拒否されます
        - 403 Forbidden を返す（権限不足を示す）
    """
    if not user.is_active:
        raise HTTPException(status_code=403, detail="アカウントが無効化されています")
    return user


# ================================================================================
# 認証依存性
# ================================================================================


def get_auth_user_dependency() -> Callable[..., Any]:
    """認証モードに応じた認証関数を返します。

    Returns:
        認証関数（get_current_azure_user または get_current_dev_user）

    Note:
        - AUTH_MODE="production": Azure AD認証
        - AUTH_MODE="development": 開発用モック認証
    """
    if settings.AUTH_MODE == "production":
        return get_current_azure_user
    return get_current_dev_user


async def get_current_user_account(
    user_service: UserServiceDep,
    auth_user: AuthUserType = Depends(get_auth_user_dependency()),
) -> UserAccount:
    """Authorizationヘッダーから認証されたユーザーを取得します。

    環境変数AUTH_MODEに応じて以下を切り替え:
    - production: Azure ADトークン検証
    - development: モックトークン検証

    Args:
        user_service: ユーザーサービス（自動注入）
        auth_user: Azure ADまたはDevユーザー（自動注入）

    Returns:
        UserAccount: データベースのユーザーモデル

    Raises:
        HTTPException: ユーザーが見つからない、または作成できない場合（404エラー）

    Note:
        - Azure OIDでユーザーを検索、存在しない場合は自動作成します
        - 既存ユーザーの場合、メール/表示名が変わっていれば更新します
        - ユーザーの is_active フィールドは検証されません
        - アクティブユーザーのみを許可する場合は get_current_active_user を使用してください
    """
    user = await user_service.get_or_create_by_azure_oid(
        azure_oid=auth_user.oid,
        email=auth_user.email or auth_user.preferred_username,
        display_name=getattr(auth_user, "name", None),
        roles=getattr(auth_user, "roles", None),
    )

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つからない、または作成できませんでした")

    return user


async def get_current_active_user_account(
    current_user: Annotated[UserAccount, Depends(get_current_user_account)],
) -> UserAccount:
    """認証されたユーザーのアクティブ状態を検証します。

    この関数は get_current_user に加えて、ユーザーの is_active フィールドを検証します。
    無効化されたアカウントへのアクセスを防止します。

    Args:
        current_user: 認証済みユーザー（get_current_userから自動注入）

    Returns:
        UserAccount: アクティブな認証済みユーザー

    Raises:
        HTTPException: ユーザーが無効化されている場合（403エラー）

    Note:
        - is_active=Falseのユーザーはアクセスを拒否されます（403 Forbidden）
        - ほとんどのエンドポイントでこの依存性を使用することを推奨します
    """
    return verify_active_user(current_user)


async def get_current_superuser_account(
    current_user: Annotated[UserAccount, Depends(get_current_active_user_account)],
) -> UserAccount:
    """スーパーユーザー（システム管理者）権限を検証します。

    この関数は get_current_active_user に加えて、ユーザーの is_superuser プロパティを
    検証します。管理者専用エンドポイントへのアクセスを制限します。

    Args:
        current_user: アクティブな認証済みユーザー（get_current_active_userから自動注入）

    Returns:
        UserAccount: システム管理者権限を持つユーザー

    Raises:
        HTTPException: ユーザーがシステム管理者でない場合（403エラー）

    Note:
        - is_superuser=False のユーザーはアクセスを拒否されます
        - 管理者専用の危険な操作には必ずこの依存性を使用してください
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="権限が不足しています")
    return current_user


async def get_current_user_account_optional(
    user_service: UserServiceDep,
    auth_user: AuthUserType | None = Depends(get_auth_user_dependency()),
) -> UserAccount | None:
    """認証ユーザーを取得しますが、認証なしでもエラーを発生させません。

    この関数は get_current_user と同じ処理を実行しますが、認証が失敗した場合に
    例外を発生させず、Noneを返します。
    認証済みユーザーとゲストユーザーの両方に対応するエンドポイントで使用します。

    Args:
        user_service: ユーザーサービス（自動注入）
        auth_user: Azure ADまたはDevユーザー（自動注入、オプション）

    Returns:
        UserAccount | None: 認証されたユーザー、または None（認証失敗/未認証）

    Note:
        - 認証エラーは例外として発生せず、Noneが返されます
        - エンドポイント内でuserがNoneかどうかをチェックする必要があります
    """
    if not auth_user:
        return None

    try:
        return await user_service.get_or_create_by_azure_oid(
            azure_oid=auth_user.oid,
            email=auth_user.email or auth_user.preferred_username,
            display_name=getattr(auth_user, "name", None),
            roles=getattr(auth_user, "roles", None),
        )
    except Exception:
        return None


# ================================================================================
# 依存性型エイリアス
# ================================================================================

CurrentUserAccountDep = Annotated[UserAccount, Depends(get_current_active_user_account)]
"""認証済みアクティブユーザーの依存性型。

この依存性を使用すると、エンドポイントは認証とアクティブ状態の検証を自動的に実行します。
未認証ユーザーや無効化されたユーザーはアクセスを拒否されます。

環境変数AUTH_MODEに応じて以下を切り替え:
- production: Azure ADトークン検証
- development: モックトークン検証
"""

SuperuserAccountDep = Annotated[UserAccount, Depends(get_current_superuser_account)]
"""スーパーユーザーの依存性型。

この依存性を使用すると、エンドポイントは管理者権限を自動的に検証します。
スーパーユーザーでないユーザーはアクセスを拒否されます（403エラー）。
"""

CurrentUserAccountOptionalDep = Annotated[UserAccount | None, Depends(get_current_user_account_optional)]
"""オプション認証ユーザーの依存性型。

この依存性を使用すると、エンドポイントは認証済みユーザーとゲストユーザーの
両方に対応します。認証失敗時に例外を発生させず、Noneを返します。
"""
