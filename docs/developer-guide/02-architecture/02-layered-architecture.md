# レイヤードアーキテクチャ

このドキュメントでは、camp-backendが採用しているエンタープライズレイヤードアーキテクチャについて説明します。

## アーキテクチャ概要

このプロジェクトは、関心の分離（Separation of Concerns）の原則に基づき、4つの主要なレイヤーで構成されています。

### リクエストフロー（クライアント → データベース）

::: mermaid
graph LR
    A[HTTPリクエスト] --> B[API Layer]
    B --> C[Service Layer]
    C --> D[Repository Layer]
    D --> E[Model Layer]
    E --> F[(PostgreSQL<br/>Database)]

    style A fill:#81d4fa,stroke:#01579b,stroke-width:3px,color:#000
    style B fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000
    style C fill:#ce93d8,stroke:#4a148c,stroke-width:3px,color:#000
    style D fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000
    style E fill:#f48fb1,stroke:#880e4f,stroke-width:3px,color:#000
    style F fill:#757575,stroke:#212121,stroke-width:3px,color:#fff
:::

### レスポンスフロー（データベース → クライアント）

::: mermaid
graph LR
    F[(PostgreSQL<br/>Database)] --> E[Model Layer]
    E --> D[Repository Layer]
    D --> C[Service Layer]
    C --> B[API Layer]
    B --> A[HTTPレスポンス]

    style F fill:#757575,stroke:#212121,stroke-width:3px,color:#fff
    style E fill:#f48fb1,stroke:#880e4f,stroke-width:3px,color:#000
    style D fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000
    style C fill:#ce93d8,stroke:#4a148c,stroke-width:3px,color:#000
    style B fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000
    style A fill:#81d4fa,stroke:#01579b,stroke-width:3px,color:#000
:::

### レイヤーの役割

各レイヤーの責務を詳細に図示します。

::: mermaid
graph TB
    subgraph "API Layer api/"
        direction TB
        API_Main[HTTPリクエスト/レスポンス]
        API_1[Routes: エンドポイント定義]
        API_2[Dependencies: 依存性注入]
        API_3[Middlewares: 横断的関心事]
        API_4[Validation: Pydanticスキーマ]
    end

    subgraph "Service Layer services/"
        direction TB
        Service_Main[ビジネスロジック]
        Service_1[ビジネスルールの実装]
        Service_2[トランザクション管理]
        Service_3[複数リポジトリの調整]
        Service_4[データ変換とバリデーション]
    end

    subgraph "Repository Layer repositories/"
        direction TB
        Repo_Main[データアクセス]
        Repo_1[データベースクエリ]
        Repo_2[CRUD操作]
        Repo_3[データアクセスの抽象化]
        Repo_4[クエリの最適化]
    end

    subgraph "Model Layer models/"
        direction TB
        Model_Main[データ定義]
        Model_1[SQLAlchemyモデル]
        Model_2[テーブル定義]
        Model_3[リレーションシップ]
        Model_4[制約とインデックス]
    end

    API_Main --> Service_Main
    Service_Main --> Repo_Main
    Repo_Main --> Model_Main

    style API_Main fill:#81d4fa,stroke:#01579b,stroke-width:3px,color:#000
    style Service_Main fill:#ce93d8,stroke:#4a148c,stroke-width:3px,color:#000
    style Repo_Main fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000
    style Model_Main fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000

    style API_1 fill:#b3e5fc,stroke:#0277bd,stroke-width:2px,color:#000
    style API_2 fill:#b3e5fc,stroke:#0277bd,stroke-width:2px,color:#000
    style API_3 fill:#b3e5fc,stroke:#0277bd,stroke-width:2px,color:#000
    style API_4 fill:#b3e5fc,stroke:#0277bd,stroke-width:2px,color:#000

    style Service_1 fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px,color:#000
    style Service_2 fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px,color:#000
    style Service_3 fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px,color:#000
    style Service_4 fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px,color:#000

    style Repo_1 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000
    style Repo_2 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000
    style Repo_3 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000
    style Repo_4 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000

    style Model_1 fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,color:#000
    style Model_2 fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,color:#000
    style Model_3 fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,color:#000
    style Model_4 fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,color:#000
:::

**各レイヤーの詳細:**

| レイヤー | ディレクトリ | 主な責務 |
|---------|------------|---------|
| **API Layer** | `src/app/api/` | HTTPリクエストの受付、バリデーション、サービス層の呼び出し、レスポンス返却 |
| **Service Layer** | `src/app/services/` | ビジネスロジックの実装、トランザクション管理、複数リポジトリの調整 |
| **Repository Layer** | `src/app/repositories/` | データベースクエリの実装、CRUD操作、データアクセスの抽象化 |
| **Model Layer** | `src/app/models/` | データベーステーブルの定義、リレーションシップ、制約の定義 |

