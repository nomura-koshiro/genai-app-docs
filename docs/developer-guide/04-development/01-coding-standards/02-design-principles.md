# 設計原則

高品質なバックエンドAPIを構築するための設計原則について説明します。

## 概要

本プロジェクトでは、以下の設計原則に基づいてアーキテクチャを構築しています：

- **SOLID原則**
- **Clean Architecture**
- **依存性逆転の原則**
- **レイヤードアーキテクチャ**

これらの原則により、テスタビリティ、保守性、拡張性の高いシステムを実現します。

---

## 1. SOLID原則

### S - Single Responsibility Principle（単一責任の原則）

各クラスは1つの責任のみを持ち、変更の理由は1つであるべきです。

#### 実装例

```python
# src/app/services/project/project/crud.py
class ProjectCrudService(ProjectBaseService):
    """プロジェクトのビジネスロジック専用サービス。"""

    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        """プロジェクト作成のビジネスロジックのみを担当。"""
        # バリデーション
        existing = await self.project_repo.get_by_code(project_data.code)
        if existing:
            raise ValidationError("プロジェクトコードが既に使用されています")

        # データ永続化（リポジトリに委譲）
        project = await self.project_repo.create(
            name=project_data.name,
            code=project_data.code,
            description=project_data.description,
            created_by=creator_id,
        )

        # メンバー追加（別リポジトリに委譲）
        await self.member_repo.create(
            project_id=project.id,
            user_id=creator_id,
            role=ProjectRole.OWNER,
        )

        await self.db.commit()
        return project


# src/app/repositories/project/project.py
class ProjectRepository(BaseRepository[Project]):
    """プロジェクトのデータアクセス専用リポジトリ。"""

    async def get_by_code(self, code: str) -> Project | None:
        """データアクセスロジックのみを担当。"""
        query = select(Project).where(Project.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

### O - Open/Closed Principle（開放/閉鎖原則）

拡張に対して開いており、修正に対して閉じているべきです。

#### 実装例：Storage抽象化

```python
# src/app/storage/base.py
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """ストレージの抽象基底クラス。新しいストレージを追加しても既存コードは変更不要。"""

    @abstractmethod
    async def upload(self, file_path: str, content: bytes) -> str:
        """ファイルをアップロード。"""
        pass

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """ファイルをダウンロード。"""
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """ファイルを削除。"""
        pass


# src/app/storage/local.py
class LocalStorage(StorageBackend):
    """ローカルファイルシステムストレージの実装。"""

    async def upload(self, file_path: str, content: bytes) -> str:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return file_path


# src/app/storage/azure_blob.py
class AzureBlobStorage(StorageBackend):
    """Azure Blob Storageの実装。既存コードを変更せずに追加可能。"""

    async def upload(self, file_path: str, content: bytes) -> str:
        blob_client = self.container_client.get_blob_client(file_path)
        await blob_client.upload_blob(content, overwrite=True)
        return file_path
```

### L - Liskov Substitution Principle（リスコフの置換原則）

基底クラスのインスタンスを派生クラスのインスタンスで置き換えても、プログラムの正しさは保たれるべきです。

#### 実装例

```python
# src/app/repositories/base.py
class BaseRepository(Generic[ModelType]):
    """ベースリポジトリ。すべての派生クラスは同じインターフェースを提供。"""

    async def get(self, id: int) -> ModelType | None:
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


# 派生クラスは基底クラスと同じ動作を保証
class ProjectRepository(BaseRepository[Project]):
    pass

class UserAccountRepository(BaseRepository[UserAccount]):
    pass


# どのリポジトリも同じように使用可能
async def get_entity(repo: BaseRepository[Any], entity_id: uuid.UUID):
    """どのリポジトリでも同じように動作する。"""
    return await repo.get(entity_id)
```

### I - Interface Segregation Principle（インターフェース分離原則）

クライアントは使用しないインターフェースに依存すべきではありません。

#### 実装例

```python
# 悪い例：1つの大きなインターフェース
class UserManager(ABC):
    @abstractmethod
    async def create_user(self, data: UserAccountCreate) -> UserAccount: pass

    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> UserAccount: pass

    @abstractmethod
    async def send_welcome_email(self, user: UserAccount) -> None: pass

    @abstractmethod
    async def generate_report(self, user_id: uuid.UUID) -> Report: pass


# 良い例：小さなインターフェースに分離
class UserCreator(ABC):
    @abstractmethod
    async def create_user(self, data: UserAccountCreate) -> UserAccount: pass


class UserAuthenticator(ABC):
    @abstractmethod
    async def authenticate(self, email: str, password: str) -> UserAccount: pass


class EmailSender(ABC):
    @abstractmethod
    async def send_welcome_email(self, user: UserAccount) -> None: pass


class ReportGenerator(ABC):
    @abstractmethod
    async def generate_report(self, user_id: uuid.UUID) -> Report: pass
