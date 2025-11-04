"""アプリケーション設定管理モジュール。

このモジュールは、環境変数と.envファイルからアプリケーション設定を読み込み、
Pydantic BaseSettingsを使用して型安全な設定オブジェクトを提供します。

主な機能:
    1. **環境別設定ファイル読み込み**:
       - 環境に応じた.envファイルを自動選択
       - .env.local（開発）、.env.staging（ステージング）、.env.production（本番）
    2. **型安全な設定管理**:
       - Pydanticによる自動バリデーション
       - 型アノテーションによるIDEサポート
    3. **セキュリティバリデーション**:
       - 本番環境でのSECRET_KEYチェック
       - ALLOWED_ORIGINSの必須化（本番環境）

設定の優先順位:
    1. 環境変数（最優先）
    2. .env.{environment}ファイル（環境別）
    3. .envファイル（共通設定）
    4. Settingsクラスのデフォルト値

使用方法:
    >>> from app.core.config import settings
    >>>
    >>> # 設定値にアクセス
    >>> print(settings.DATABASE_URL)
    "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"
    >>>
    >>> print(settings.ENVIRONMENT)
    "development"
    >>>
    >>> # 型安全（IDEが補完してくれる）
    >>> port: int = settings.PORT  # portは確実にint型

環境変数設定例:
    開発環境（.env.local）:
        ENVIRONMENT=development
        DEBUG=True
        DATABASE_URL=postgresql+asyncpg://localhost:5432/app_db
        REDIS_URL=redis://localhost:6379/0
        LLM_PROVIDER=anthropic
        ANTHROPIC_API_KEY=sk-...

    本番環境（.env.production）:
        ENVIRONMENT=production
        DEBUG=False
        DATABASE_URL=postgresql+asyncpg://prod-db:5432/app_db
        SECRET_KEY=<32文字以上のランダム文字列>
        ALLOWED_ORIGINS=["https://example.com"]
        LLM_PROVIDER=azure_openai
        AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com
        AZURE_OPENAI_API_KEY=...

Note:
    - 本番環境では SECRET_KEY と ALLOWED_ORIGINS の設定が必須です
    - .envファイルは .gitignore に含めてください（機密情報を含むため）
    - settings オブジェクトはシングルトンとして扱われます
"""

import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def get_env_file() -> tuple[str, ...]:
    """環境に応じた.envファイルのパスを取得します。

    ENVIRONMENT環境変数の値に基づいて、適切な.envファイルを選択します。
    複数のファイルが存在する場合、Pydanticは優先順位に従って読み込みます。

    環境名のマッピング:
        - development → .env.local
        - staging → .env.staging
        - production → .env.production

    読み込み優先順位:
        1. .env.{environment}（環境別設定、最優先）
        2. .env（共通設定、フォールバック）

    Returns:
        tuple[str, ...]: 読み込む.envファイルパスのタプル
            - ファイルが存在する場合のみ含まれる
            - 優先順位の高い順（最初の要素が最優先）
            - どちらも存在しない場合は (".env",) を返す（Pydantic仕様）

    Example:
        >>> # 開発環境の場合
        >>> os.environ["ENVIRONMENT"] = "development"
        >>> get_env_file()
        ('.env.local', '.env')
        >>>
        >>> # .env.localが存在しない場合
        >>> get_env_file()
        ('.env',)

    Note:
        - プロジェクトルート（src/app/の2階層上）から.envファイルを探します
        - この関数はSettingsクラスの model_config で使用されます
    """
    # 環境変数から環境を取得（デフォルト: development）
    environment = os.getenv("ENVIRONMENT", "development")

    # 環境名のマッピング
    env_mapping = {
        "development": "local",
        "staging": "staging",
        "production": "production",
    }

    env_name = env_mapping.get(environment, "local")
    project_root = Path(__file__).parent.parent.parent.parent

    # 環境別.envファイルのパス
    env_specific = project_root / f".env.{env_name}"
    env_common = project_root / ".env"

    # 存在するファイルのみを返す
    env_files = []
    if env_specific.exists():
        env_files.append(str(env_specific))
    if env_common.exists():
        env_files.append(str(env_common))

    return tuple(env_files) if env_files else (".env",)