## データフロー

### リクエストフロー（API → Database）

```text
1. HTTPリクエスト
   ↓
2. API Layer (routes/)
   - リクエストの受信
   - バリデーション（Pydanticスキーマ）
   - 依存性の解決
   ↓
3. Service Layer (services/)
   - ビジネスロジックの実行
   - Repository層の呼び出し
   - トランザクション管理
   ↓
4. Repository Layer (repositories/)
   - SQLAlchemyクエリの構築
   - データベース操作
   ↓
5. Model Layer (models/)
   - データベーステーブル
   - ORM操作
   ↓
6. Database
```

### レスポンスフロー（Database → API）

```text
1. Database
   ↓
2. Model Layer
   - SQLAlchemyモデルインスタンス
   ↓
3. Repository Layer
   - モデルインスタンスの返却
   ↓
4. Service Layer
   - ビジネスロジックの適用
   - データ変換
   ↓
5. API Layer
   - Pydanticモデルへの変換
   - HTTPレスポンスの構築
   ↓
6. HTTPレスポンス（JSON）
```

## 実例: ユーザー作成のフロー

以下は、新しいユーザーを作成する際の各レイヤーの連携を示すシーケンス図です。

::: mermaid
sequenceDiagram
    participant Client
    participant API as API Layer<br/>(routes/users.py)
    participant Service as Service Layer<br/>(SampleUserService)
    participant Repo as Repository Layer<br/>(SampleUserRepository)
    participant DB as PostgreSQL

    Client->>API: POST /api/sample-users<br/>{email, username, password}

    Note over API: Pydanticバリデーション
    API->>API: UserCreate検証

    API->>Service: create_user(user_data)

    Note over Service: ビジネスルール適用
    Service->>Repo: get_by_email(email)
    Repo->>DB: SELECT * FROM sample_users<br/>WHERE email=?
    DB-->>Repo: NULL (存在しない)
    Repo-->>Service: None

    Service->>Repo: get_by_username(username)
    Repo->>DB: SELECT * FROM sample_users<br/>WHERE username=?
    DB-->>Repo: NULL (存在しない)
    Repo-->>Service: None

    Service->>Service: hash_password()

    Service->>Repo: create(user_data)
    Repo->>DB: INSERT INTO sample_users
    DB-->>Repo: SampleUser(id=1)
    Repo-->>Service: SampleUser

    Service-->>API: SampleUser

    Note over API: レスポンス変換
    API->>API: SampleUserResponse.model_validate()

    API-->>Client: 201 Created<br/>SampleUserResponse
:::

この図から、各レイヤーが明確に分離され、それぞれの責務を果たしていることが分かります。

## 各レイヤーの詳細

### 1. API Layer（API層）

**場所**: `src/app/api/`

**責務**:

- HTTPリクエストの受け取り
- リクエストデータのバリデーション
- 認証・認可の確認
- サービス層の呼び出し
- HTTPレスポンスの返却
- エラーハンドリング

**実装例**:

```python
# src/app/api/routes/sample_users.py
from fastapi import APIRouter, status
from app.api.core import SampleUserServiceDep, CurrentSampleUserDep
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SampleUserResponse)
async def create_user(
    user_data: SampleUserCreate,                    # リクエストバリデーション
    service: SampleUserServiceDep,                  # 依存性注入
) -> SampleUserResponse:
    """新しいユーザーを作成します。"""
    # サービス層を呼び出し
    user = await service.create_user(user_data)

    # レスポンスを返却
    return SampleUserResponse.model_validate(sample_user)

@router.get("/me", response_model=SampleUserResponse)
async def get_current_user(
    current_user: CurrentSampleUserDep,             # 認証済みユーザー
) -> SampleUserResponse:
    """現在のユーザー情報を取得します。"""
    return SampleUserResponse.model_validate(current_user)
```

**禁止事項**:

- データベースへの直接アクセス
- ビジネスロジックの実装
- 他のAPI層への直接依存

### 2. Service Layer（サービス層）

**場所**: `src/app/services/`

**責務**:

- ビジネスロジックの実装
- ドメインルールの適用
- トランザクション管理
- 複数リポジトリの調整
- データ変換とバリデーション

**実装例（Facadeパターン）**:

サービス層はFacadeパターンで実装され、機能別にサブサービスに分割されています。