```

### D - Dependency Inversion Principle（依存性逆転の原則）

高レベルモジュールは低レベルモジュールに依存すべきではありません。両方とも抽象に依存すべきです。

#### 実装例

```python
# src/app/api/dependencies.py
# 依存性注入を使用して抽象に依存

def get_project_service(db: DatabaseDep) -> ProjectService:
    """ProjectServiceを注入。具体的な実装は隠蔽。"""
    return ProjectService(db)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


# src/app/api/routes/v1/projects.py
@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectServiceDep,  # 抽象に依存、具体的な実装は知らない
    current_user: CurrentUserDep,
) -> ProjectResponse:
    """APIルートは具体的な実装ではなく、抽象（インターフェース）に依存。"""
    project = await project_service.create_project(project_data, current_user.id)
    return ProjectResponse.model_validate(project)
```

---

## 2. Clean Architecture

### アーキテクチャ構造

本プロジェクトは Clean Architecture の原則に従った層構造を採用しています：

```text
┌─────────────────────────────────────────┐
│         API Layer (routes/)              │  <- 外側の層（詳細）
│  - HTTPリクエスト/レスポンス処理         │
│  - ルーティング                           │
│  - バリデーション                         │
└─────────────────┬───────────────────────┘
                  │ 依存
┌─────────────────▼───────────────────────┐
│       Service Layer (services/)          │
│  - ビジネスロジック                       │
│  - トランザクション管理                   │
│  - オーケストレーション                   │
└─────────────────┬───────────────────────┘
                  │ 依存
┌─────────────────▼───────────────────────┐
│     Repository Layer (repositories/)     │
│  - データアクセス抽象化                   │
│  - クエリ構築                             │
│  - CRUD操作                               │
└─────────────────┬───────────────────────┘
                  │ 依存
┌─────────────────▼───────────────────────┐
│         Model Layer (models/)            │  <- 内側の層（核心）
│  - ドメインモデル                         │
│  - ビジネスルール                         │
│  - エンティティ定義                       │
└─────────────────────────────────────────┘
```

### 依存の方向

**重要**: 依存は常に外側から内側に向かいます。内側の層は外側の層を知りません。

```python
# ✅ 良い例：外側が内側に依存
# API Layer -> Service Layer
@router.post("/")
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectServiceDep,  # サービス層に依存
    current_user: CurrentUserDep,
):
    return await project_service.create_project(project_data, current_user.id)


# Service Layer -> Repository Layer（Facadeパターン）
# src/app/services/project/project/__init__.py
class ProjectService:
    def __init__(self, db: AsyncSession):
        self._crud_service = ProjectCrudService(db)  # サブサービスに委譲

    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        return await self._crud_service.create_project(project_data, creator_id)


# ❌ 悪い例：内側が外側に依存
class Project(Base):
    # モデルがAPIレスポンスを知っている（悪い）
    def to_api_response(self) -> ProjectResponse:
        pass
```

### 層ごとの責務

#### 1. Model Layer（最も内側）

```python
# src/app/models/project/project.py
from sqlalchemy.orm import Mapped, mapped_column

