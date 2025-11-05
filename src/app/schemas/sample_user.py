"""ユーザー認証・管理のためのPydanticスキーマ。

このモジュールは、ユーザー登録、ログイン、プロフィール管理、JWT認証に関する
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    認証関連:
        - SampleUserCreate: 新規ユーザー登録リクエスト
        - SampleUserLogin: ログインリクエスト
        - SampleToken: JWTトークンレスポンス
        - SampleTokenPayload: JWTペイロード

    ユーザー情報:
        - SampleUserBase: 基本ユーザー情報（共通フィールド）
        - SampleUserResponse: ユーザー情報レスポンス

使用方法:
    >>> from app.schemas.sample_user import SampleUserCreate, SampleToken
    >>>
    >>> # ユーザー登録
    >>> user_data = SampleUserCreate(
    ...     email="user@example.com",
    ...     username="johndoe",
    ...     password="SecurePass123!"
    ... )
    >>>
    >>> # トークンレスポンス
    >>> token = SampleToken(
    ...     access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    ...     token_type="bearer"
    ... )
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SampleUserBase(BaseModel):
    """ベースユーザースキーマ。

    ユーザーの基本情報を定義します。他のユーザースキーマの基底クラスとして使用されます。

    Attributes:
        email (EmailStr): ユーザーメールアドレス
            - 自動的にメール形式検証が行われます
        username (str): ユーザー名
            - 最小3文字、最大50文字

    Example:
        >>> user = SampleUserBase(
        ...     email="john@example.com",
        ...     username="johndoe"
        ... )

    Note:
        - このクラスは直接使用せず、継承して使用します
        - EmailStr型により自動的にメール形式がバリデーションされます
    """

    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")


class SampleUserCreate(SampleUserBase):
    """新規ユーザー登録リクエストスキーマ。

    ユーザー登録時のリクエストボディを定義します。

    Attributes:
        email (EmailStr): ユーザーメールアドレス（SampleUserBaseから継承）
        username (str): ユーザー名（SampleUserBaseから継承）
        password (str): ユーザーパスワード
            - 最小8文字、最大100文字
            - 数字と大文字を含む必要があります

    Example:
        >>> user = SampleUserCreate(
        ...     email="john@example.com",
        ...     username="johndoe",
        ...     password="SecurePass123!"
        ... )

    Note:
        - passwordは平文で送信されますが、サーバー側でbcryptハッシュ化されます
        - HTTPS必須（平文パスワード送信のため）
        - POST /users/register エンドポイントで使用されます
    """

    password: str = Field(..., min_length=8, max_length=100, description="ユーザーパスワード")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """パスワード強度を検証します。

        Args:
            v (str): パスワード文字列

        Returns:
            str: 検証済みパスワード

        Raises:
            ValueError: パスワードが強度要件を満たさない場合

        Note:
            - 数字を最低1文字含む必要があります
            - 大文字を最低1文字含む必要があります
        """
        if not any(c.isdigit() for c in v):
            raise ValueError("パスワードには数字を含める必要があります")
        if not any(c.isupper() for c in v):
            raise ValueError("パスワードには大文字を含める必要があります")
        return v


class SampleUserLogin(BaseModel):
    """ユーザーログインリクエストスキーマ。

    ログイン時のリクエストボディを定義します。

    Attributes:
        email (EmailStr): ユーザーメールアドレス
        password (str): ユーザーパスワード

    Example:
        >>> login_data = SampleUserLogin(
        ...     email="john@example.com",
        ...     password="SecurePass123!"
        ... )

    Note:
        - HTTPS必須（平文パスワード送信のため）
        - POST /users/login エンドポイントで使用されます
        - 認証成功時はSampleToken型のレスポンスが返されます
    """

    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    password: str = Field(..., description="ユーザーパスワード")


class SampleUserResponse(SampleUserBase):
    """ユーザー情報レスポンススキーマ。

    ユーザー情報取得時のレスポンスボディを定義します。

    Attributes:
        id (int): ユーザーID（プライマリキー）
        email (EmailStr): ユーザーメールアドレス（SampleUserBaseから継承）
        username (str): ユーザー名（SampleUserBaseから継承）
        is_active (bool): ユーザーがアクティブかどうか
            - False: アカウント無効化
        is_superuser (bool): 管理者権限フラグ
            - デフォルト: False
        created_at (datetime): ユーザー作成日時（UTC）

    Example:
        >>> from datetime import datetime, UTC
        >>> user = SampleUserResponse(
        ...     id=1,
        ...     email="john@example.com",
        ...     username="johndoe",
        ...     is_active=True,
        ...     is_superuser=False,
        ...     created_at=datetime.now(UTC)
        ... )

    Note:
        - パスワードは含まれません（セキュリティ）
        - GET /users/me エンドポイント等で使用されます
        - model_config によりORMモデルから直接変換可能です
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ユーザーID")
    is_active: bool = Field(..., description="ユーザーがアクティブかどうか")
    is_superuser: bool = Field(False, description="ユーザーがスーパーユーザーかどうか")
    created_at: datetime = Field(..., description="ユーザー作成時刻")


class SampleToken(BaseModel):
    """JWTトークンレスポンススキーマ。

    ログイン成功時に返されるJWTアクセストークンを定義します。

    Attributes:
        access_token (str): JWTアクセストークン
            - HS256アルゴリズムで署名済み
            - 有効期限付き（通常30分）
        token_type (str): トークンタイプ
            - デフォルト: "bearer"
            - HTTPヘッダー: Authorization: Bearer <access_token>

    Example:
        >>> token = SampleToken(
        ...     access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     token_type="bearer"
        ... )

    Note:
        - クライアントはaccess_tokenを安全に保存する必要があります
        - トークンはAuthorizationヘッダーに含めてリクエストします
        - POST /users/login エンドポイントのレスポンスとして使用されます
    """

    access_token: str = Field(..., description="JWTアクセストークン")
    token_type: str = Field("bearer", description="トークンタイプ")


class SampleTokenPayload(BaseModel):
    """JWTトークンペイロードスキーマ。

    JWTトークンにエンコードされるペイロード情報を定義します。

    Attributes:
        sub (str): サブジェクト（ユーザーID）
            - JWTの標準クレーム
            - ユーザーIDの文字列表現
        exp (int): 有効期限タイムスタンプ
            - Unix epoch time（秒）
            - JWTの標準クレーム

    Example:
        >>> import time
        >>> payload = SampleTokenPayload(
        ...     sub="123",
        ...     exp=int(time.time()) + 1800  # 30分後
        ... )

    Note:
        - このスキーマは内部的に使用されます（トークン検証時）
        - クライアントには公開されません
        - decode_access_token()関数で使用されます
    """

    sub: str = Field(..., description="サブジェクト（ユーザーID）")
    exp: int = Field(..., description="有効期限タイムスタンプ")


class SampleTokenWithRefresh(BaseModel):
    """アクセストークンとリフレッシュトークンのレスポンススキーマ。"""

    access_token: str = Field(..., description="JWTアクセストークン")
    refresh_token: str = Field(..., description="JWTリフレッシュトークン")
    token_type: str = Field("bearer", description="トークンタイプ")


class SampleRefreshTokenRequest(BaseModel):
    """リフレッシュトークンリクエストスキーマ。"""

    refresh_token: str = Field(..., description="リフレッシュトークン")


class SampleAPIKeyResponse(BaseModel):
    """APIキーレスポンススキーマ。"""

    api_key: str = Field(..., description="生成されたAPIキー")
    created_at: datetime = Field(..., description="作成日時")
    message: str = Field(..., description="警告メッセージ")
