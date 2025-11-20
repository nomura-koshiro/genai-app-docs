"""開発モード用のモック認証。

開発環境で簡易的な認証を提供します。

主な機能:
    - DevUser: Azure AD Userと互換性のあるモックユーザー
    - get_current_dev_user(): モック認証ユーザー取得

セキュリティ考慮事項:
    - このモジュールは開発環境専用です
    - 本番環境では絶対に使用しないでください
    - モックトークンは固定値です（DEV_MOCK_TOKEN）

使用例:
    >>> from app.core.security.dev_auth import get_current_dev_user
    >>> from fastapi import Depends
    >>>
    >>> @router.get("/dev-test")
    >>> async def dev_test(dev_user = Depends(get_current_dev_user)):
    ...     return {"email": dev_user.email, "oid": dev_user.oid}
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

security = HTTPBearer()


class DevUser:
    """開発モード用のモックユーザークラス。

    Azure AD Userと互換性のある構造を持ちます。

    Attributes:
        oid (str): Azure AD Object ID（モック値）
        preferred_username (str): メールアドレス（モック値）
        email (str): メールアドレス（モック値）
        name (str): 表示名（モック値）
        roles (list): ロールリスト（空リスト）

    Example:
        >>> dev_user = DevUser()
        >>> print(dev_user.email)
        'dev.user@example.com'
        >>> print(dev_user.oid)
        'dev-azure-oid-12345'
    """

    def __init__(self):
        """DevUserインスタンスを初期化します。

        環境変数から以下の設定を読み込みます:
            - DEV_MOCK_USER_OID: Azure Object ID
            - DEV_MOCK_USER_EMAIL: メールアドレス
            - DEV_MOCK_USER_NAME: 表示名
        """
        self.oid = settings.DEV_MOCK_USER_OID
        self.preferred_username = settings.DEV_MOCK_USER_EMAIL
        self.email = settings.DEV_MOCK_USER_EMAIL
        self.name = settings.DEV_MOCK_USER_NAME
        # rolesはデータベースの値を保持するため、Noneにする
        # これにより、get_or_create_by_azure_oidで既存のrolesが上書きされない
        self.roles = None

    def __repr__(self):
        """オブジェクトの文字列表現を返します。

        Returns:
            str: "<DevUser {email}>" 形式の文字列

        Example:
            >>> dev_user = DevUser()
            >>> print(repr(dev_user))
            '<DevUser dev.user@example.com>'
        """
        return f"<DevUser {self.email}>"


async def get_current_dev_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> DevUser:
    """開発モード用の認証（トークンチェックのみ）。

    Authorizationヘッダーから受け取ったBearerトークンが
    環境変数DEV_MOCK_TOKENと一致するかをチェックします。

    Args:
        credentials: HTTPAuthorizationCredentials
            - Authorizationヘッダーから自動抽出される
            - 形式: "Bearer mock-access-token-dev-12345"

    Returns:
        DevUser: モックユーザー情報

    Raises:
        HTTPException: トークンが一致しない場合（401 Unauthorized）

    Example:
        >>> # 正しいトークン
        >>> # Authorization: Bearer mock-access-token-dev-12345
        >>> dev_user = await get_current_dev_user(credentials)
        >>> print(dev_user.email)
        'dev.user@example.com'
        >>>
        >>> # 間違ったトークン
        >>> # Authorization: Bearer wrong-token
        >>> dev_user = await get_current_dev_user(credentials)
        HTTPException: 401 Unauthorized

    Note:
        - トークンは環境変数DEV_MOCK_TOKENで設定します
        - デフォルトトークン: "mock-access-token-dev-12345"
        - 本番環境では絶対に使用しないでください
    """
    token = credentials.credentials

    # モックトークンと一致するかチェック
    if token != settings.DEV_MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid development token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return DevUser()