class Project(Base):
    """純粋なドメインモデル。ビジネスルールのみを持つ。"""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # リレーションシップ
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
```

**責務**:

- データ構造の定義
- ビジネスルール（バリデーションロジック等）
- エンティティ間の関係性

**依存してはいけないもの**:

- HTTPリクエスト/レスポンス
- データベース接続の詳細
- 外部サービス

#### 2. Repository Layer

```python
# src/app/repositories/project/project.py
class ProjectRepository(BaseRepository[Project]):
    """データアクセスの抽象化。"""

    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_by_code(self, code: str) -> Project | None:
        """プロジェクトコードでプロジェクトを検索。"""
        query = select(Project).where(Project.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_projects(self, user_id: uuid.UUID) -> list[Project]:
        """ユーザーが所属するプロジェクト一覧を取得。"""
        query = (
            select(Project)
            .join(ProjectMember)
            .where(ProjectMember.user_id == user_id)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

**責務**:

- データの永続化・取得
- クエリの構築
- データアクセスパターンの実装

**依存してはいけないもの**:

- HTTPリクエスト/レスポンス
- ビジネスロジック（それはサービス層の仕事）

#### 3. Service Layer（Facadeパターン）

```python
# src/app/services/project/project/__init__.py（Facade）
class ProjectService:
    """ビジネスロジックのオーケストレーション（Facade）。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._crud_service = ProjectCrudService(db)

    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        """サブサービスに委譲。"""
        return await self._crud_service.create_project(project_data, creator_id)


# src/app/services/project/project/crud.py（サブサービス）
class ProjectCrudService(ProjectBaseService):
    """プロジェクト作成のビジネスロジック。"""

    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        # バリデーション
        existing = await self.project_repo.get_by_code(project_data.code)
        if existing:
            raise ValidationError("プロジェクトコードが既に使用されています")

        # プロジェクト作成
        project = await self.project_repo.create(
            name=project_data.name,
            code=project_data.code,
            created_by=creator_id,
        )

        # メンバー追加
        await self.member_repo.create(
            project_id=project.id,
            user_id=creator_id,
            role=ProjectRole.OWNER,
        )

        await self.db.commit()
        return project
```

**責務**:

- ビジネスルールの実装
- 複数のリポジトリの調整
- トランザクション境界の定義
- ドメインロジックのオーケストレーション

#### 4. API Layer（最も外側）

```python
# src/app/api/routes/v1/projects.py
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectServiceDep,
    current_user: CurrentUserDep,
) -> ProjectResponse:
    """プロジェクト作成エンドポイント。"""
    project = await project_service.create_project(project_data, current_user.id)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUserDep,
) -> ProjectResponse:
    """プロジェクト詳細取得エンドポイント。"""
    project = await project_service.get_project(project_id)
    return ProjectResponse.model_validate(project)
```

**責務**:

- HTTPリクエストの受け取り
- 入力のバリデーション（Pydanticスキーマ）
- サービス層の呼び出し
- レスポンスの整形
- エラーハンドリング

---

## 3. 依存性注入（Dependency Injection）

FastAPIの依存性注入システムを活用して、テスタビリティと疎結合を実現します。

### 実装例

```python
# src/app/api/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# データベースセッションの依存性
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# サービスの依存性（Facadeサービス）
def get_project_service(db: DatabaseDep) -> ProjectService:
    return ProjectService(db)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_user_account_service(db: DatabaseDep) -> UserAccountService:
    return UserAccountService(db)


UserAccountServiceDep = Annotated[UserAccountService, Depends(get_user_account_service)]


# 認証の依存性
async def get_current_user(
    authorization: str | None = Header(None),
    user_service: UserAccountServiceDep = None,
) -> UserAccount:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = await user_service.get_user(uuid.UUID(user_id))
    return user


CurrentUserDep = Annotated[UserAccount, Depends(get_current_user)]
```

### 使用例

```python
# エンドポイントで依存性を注入
@router.get("/me", response_model=UserAccountResponse)
async def get_current_user_info(
    current_user: CurrentUserDep,
) -> UserAccountResponse:
    """現在のユーザー情報を取得。依存性注入により自動的に認証が行われる。"""
    return UserAccountResponse.model_validate(current_user)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    """複数の依存性を注入。"""
    project = await project_service.create_project(
        project_data=project_data,
        creator_id=current_user.id,
    )
    return ProjectResponse.model_validate(project)
```

### 依存性注入の利点

1. **テスタビリティ**

   ```python
   # テスト時にモックを注入可能
   def mock_user_service():
       return MockUserService()

   app.dependency_overrides[get_user_service] = mock_user_service
   ```

2. **疎結合**

   - コンポーネント間の結合度が低い
   - 実装の変更が容易

3. **再利用性**
   - 共通の依存性を複数のエンドポイントで使用可能

---

## よくある間違いとその対処法

### 間違い1: 層の責務を混在させる

```python
# ❌ 悪い例：サービス層でHTTPレスポンスを作成
class ProjectCrudService:
    async def create_project(self, project_data: ProjectCreate) -> dict:
        project = await self.project_repo.create(...)
        # HTTPレスポンスはAPI層の責務（悪い）
        return {
            "status": "success",
            "data": {"id": str(project.id), "name": project.name}
        }

# ✅ 良い例：サービス層はドメインオブジェクトを返す
class ProjectCrudService:
    async def create_project(self, project_data: ProjectCreate) -> Project:
        return await self.project_repo.create(...)
```

### 間違い2: 内側の層が外側の層に依存

```python
# ❌ 悪い例：モデルがAPIスキーマを知っている
class Project(Base):
    def to_response(self) -> ProjectResponse:
        return ProjectResponse(...)

# ✅ 良い例：外側の層（API）が内側を知る
@router.get("/{project_id}")
async def get_project(project_id: uuid.UUID, project_service: ProjectServiceDep):
    project = await project_service.get_project(project_id)
    return ProjectResponse.model_validate(project)  # API層で変換
```

### 間違い3: ビジネスロジックをリポジトリに配置

```python
# ❌ 悪い例：リポジトリにビジネスロジック
class ProjectRepository:
    async def create_with_validation(self, project_data: ProjectCreate):
        # バリデーションはサービス層の責務（悪い）
        if await self.get_by_code(project_data.code):
            raise ValidationError("Project code exists")
        return await self.create(...)

# ✅ 良い例：ビジネスロジックはサービス層（サブサービス）
class ProjectCrudService(ProjectBaseService):
    async def create_project(self, project_data: ProjectCreate, creator_id: uuid.UUID):
        if await self.project_repo.get_by_code(project_data.code):
            raise ValidationError("Project code exists")
        return await self.project_repo.create(...)
```

---

## 参考リンク

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [The Dependency Inversion Principle](https://stackify.com/dependency-inversion-principle/)

---

次のセクション: [03-readable-code.md](./03-readable-code.md)