class Settings(BaseSettings):
    """アプリケーション設定クラス。

    Pydantic BaseSettingsを継承し、環境変数と.envファイルから設定を読み込みます。
    すべての設定項目は型安全で、バリデーション済みです。

    設定カテゴリ:
        1. **アプリケーション設定**:
           - APP_NAME, VERSION, DEBUG, HOST, PORT, ALLOWED_ORIGINS

        2. **環境設定**:
           - ENVIRONMENT（development | staging | production）

        3. **セキュリティ設定**:
           - SECRET_KEY（必須、32文字以上）
           - ALGORITHM（JWT署名アルゴリズム）
           - ACCESS_TOKEN_EXPIRE_MINUTES
           - RATE_LIMIT_CALLS、RATE_LIMIT_PERIOD
           - MAX_LOGIN_ATTEMPTS、ACCOUNT_LOCK_DURATION_HOURS

        4. **データベース設定**:
           - DATABASE_URL（本番用）
           - TEST_DATABASE_URL、TEST_DATABASE_ADMIN_URL、TEST_DATABASE_NAME
           - DB_POOL_SIZE、DB_MAX_OVERFLOW、DB_POOL_RECYCLE、DB_POOL_PRE_PING

        5. **Redisキャッシュ設定**:
           - REDIS_URL、CACHE_TTL

        6. **ストレージ設定**:
           - STORAGE_BACKEND（local | azure）
           - LOCAL_STORAGE_PATH
           - AZURE_STORAGE_ACCOUNT_NAME、AZURE_STORAGE_CONNECTION_STRING、AZURE_STORAGE_CONTAINER_NAME

        7. **LLM設定**:
           - LLM_PROVIDER、LLM_MODEL、LLM_TEMPERATURE、LLM_MAX_TOKENS
           - ANTHROPIC_API_KEY
           - OPENAI_API_KEY、AZURE_OPENAI_*
           - LANGCHAIN_TRACING_V2、LANGCHAIN_API_KEY、LANGCHAIN_PROJECT

        8. **ファイルアップロード設定**:
           - MAX_UPLOAD_SIZE

    バリデーション:
        __init__メソッドで以下をチェック:
        - 本番環境でのSECRET_KEY必須化
        - 本番環境でのALLOWED_ORIGINS必須化
        - 開発環境でもデフォルトSECRET_KEY使用時は警告

    使用例:
        >>> from app.core.config import settings
        >>>
        >>> # 基本設定
        >>> print(settings.APP_NAME)
        "camp-backend"
        >>>
        >>> # データベース接続
        >>> print(settings.DATABASE_URL)
        "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"
        >>>
        >>> # LLM設定
        >>> print(settings.LLM_PROVIDER)
        "anthropic"
        >>> print(settings.LLM_MODEL)
        "claude-3-5-sonnet-20241022"

    Note:
        - 設定値は環境変数 > .env.{environment} > .env > デフォルト値 の順で優先されます
        - 本番環境では必ずSECRET_KEYとALLOWED_ORIGINSを設定してください
        - settings オブジェクトはモジュールレベルでインスタンス化されています
    """

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # アプリケーション設定
    APP_NAME: str = "camp-backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] | None = None

    # 環境設定
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # セキュリティ設定
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-must-be-32-chars-minimum",
        min_length=32,
        description="Must be set in production. Generate with: openssl rand -hex 32",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # レート制限設定
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # 秒単位

    # セキュリティポリシー設定
    MAX_LOGIN_ATTEMPTS: int = Field(
        default=5,
        description="アカウントロックまでのログイン失敗回数",
    )
    ACCOUNT_LOCK_DURATION_HOURS: int = Field(
        default=1,
        description="アカウントロック時間（時間）",
    )

    # データベース設定（PostgreSQL）
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"

    # テストデータベース設定（PostgreSQL）
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
    TEST_DATABASE_ADMIN_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    TEST_DATABASE_NAME: str = "test_db"

    # データベース接続プール設定
    DB_POOL_SIZE: int = Field(
        default=5,
        description="通常時の接続プールサイズ",
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        description="ピーク時の追加接続数",
    )
    DB_POOL_RECYCLE: int = Field(
        default=1800,
        description="接続リサイクル時間（秒）",
    )
    DB_POOL_PRE_PING: bool = Field(
        default=True,
        description="接続前のPINGチェック",
    )

    # Redisキャッシュ設定
    REDIS_URL: str | None = None  # 例: "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # デフォルトキャッシュTTL（秒）

    # ストレージ設定
    STORAGE_BACKEND: Literal["local", "azure"] = "local"
    LOCAL_STORAGE_PATH: str = "./uploads"
    AZURE_STORAGE_ACCOUNT_NAME: str | None = None
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_CONTAINER_NAME: str = "uploads"

    # LLM設定
    LLM_PROVIDER: Literal["anthropic", "openai", "azure_openai"] = "anthropic"
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4096

    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str | None = None

    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "camp-backend"

    # ファイルアップロード設定
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MBデフォルト

    # ================================================================================
    # Azure AD認証設定
    # ================================================================================

    # 認証モード切り替え
    AUTH_MODE: Literal["development", "production"] = Field(
        default="development",
        description="Authentication mode: development (JWT) or production (Azure AD)",
    )

    # Azure AD設定（本番モード用）
    AZURE_TENANT_ID: str | None = Field(
        default=None,
        description="Azure AD Tenant ID",
    )
    AZURE_CLIENT_ID: str | None = Field(
        default=None,
        description="Azure AD Application (client) ID for backend",
    )
    AZURE_CLIENT_SECRET: str | None = Field(
        default=None,
        description="Azure AD Client Secret (optional for token validation)",
    )
    AZURE_OPENAPI_CLIENT_ID: str | None = Field(
        default=None,
        description="Azure AD Application (client) ID for Swagger UI",
    )

    # 開発モード設定
    DEV_MOCK_TOKEN: str = Field(
        default="mock-access-token-dev-12345",
        description="Development mode mock token",
    )
    DEV_MOCK_USER_EMAIL: str = Field(
        default="dev.user@example.com",
        description="Development mode mock user email",
    )
    DEV_MOCK_USER_OID: str = Field(
        default="dev-azure-oid-12345",
        description="Development mode mock Azure Object ID",
    )
    DEV_MOCK_USER_NAME: str = Field(
        default="Development User",
        description="Development mode mock user name",
    )

    @model_validator(mode='after')
    def validate_dev_auth_not_in_production(self) -> 'Settings':
        """本番環境で開発モード認証が有効な場合にエラーを発生させます。

        セキュリティリスクを防ぐため、本番環境（ENVIRONMENT=production）で
        開発モード認証（AUTH_MODE=development）が有効な場合にエラーを発生させます。

        Raises:
            ValueError: 本番環境で開発モード認証が有効な場合

        Returns:
            Settings: バリデーション済み設定オブジェクト

        Note:
            - ENVIRONMENT="production" かつ AUTH_MODE="development" の組み合わせは禁止
            - 他の環境（development, staging）では開発モード認証を許可
        """
        if self.ENVIRONMENT == "production" and self.AUTH_MODE == "development":
            raise ValueError(
                "Development authentication cannot be enabled in production environment. "
                "Set AUTH_MODE=production for production."
            )
        return self

    def __init__(self, **kwargs):
        """設定を初期化し、環境に応じたバリデーションを実行します。

        Pydantic BaseSettingsの__init__を呼び出した後、以下のカスタムバリデーションを実行:
            1. ALLOWED_ORIGINS の自動設定と検証
            2. SECRET_KEY の本番環境での必須化と検証
            3. 開発環境でのデフォルトSECRET_KEY使用時の警告

        バリデーションルール:
            **ALLOWED_ORIGINS**:
                - 本番環境: 明示的な設定が必須（ValueError）
                - ステージング環境: デフォルトで["https://staging.example.com"]
                - 開発環境: デフォルトで["http://localhost:3000", "http://localhost:5173"]

            **SECRET_KEY**:
                - 本番環境: 必須、かつ "dev-secret-key" を含まないこと（ValueError）
                - 開発環境: デフォルトキー使用時は警告ログを出力

        Args:
            **kwargs: 環境変数または.envファイルから読み込まれた設定値
                - Pydantic BaseSettingsが自動的に処理します

        Raises:
            ValueError: 以下のいずれかの場合
                - 本番環境でALLOWED_ORIGINSが未設定
                - 本番環境でSECRET_KEYが未設定またはデフォルト値

        Example:
            >>> # 本番環境でSECRET_KEY未設定の場合
            >>> os.environ["ENVIRONMENT"] = "production"
            >>> settings = Settings()
            ValueError: SECRET_KEY must be set in production environment.
            Generate one with: openssl rand -hex 32
            >>>
            >>> # 正しい設定
            >>> os.environ["SECRET_KEY"] = "a" * 32
            >>> os.environ["ALLOWED_ORIGINS"] = '["https://example.com"]'
            >>> settings = Settings()
            >>> # 正常に初期化される

        Note:
            - このメソッドは Settings() インスタンス化時に自動実行されます
            - SECRET_KEY生成方法: `openssl rand -hex 32` をターミナルで実行
        """
        super().__init__(**kwargs)

        self._validate_cors_settings()
        self._validate_security_settings()
        self._validate_llm_config()
        self._validate_database_config()
        self._validate_storage_config()
        self._validate_azure_ad_config()

    def _validate_cors_settings(self) -> None:
        """CORS設定のバリデーション。

        環境に応じたALLOWED_ORIGINSの設定と検証を行います。

        Raises:
            ValueError: 本番環境でALLOWED_ORIGINSが未設定、またはワイルドカードが含まれる場合
        """
        # ALLOWED_ORIGINSを環境に応じて設定
        if self.ALLOWED_ORIGINS is None:
            if self.ENVIRONMENT == "production":
                raise ValueError("本番環境ではALLOWED_ORIGINSを明示的に設定する必要があります")
            elif self.ENVIRONMENT == "staging":
                self.ALLOWED_ORIGINS = ["https://staging.example.com"]
            else:
                # 開発環境のみワイルドカードまたはlocalhostを許可
                self.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

        # 本番環境でのCORS設定厳格化（ALLOWED_ORIGINSがNoneでない場合のみチェック）
        if self.ENVIRONMENT == "production" and self.ALLOWED_ORIGINS is not None:
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError("本番環境ではワイルドカードCORS (*)は許可されていません")

    def _validate_security_settings(self) -> None:
        """セキュリティ設定のバリデーション。

        SECRET_KEYの検証を行います。

        Raises:
            ValueError: 本番環境でSECRET_KEYが未設定またはデフォルト値の場合
        """
        # 本番環境でのSECRET_KEYチェック
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or "dev-secret-key" in self.SECRET_KEY:
                raise ValueError("本番環境ではSECRET_KEYを設定する必要があります。生成方法: openssl rand -hex 32")

        # 開発環境でも警告
        if self.ENVIRONMENT == "development" and "dev-secret-key" in self.SECRET_KEY:
            logger.warning("Using default SECRET_KEY. Set a custom key for better security even in development.")

    def _validate_llm_config(self) -> None:
        """LLM設定のバリデーション。

        本番環境でLLMプロバイダーに応じたAPIキーの存在を検証します。

        Raises:
            ValueError: 本番環境で必要なAPIキーが未設定の場合
        """
        if self.ENVIRONMENT != "production":
            return

        # LLM API キーの検証
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError("LLM_PROVIDER=anthropicの場合、ANTHROPIC_API_KEYが必要です")
        elif self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("LLM_PROVIDER=openaiの場合、OPENAI_API_KEYが必要です")
        elif self.LLM_PROVIDER == "azure_openai":
            if not self.AZURE_OPENAI_ENDPOINT or not self.AZURE_OPENAI_API_KEY:
                raise ValueError("LLM_PROVIDER=azure_openaiの場合、AZURE_OPENAI_ENDPOINTとAZURE_OPENAI_API_KEYが必要です")

    def _validate_database_config(self) -> None:
        """データベース設定のバリデーション。

        本番環境でデータベースURLの形式と設定を検証します。

        Raises:
            ValueError: 本番環境でDATABASE_URLが不正な形式の場合
        """
        if self.ENVIRONMENT != "production":
            return

        # データベースURL の検証
        if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URLはasyncpgドライバーを使用する必要があります (postgresql+asyncpg://)")

        if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
            logger.warning("本番環境でlocalhostのデータベースURLを使用しています - 意図的ですか？")

    def _validate_storage_config(self) -> None:
        """ストレージ設定のバリデーション。

        本番環境でAzure Storageを使用する場合に必要な設定を検証します。

        Raises:
            ValueError: 本番環境でAzure Storage使用時に必要な設定が未設定の場合
        """
        if self.ENVIRONMENT != "production":
            return

        # Azure Storage の検証
        if self.STORAGE_BACKEND == "azure":
            if not self.AZURE_STORAGE_ACCOUNT_NAME:
                raise ValueError("STORAGE_BACKEND=azureの場合、AZURE_STORAGE_ACCOUNT_NAMEが必要です")
            if not self.AZURE_STORAGE_CONNECTION_STRING:
                raise ValueError("STORAGE_BACKEND=azureの場合、AZURE_STORAGE_CONNECTION_STRINGが必要です")

    def _validate_azure_ad_config(self) -> None:
        """Azure AD設定のバリデーション。

        本番モード認証時にAzure AD設定が存在することを検証します。

        Raises:
            ValueError: 本番モード認証時にAzure AD設定が未設定の場合
        """
        # Azure AD設定の検証（本番モードのみ）
        if self.AUTH_MODE == "production":
            if not self.AZURE_TENANT_ID:
                raise ValueError("AUTH_MODE=productionの場合、AZURE_TENANT_IDが必要です")
            if not self.AZURE_CLIENT_ID:
                raise ValueError("AUTH_MODE=productionの場合、AZURE_CLIENT_IDが必要です")

            logger.info("✅ Azure AD認証が有効化されました（本番モード）")
        else:
            logger.info("⚠️  開発モード認証が有効化されました（モック認証）")


settings = Settings()
