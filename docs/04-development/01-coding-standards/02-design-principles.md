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
# src/app/services/sample_user.py
class SampleUserService:
    """ユーザーのビジネスロジック専用サービス。"""

    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        """ユーザー作成のビジネスロジックのみを担当。"""
        # バリデーション
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("User already exists")

        # パスワードハッシュ化（セキュリティモジュールに委譲）
        hashed_password = hash_password(user_data.password)

        # データ永続化（リポジトリに委譲）
        user = await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        return user


# src/app/repositories/sample_user.py
class SampleUserRepository(BaseRepository[SampleUser]):
    """ユーザーのデータアクセス専用リポジトリ。"""

    async def get_by_email(self, email: str) -> SampleUser | None:
        """データアクセスロジックのみを担当。"""
        query = select(SampleUser).where(SampleUser.email == email)
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
class SampleUserRepository(BaseRepository[SampleUser]):
    pass

class SampleSessionRepository(BaseRepository[Session]):
    pass


# どのリポジトリも同じように使用可能
async def get_entity(repo: BaseRepository[Any], entity_id: int):
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
    async def create_user(self, data: SampleUserCreate) -> SampleUser: pass

    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> SampleUser: pass

    @abstractmethod
    async def send_welcome_email(self, user: SampleUser) -> None: pass

    @abstractmethod
    async def generate_report(self, user_id: int) -> Report: pass


# 良い例：小さなインターフェースに分離
class UserCreator(ABC):
    @abstractmethod
    async def create_user(self, data: SampleUserCreate) -> SampleUser: pass


class UserAuthenticator(ABC):
    @abstractmethod
    async def authenticate(self, email: str, password: str) -> SampleUser: pass


class EmailSender(ABC):
    @abstractmethod
    async def send_welcome_email(self, user: SampleUser) -> None: pass


class ReportGenerator(ABC):
    @abstractmethod
    async def generate_report(self, user_id: int) -> Report: pass
```

### D - Dependency Inversion Principle（依存性逆転の原則）

高レベルモジュールは低レベルモジュールに依存すべきではありません。両方とも抽象に依存すべきです。

#### 実装例

```python
# src/app/api/dependencies.py
# 依存性注入を使用して抽象に依存

def get_sample_user_service(db: DatabaseDep) -> SampleUserService:
    """SampleUserServiceを注入。具体的な実装は隠蔽。"""
    return SampleUserService(db)


SampleUserServiceDep = Annotated[SampleUserService, Depends(get_sample_user_service)]


# src/app/api/routes/sample_users.py
@router.post("/users", response_model=SampleUserResponse)
async def create_user(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,  # 抽象に依存、具体的な実装は知らない
) -> SampleUserResponse:
    """APIルートは具体的な実装ではなく、抽象（インターフェース）に依存。"""
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(sample_user)
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
@router.post("/users")
async def create_user(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,  # サービス層に依存
):
    return await user_service.create_user(user_data)


# Service Layer -> Repository Layer
class SampleUserService:
    def __init__(self, db: AsyncSession):
        self.repository = SampleUserRepository(db)  # リポジトリ層に依存

    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        return await self.repository.create(...)


# ❌ 悪い例：内側が外側に依存
class SampleUser(Base):
    # モデルがAPIレスポンスを知っている（悪い）
    def to_api_response(self) -> SampleUserResponse:
        pass
```

### 層ごとの責務

#### 1. Model Layer（最も内側）

```python
# src/app/models/sample_user.py
from sqlalchemy.orm import Mapped, mapped_column

