# コードリーディングガイド

このガイドは、AI Agent Appプロジェクトに新規参加したメンバーが効率的にコードベースを理解できるよう、推奨される読み方と重要なポイントをまとめたものです。

## このガイドの目的

- プロジェクトの全体像を素早く把握する
- 重要なコンポーネントと実装パターンを理解する
- コードを読む順序と注目すべきポイントを提示する
- 実装の詳細な解説を提供する

## コードリーディングの推奨順序

### ステップ1: プロジェクト概要の把握

まず、プロジェクトの全体像を理解しましょう。

1. **README.md** - プロジェクト概要と主要機能
   - 位置: `C:\developments\genai-app-docs\README.md`
   - 内容: プロジェクトの目的、技術スタック、クイックスタート

2. **pyproject.toml** - 依存関係とプロジェクト設定
   - 位置: `C:\developments\genai-app-docs\pyproject.toml`
   - 内容: Python依存関係、ツール設定、メタデータ

3. **ドキュメント目次**
   - 位置: `docs/README.md`
   - 内容: 全ドキュメントの一覧と構成

### ステップ2: 設定とエントリーポイント

次に、アプリケーションがどのように起動し、設定されるかを理解します。

1. **config.py** - アプリケーション設定
   - 位置: `src/app/config.py`
   - 重要ポイント:
     - 環境変数の読み込み（.env.local, .env.staging, .env.production）
     - データベース設定（DATABASE_URL）
     - LLMプロバイダー設定（Anthropic, OpenAI, Azure）
     - セキュリティ設定（SECRET_KEY, JWT）
     - Redis、ストレージバックエンド設定

2. **main.py** - エントリーポイント
   - 位置: `src/app/main.py`
   - 重要ポイント:
     - ロギングのセットアップ
     - `create_app()`ファクトリーの呼び出し
     - CLI起動用の`main()`関数

3. **core/app_factory.py** - アプリケーションファクトリー
   - 位置: `src/app/core/app_factory.py`
   - 重要ポイント:
     - FastAPIアプリケーションの初期化
     - ミドルウェアの登録順序（重要！）
     - ルーターの統合（v1エンドポイント vs システムエンドポイント）
     - 例外ハンドラーの登録

4. **core/lifespan.py** - ライフサイクル管理
   - 位置: `src/app/core/lifespan.py`
   - 重要ポイント:
     - 起動時処理（DB初期化、Redis接続）
     - 終了時処理（gracefulシャットダウン）

### ステップ3: データベース設計

データモデルを理解することで、アプリケーションが扱うデータ構造が明確になります。

1. **database.py** - データベース接続設定
   - 位置: `src/app/database.py`
   - 重要ポイント:
     - 非同期エンジン設定（asyncpg）
     - コネクションプール設定
     - セッションファクトリー