```python
# src/app/services/project/project/__init__.py（Facadeクラス）
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.project.project.crud import ProjectCrudService


class ProjectService:
    """プロジェクト管理のビジネスロジックを提供するサービスクラス。

    各機能は専用のサービスクラスに委譲されます（Facadeパターン）。
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._crud_service = ProjectCrudService(db)

    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        """新しいプロジェクトを作成します。"""
        return await self._crud_service.create_project(project_data, creator_id)

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """プロジェクトIDでプロジェクト情報を取得します。"""
        return await self._crud_service.get_project(project_id)
```

```python
# src/app/services/project/project/crud.py（サブサービス）
import uuid
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Project, ProjectRole
from app.services.project.project.base import ProjectBaseService


class ProjectCrudService(ProjectBaseService):
    """プロジェクトのCRUD操作を提供するサービス。"""

    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        """新しいプロジェクトを作成します。"""
        # ビジネスルール: プロジェクトコードの重複チェック
        existing = await self.project_repo.get_by_code(project_data.code)
        if existing:
            raise ValidationError(
                "プロジェクトコードが既に使用されています",
                details={"code": project_data.code}
            )

        # プロジェクト作成
        project = await self.project_repo.create(
            name=project_data.name,
            code=project_data.code,
            description=project_data.description,
            created_by=creator_id,
        )

        # 作成者をOWNERとして追加
        await self.member_repo.create(
            project_id=project.id,
            user_id=creator_id,
            role=ProjectRole.OWNER,
        )

        await self.db.commit()
        return project
```

**禁止事項**:

- HTTPリクエスト/レスポンスの直接処理
- データベースクエリの直接実行（リポジトリを使用）
- グローバル状態への依存

### 3. Repository Layer（リポジトリ層）

**場所**: `src/app/repositories/`

**責務**:

- データベースクエリの実装
- CRUD操作
- データアクセスの抽象化
- クエリの最適化

**実装例**:

```python
# src/app/repositories/base.py
from typing import Generic, TypeVar, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """全リポジトリの基底クラス。共通CRUD操作を提供。"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        """IDでレコードを取得。"""
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """複数のレコードを取得（フィルタリング可能）。"""
        query = select(self.model)

        # フィルタの適用
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **obj_in: Any) -> ModelType:
        """新しいレコードを作成。"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, **update_data: Any) -> ModelType:
        """既存のレコードを更新。"""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        """レコードを削除。"""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False
```