class SampleUser(Base):
    """純粋なドメインモデル。ビジネスルールのみを持つ。"""

    __tablename__ = "sample_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # リレーションシップ
    sessions: Mapped[list["SampleSession"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
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
# src/app/repositories/sample_user.py
class SampleUserRepository(BaseRepository[SampleUser]):
    """データアクセスの抽象化。"""

    def __init__(self, db: AsyncSession):
        super().__init__(SampleUser, db)

    async def get_by_email(self, email: str) -> SampleUser | None:
        """メールアドレスでユーザーを検索。"""
        query = select(SampleUser).where(SampleUser.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> SampleUser | None:
        """ユーザー名でユーザーを検索。"""
        query = select(SampleUser).where(SampleUser.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

**責務**:

- データの永続化・取得
- クエリの構築
- データアクセスパターンの実装

**依存してはいけないもの**:

- HTTPリクエスト/レスポンス
- ビジネスロジック（それはサービス層の仕事）

#### 3. Service Layer

```python
# src/app/services/sample_user.py
class SampleUserService:
    """ビジネスロジックのオーケストレーション。"""

    def __init__(self, db: AsyncSession):
        self.repository = SampleUserRepository(db)

    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        """ユーザー作成のビジネスロジック。"""
        # バリデーション
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("User already exists")

        existing_username = await self.repository.get_by_username(user_data.username)
        if existing_username:
            raise ValidationError("Username already taken")

        # パスワードハッシュ化
        hashed_password = hash_password(user_data.password)

        # ユーザー作成
        user = await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        return user

    async def authenticate(self, email: str, password: str) -> SampleUser:
        """認証ビジネスロジック。"""
        user = await self.repository.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user
```

**責務**:

- ビジネスルールの実装
- 複数のリポジトリの調整
- トランザクション境界の定義
- ドメインロジックのオーケストレーション

#### 4. API Layer（最も外側）

```python
# src/app/api/routes/sample_users.py
@router.post("/register", response_model=SampleUserResponse)
async def register(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """ユーザー登録エンドポイント。"""
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(sample_user)


@router.post("/login", response_model=Token)
async def login(
    login_data: SampleUserLogin,
    user_service: SampleUserServiceDep,
) -> Token:
    """ログインエンドポイント。"""
    user = await user_service.authenticate(
        login_data.email,
        login_data.password
    )

    # トークン生成
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(access_token=access_token, token_type="bearer")
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


# サービスの依存性
def get_sample_user_service(db: DatabaseDep) -> SampleUserService:
    return SampleUserService(db)


SampleUserServiceDep = Annotated[SampleUserService, Depends(get_sample_user_service)]


# 認証の依存性
async def get_current_user(
    authorization: str | None = Header(None),
    user_service: SampleUserServiceDep = None,
) -> SampleUser:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = await user_service.get_user(int(user_id))
    return user


CurrentSampleUserDep = Annotated[SampleUser, Depends(get_current_user)]
```

### 使用例

```python
# エンドポイントで依存性を注入
@router.get("/me", response_model=SampleUserResponse)
async def get_current_user_info(
    current_user: CurrentSampleUserDep,
) -> SampleUserResponse:
    """現在のユーザー情報を取得。依存性注入により自動的に認証が行われる。"""
    return SampleUserResponse.model_validate(current_user)


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: CurrentSampleUserDep,
    session_service: SampleSessionServiceDep,
) -> SessionResponse:
    """複数の依存性を注入。"""
    session = await session_service.create_session(
        user_id=current_user.id,
        metadata=session_data.metadata
    )
    return SessionResponse.model_validate(session)
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
class SampleUserService:
    async def create_user(self, user_data: SampleUserCreate) -> dict:
        user = await self.repository.create(...)
        # HTTPレスポンスはAPI層の責務（悪い）
        return {
            "status": "success",
            "data": {"id": user.id, "email": user.email}
        }

# ✅ 良い例：サービス層はドメインオブジェクトを返す
class SampleUserService:
    async def create_user(self, user_data: SampleUserCreate) -> SampleUser:
        return await self.repository.create(...)
```

### 間違い2: 内側の層が外側の層に依存

```python
# ❌ 悪い例：モデルがAPIスキーマを知っている
class SampleUser(Base):
    def to_response(self) -> SampleUserResponse:
        return SampleUserResponse(...)

# ✅ 良い例：外側の層（API）が内側を知る
@router.get("/users/{user_id}")
async def get_user(user_id: int, user_service: SampleUserServiceDep):
    user = await user_service.get_user(user_id)
    return SampleUserResponse.model_validate(sample_user)  # API層で変換
```

### 間違い3: ビジネスロジックをリポジトリに配置

```python
# ❌ 悪い例：リポジトリにビジネスロジック
class SampleUserRepository:
    async def create_user_with_validation(self, user_data: SampleUserCreate):
        # バリデーションはサービス層の責務（悪い）
        if await self.get_by_email(user_data.email):
            raise ValidationError("User exists")
        return await self.create(...)

# ✅ 良い例：ビジネスロジックはサービス層
class SampleUserService:
    async def create_user(self, user_data: SampleUserCreate):
        if await self.repository.get_by_email(user_data.email):
            raise ValidationError("User exists")
        return await self.repository.create(...)
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