2. **models/** - データベースモデル
   - 推奨読み順:
     1. `models/sample_user.py` - ユーザーモデル
     2. `models/sample_session.py` - セッションとメッセージモデル
     3. `models/sample_file.py` - ファイルメタデータモデル
   - 重要ポイント:
     - SQLAlchemy 2.0の新しい型ヒント構文（Mapped）
     - リレーションシップの定義（one-to-many, many-to-one）
     - タイムスタンプ管理（created_at, updated_at）
     - インデックスとユニーク制約

### ステップ4: API層の理解

APIエンドポイントから実装を読むことで、ユーザーインターフェースが理解できます。

1. **api/routes/v1/** - ビジネスロジックAPI
   - 推奨読み順:
     1. `agents.py` - AIエージェント機能
        - チャットエンドポイント
        - セッション管理
     2. `files.py` - ファイル管理
        - アップロード/ダウンロード/削除
        - ファイル一覧取得
     3. `users.py` - ユーザー管理
        - 登録、ログイン、プロフィール管理

2. **api/routes/system/** - システムエンドポイント
   - `health.py` - ヘルスチェック（DB、Redis接続確認）
   - `metrics.py` - Prometheusメトリクス
   - `root.py` - ルートエンドポイント

3. **api/dependencies.py** - 依存性注入
   - 重要ポイント:
     - `DatabaseDep` - データベースセッション
     - サービス依存性（`SampleUserServiceDep`, `AgentServiceDep`, `SampleFileServiceDep`）
     - 認証依存性（`CurrentSampleUserDep`, `CurrentUserOptionalDep`）

### ステップ5: サービス層のビジネスロジック

サービス層は、ビジネスロジックの中核です。

1. **services/** - ビジネスロジック層
   - 推奨読み順:
     1. `services/agent.py` - エージェントサービス
        - 現在: エコーバック機能
        - 将来: LangChain/LangGraph統合
     2. `services/file.py` - ファイルサービス
        - ファイルアップロード/ダウンロード/削除
        - MIME型バリデーション
        - サイズ制限チェック
     3. `services/user.py` - ユーザーサービス
        - ユーザー作成、認証
        - パスワードハッシュ化

### ステップ6: リポジトリ層のデータアクセス

リポジトリパターンは、データアクセスを抽象化します。

1. **repositories/base.py** - ベースリポジトリ
   - 重要ポイント:
     - ジェネリック型を使用した共通CRUD操作
     - `flush()`のみ実行、`commit()`は呼び出し側の責任
     - 型安全なクエリ実装

2. **repositories/** - 各リポジトリ
   - `user.py` - ユーザーリポジトリ
   - `session.py` - セッションリポジトリ
   - `file.py` - ファイルリポジトリ

### ステップ7: コア機能とユーティリティ

横断的な機能を理解します。

1. **core/security/** - セキュリティ機能
   - 重要ポイント:
     - パスワードハッシュ化（SHA-256 + bcrypt）（password.py）
     - JWT生成と検証（jwt.py）
     - APIキー生成と検証（api_key.py）
     - パスワード強度検証（password.py）

2. **core/exceptions.py** - カスタム例外
   - `AppException` - 基底例外
   - `NotFoundError`, `ValidationError`, `AuthenticationError`等

3. **core/cache.py** - Redisキャッシュマネージャー
   - キャッシュの取得、保存、削除
   - TTL管理

4. **api/middlewares/** - ミドルウェア
   - `error_handler.py` - エラーハンドリング
   - `logging.py` - リクエスト/レスポンスロギング
   - `rate_limit.py` - レート制限
   - `metrics.py` - Prometheusメトリクス収集
   - `security_headers.py` - セキュリティヘッダー

## 主要コンポーネントの詳細解説

### 1. アプリケーション起動フロー

```text
main.py
  ├─ setup_logging()           # ロギング初期化
  └─ create_app()              # core/app_factory.py
      ├─ FastAPI初期化
      ├─ lifespan設定          # core/lifespan.py
      │   ├─ 起動時: init_db(), Redis接続
      │   └─ 終了時: Redis切断, DB接続クローズ
      ├─ ミドルウェア登録（実行順序は逆順）
      │   ├─ SecurityHeadersMiddleware
      │   ├─ CORSMiddleware
      │   ├─ RateLimitMiddleware
      │   ├─ LoggingMiddleware
      │   ├─ ErrorHandlerMiddleware
      │   └─ PrometheusMetricsMiddleware
      ├─ ルーター登録
      │   ├─ /api/v1/agents
      │   ├─ /api/v1/files
      │   ├─ /api/v1/sample-users
      │   ├─ / (root)
      │   ├─ /health
      │   └─ /metrics
      └─ 例外ハンドラー登録
```

### 2. リクエスト処理フロー（例: チャット）

```text
1. クライアント
   ↓ POST /api/v1/agents/chat
2. ミドルウェア（順次実行）
   ↓
3. API Layer (api/routes/v1/agents.py)
   - リクエストバリデーション（ChatRequest）
   - 依存性注入（AgentServiceDep）
   ↓
4. Service Layer (services/agent.py)
   - セッション取得/作成
   - メッセージ保存
   - AIレスポンス生成（現在: エコーバック）
   - アシスタントメッセージ保存
   ↓
5. Repository Layer (repositories/sample_session.py)
   - データベースクエリ（SELECT, INSERT）
   ↓
6. Model Layer (models/sample_session.py, models/sample_message.py)
   - SQLAlchemyモデル
   ↓
7. Database (PostgreSQL)
```

### 3. トランザクション管理パターン

```python
# repositories/base.py - flush()のみ
async def create(self, **obj_in):
    db_obj = self.model(**obj_in)
    self.db.add(db_obj)
    await self.db.flush()  # ID生成を待つ
    await self.db.refresh(db_obj)
    return db_obj  # commit()は呼ばない

# services/file.py - commit()を明示的に呼ぶ
async def upload_file(self, file, user_id):
    # バリデーション
    # ファイルI/O
    # リポジトリ操作（flush自動）
    await self.db.commit()  # ここでコミット
```

### 4. セキュリティ実装の詳細

#### パスワードハッシュ化

```python
# core/security/password.py
def hash_password(password: str) -> str:
    # SHA-256でプリハッシュ（bcryptの72バイト制限対策）
    prehashed = hashlib.sha256(password.encode()).hexdigest()
    # bcryptでハッシュ化（コスト: 12ラウンド）
    return pwd_context.hash(prehashed)
```

#### JWT認証

```python
# core/security/jwt.py
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

### 5. ファイルアップロードのセキュリティ

```python
# services/file.py
ALLOWED_MIME_TYPES = {
    "text/plain", "text/csv", "application/pdf", "application/json",
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def upload_file(self, file: UploadFile, user_id: int | None):
    # 1. MIME型チェック
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"File type {file.content_type} not allowed")

    # 2. サイズチェック
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds {MAX_FILE_SIZE} bytes")

    # 3. ファイル名サニタイズ
    safe_filename = sanitize_filename(file.filename)
```

## 依存性注入パターン

FastAPIの依存性注入システムを活用しています。

### 基本パターン

```python
# api/dependencies.py
from typing import Annotated
from fastapi import Depends

# データベースセッション
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]

# サービス層
def get_agent_service(db: DatabaseDep) -> AgentService:
    return AgentService(db)

AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]

# 認証
def get_current_user(token: str = Depends(oauth2_scheme), db: DatabaseDep) -> SampleUser:
    # トークン検証
    # ユーザー取得
    return user

CurrentSampleUserDep = Annotated[User, Depends(get_current_user)]
```

### エンドポイントでの使用

```python
# api/routes/v1/agents.py
@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: AgentServiceDep,           # サービス注入
    current_user: CurrentUserOptionalDep = None  # 認証オプショナル
):
    return await service.chat(
        message=request.message,
        session_id=request.session_id,
        user_id=current_user.id if current_user else None
    )
```

## 実装パターンのベストプラクティス

### 1. エンドポイント実装パターン

```python
@router.post("/resource", response_model=ResourceResponse)
async def create_resource(
    request: ResourceCreate,      # リクエストバリデーション
    service: ResourceServiceDep,  # サービス注入
    current_user: CurrentSampleUserDep  # 認証
) -> ResourceResponse:
    try:
        result = await service.create(request, current_user.id)
        return ResourceResponse.model_validate(result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 2. サービス層実装パターン

```python
class ResourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResourceRepository(db)

    async def create(self, data: ResourceCreate, user_id: int):
        # 1. バリデーション
        # 2. ビジネスロジック
        # 3. リポジトリ操作
        resource = await self.repo.create(**data.model_dump(), user_id=user_id)
        # 4. コミット
        await self.db.commit()
        return resource
```

### 3. リポジトリ実装パターン

```python
class ResourceRepository(BaseRepository[Resource]):
    def __init__(self, db: AsyncSession):
        super().__init__(Resource, db)

    async def get_by_custom_field(self, field_value: str):
        query = select(Resource).where(Resource.field == field_value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

## 主要な設定ファイル

### pyproject.toml

主要な依存関係:

- **Web**: fastapi, uvicorn
- **AI**: langchain, langgraph, langchain-anthropic, langchain-openai
- **Database**: sqlalchemy, asyncpg, alembic
- **Security**: passlib, python-jose, bcrypt
- **Cache/Monitoring**: redis, prometheus-client

### .env ファイル（環境別）

環境別設定ファイル:

- `.env.local` - 開発環境
- `.env.staging` - ステージング環境
- `.env.production` - 本番環境

読み込み優先順位:

1. 環境変数（最優先）
2. `.env.{ENVIRONMENT}`
3. `.env`（共通）
4. デフォルト値

## 次に読むべきドキュメント

コードリーディングを進めながら、以下のドキュメントを参照してください:

1. **アーキテクチャ理解**
   - [プロジェクト構造](../02-architecture/01-project-structure.md)
   - [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md)
   - [依存性注入](../02-architecture/03-dependency-injection.md)

2. **技術詳細**
   - [技術スタック](../03-core-concepts/01-tech-stack/index.md)
   - [データベース設計](../03-core-concepts/02-database-design/index.md)
   - [セキュリティ実装](../03-core-concepts/03-security/index.md)

3. **開発ガイド**
   - [コーディング規約](../04-development/01-coding-standards/)
   - [レイヤー別実装ガイド](../04-development/02-layer-implementation/)
   - [テスト戦略](../05-testing/01-testing-strategy/index.md)

## よくある質問

### Q1: どのファイルから読み始めるべきですか？

**A**: 以下の順序がおすすめです:

1. `src/app/config.py` - 設定を理解する
2. `src/app/main.py` - エントリーポイント
3. `src/app/core/app_factory.py` - アプリケーション構造
4. `src/app/api/routes/v1/agents.py` - 具体的な機能実装

### Q2: ビジネスロジックはどこにありますか？

**A**: `src/app/services/` ディレクトリにあります。各サービスクラスがビジネスロジックを実装しています。

### Q3: データベーススキーマはどこで定義されていますか？

**A**: `src/app/models/` ディレクトリにSQLAlchemyモデルとして定義されています。

### Q4: AI機能の実装はどこですか？

**A**: 現在、`src/app/services/sample_agent.py` にシンプルなエコーバック機能があります。将来的にLangChain/LangGraphを統合予定です。

### Q5: テストコードはどこにありますか？

**A**: `tests/` ディレクトリに、レイヤーごとのテストがあります:

- `test_models.py` - モデル層
- `test_repositories.py` - リポジトリ層
- `test_services.py` - サービス層
- `test_api.py` - API層

## まとめ

このガイドに沿ってコードを読み進めることで、AI Agent Appの全体像と実装の詳細を効率的に理解できます。

重要なポイント:

1. **レイヤードアーキテクチャ** - API → Service → Repository → Model
2. **依存性注入** - FastAPIのDIシステムを活用
3. **トランザクション管理** - Repository層で`flush()`、Service層で`commit()`
4. **セキュリティ** - bcrypt、JWT、ファイルバリデーション
5. **非同期処理** - asyncpgとasync/awaitパターン

不明点があれば、各ドキュメントを参照するか、チームメンバーに質問してください。