```python
# src/app/repositories/sample_user.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.sample_user import SampleUser

class SampleUserRepository(BaseRepository[SampleUser]):
    """ユーザー専用のリポジトリ。"""

    def __init__(self, db: AsyncSession):
        super().__init__(SampleUser, db)

    async def get_by_email(self, email: str) -> SampleUser | None:
        """メールアドレスでユーザーを取得。"""
        query = select(SampleUser).where(SampleUser.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> SampleUser | None:
        """ユーザー名でユーザーを取得。"""
        query = select(SampleUser).where(SampleUser.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[SampleUser]:
        """アクティブなユーザーの一覧を取得。"""
        query = (
            select(SampleUser)
            .where(SampleUser.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

**禁止事項**:

- ビジネスロジックの実装
- 他のリポジトリへの依存
- HTTPレスポンスの直接作成

### 4. Model Layer（モデル層）

**場所**: `src/app/models/`

**責務**:

- データベーステーブルの定義
- カラムとデータ型の定義
- リレーションシップの定義
- 制約の定義

**実装例**:

```python
# src/app/models/sample_user.py
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SampleUser(Base):
    """ユーザーモデル。"""

    __tablename__ = "sample_users"

    # プライマリキー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 基本情報
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # フラグ
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # リレーションシップ
    sessions: Mapped[list["SampleSession"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    files: Mapped[list["SampleFile"]] = relationship(
        "File",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
```

**禁止事項**:

- ビジネスロジックの実装
- 外部サービスへの依存
- 複雑な計算処理

## 認証システムの構成

camp-backendは、2つの認証方式をサポートしています：

### 1. JWT認証（非推奨）

- **モデル**: `SampleUser` (sample/sample_user.py)
- **サービス**: `SampleUserService` (sample/sample_user.py)
- **認証方式**: JWTトークン（ローカル発行）
- **用途**: サンプル機能、開発初期段階
- **状態**: 非推奨（新機能では使用しないでください）

### 2. Azure AD認証（推奨）

- **モデル**: `UserAccount` (user_account/user_account.py)
- **サービス**: `UserService` (user_account/user_account.py)
- **認証方式**: Azure AD Bearer Token（本番）/ モックトークン（開発）
- **用途**: 本番環境、プロジェクト管理、分析機能
- **切り替え**: 環境変数 `AUTH_MODE` で制御

#### AUTH_MODEによる認証切り替え

```python
# 環境変数設定
AUTH_MODE=development  # 開発モード（モック認証）
AUTH_MODE=production   # 本番モード（Azure AD認証）

# 依存性注入での使用
from app.api.core import CurrentUserAzureDep

@router.get("/profile")
async def get_profile(current_user: CurrentUserAzureDep):
    # AUTH_MODEに応じて自動的に認証方式が切り替わります
    # - development: モックトークン検証
    # - production: Azure ADトークン検証
    return {"email": current_user.email}
```

#### 依存性注入の型アノテーション

```python
# JWT認証（非推奨）
UserServiceDep = Annotated[SampleUserService, Depends(get_user_service)]
CurrentUserDep = Annotated[SampleUser, Depends(get_current_active_user)]

# Azure AD認証（推奨）
AzureUserServiceDep = Annotated[UserService, Depends(get_azure_user_service)]
CurrentUserAzureDep = Annotated[UserAccount, Depends(get_current_active_user_azure)]
```

## 依存関係のルール

各レイヤーは、自分より下のレイヤーにのみ依存できます。

```text
API Layer
  ↓ 依存OK
Service Layer
  ↓ 依存OK
Repository Layer
  ↓ 依存OK
Model Layer
  ↑ 依存NG（上位レイヤーへの依存は禁止）
```

### 良い例

```python
# Service層はRepository層に依存
class SampleUserService:
    def __init__(self, db: AsyncSession):
        self.repository = SampleUserRepository(db)  # OK

# API層はService層に依存
@router.post("/users")
async def create_user(service: SampleUserServiceDep):  # OK
    return await service.create_user(...)
```

### 悪い例

```python
# API層がRepository層に直接依存（Service層をスキップ）
@router.post("/users")
async def create_user(db: DatabaseDep):
    repository = SampleUserRepository(db)  # NG: Service層を経由すべき
    return await repository.create(...)

# Model層がService層に依存
class SampleUser(Base):
    def send_email(self):
        # NG: モデルはビジネスロジックを持つべきでない
        email_service.send(...)
```

## トランザクション管理

トランザクションはService層で管理します。

```python
# src/app/services/project/project/crud.py
class ProjectCrudService(ProjectBaseService):
    async def create_project(
        self,
        project_data: ProjectCreate,
        creator_id: uuid.UUID,
    ) -> Project:
        """プロジェクトとメンバーを同時に作成（トランザクション）。"""
        # 複数のリポジトリ操作を1つのトランザクションで実行
        # プロジェクト作成
        project = await self.project_repo.create(
            name=project_data.name,
            code=project_data.code,
            description=project_data.description,
            created_by=creator_id,
        )

        # 作成者をOWNERとして追加
        await self.member_repo.create(
            project_id=project.id,
            user_id=creator_id,
            role=ProjectRole.OWNER,
        )

        # 明示的にコミット
        await self.db.commit()
        return project
```

データベースセッションの管理:

```python
# src/app/core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # 成功時は自動コミット
        except Exception:
            await session.rollback()  # エラー時は自動ロールバック
            raise
        finally:
            await session.close()
```

## エラーハンドリング

各レイヤーで適切な例外を発生させます。

```python
# core/exceptions.py - カスタム例外の定義
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details

class NotFoundError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)

class ValidationError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)
```

```python
# Service層 - ビジネスロジックエラーを発生
class SampleUserService:
    async def get_user(self, user_id: int) -> SampleUser:
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError(
                "User not found",
                details={"user_id": user_id}
            )
        return user
```

```python
# API層 - 例外をHTTPレスポンスに変換
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        },
    )
```

## まとめ

### レイヤードアーキテクチャの利点

1. **関心の分離**: 各レイヤーが明確な責務を持つ
2. **テストしやすさ**: レイヤーごとに独立したテストが可能
3. **保守性**: 変更の影響範囲が限定される
4. **再利用性**: サービス層のロジックを複数のAPIで使用可能
5. **拡張性**: 新機能の追加が容易

### ベストプラクティス

- 各レイヤーの責務を守る
- 上位レイヤーへの依存を避ける
- トランザクションはService層で管理
- 適切な例外処理を実装
- 依存性注入を活用

## 次のステップ

- [依存性注入](./03-dependency-injection.md) - FastAPIのDIパターン
- [データベース設計](../03-core-concepts/02-database-design.md) - モデル定義の詳細
- [テックスタック](../03-core-concepts/01-tech-stack.md) - 使用技術の詳細
