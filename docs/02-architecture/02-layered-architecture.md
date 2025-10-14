# レイヤードアーキテクチャ

このドキュメントでは、AI Agent Appが採用しているエンタープライズレイヤードアーキテクチャについて説明します。

## アーキテクチャ概要

このプロジェクトは、関心の分離（Separation of Concerns）の原則に基づき、4つの主要なレイヤーで構成されています。

```
┌─────────────────────────────────────────────┐
│           API Layer (api/)                  │  ← HTTPリクエスト/レスポンス
│  - Routes: エンドポイント定義               │
│  - Dependencies: 依存性注入                  │
│  - Middlewares: 横断的関心事                │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│        Service Layer (services/)            │  ← ビジネスロジック
│  - ビジネスルールの実装                      │
│  - トランザクション管理                      │
│  - 複数リポジトリの調整                      │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│      Repository Layer (repositories/)       │  ← データアクセス
│  - データベースクエリ                        │
│  - CRUD操作                                  │
│  - データアクセスの抽象化                    │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│         Model Layer (models/)               │  ← データ定義
│  - SQLAlchemyモデル                          │
│  - テーブル定義                              │
│  - リレーションシップ                        │
└─────────────────────────────────────────────┘
```

## データフロー

### リクエストフロー（API → Database）

```
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

```
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
# src/app/api/routes/users.py
from fastapi import APIRouter, status
from app.api.dependencies import UserServiceDep, CurrentUserDep
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    user_data: UserCreate,                    # リクエストバリデーション
    service: UserServiceDep,                  # 依存性注入
) -> UserResponse:
    """新しいユーザーを作成します。"""
    # サービス層を呼び出し
    user = await service.create_user(user_data)

    # レスポンスを返却
    return UserResponse.model_validate(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: CurrentUserDep,             # 認証済みユーザー
) -> UserResponse:
    """現在のユーザー情報を取得します。"""
    return UserResponse.model_validate(current_user)
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

**実装例**:

```python
# src/app/services/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.repositories.session import SessionRepository
from app.core.security import hash_password, create_access_token
from app.core.exceptions import ValidationError, AuthenticationError
from app.schemas.user import UserCreate

class UserService:
    """ユーザー関連のビジネスロジック。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """新しいユーザーを作成します。

        ビジネスルール:
        - メールアドレスは一意である必要がある
        - ユーザー名は一意である必要がある
        - パスワードは安全にハッシュ化される
        """
        # ビジネスルール1: 既存ユーザーのチェック
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError(
                "User with this email already exists",
                details={"email": user_data.email}
            )

        existing_username = await self.user_repo.get_by_username(user_data.username)
        if existing_username:
            raise ValidationError(
                "Username already taken",
                details={"username": user_data.username}
            )

        # ビジネスルール2: パスワードのハッシュ化
        hashed_password = hash_password(user_data.password)

        # リポジトリを使用してユーザーを作成
        user = await self.user_repo.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

        return user

    async def authenticate_user(self, email: str, password: str) -> tuple[User, str]:
        """ユーザーを認証し、アクセストークンを返します。"""
        # ユーザーの取得
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        # パスワードの検証
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # アクティブユーザーのチェック
        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # アクセストークンの生成
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return user, access_token
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
from app.database import Base

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
# src/app/repositories/user.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    """ユーザー専用のリポジトリ。"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得。"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """ユーザー名でユーザーを取得。"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """アクティブなユーザーの一覧を取得。"""
        query = (
            select(User)
            .where(User.is_active == True)
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
# src/app/models/user.py
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    """ユーザーモデル。"""

    __tablename__ = "users"

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
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    files: Mapped[list["File"]] = relationship(
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

## 依存関係のルール

各レイヤーは、自分より下のレイヤーにのみ依存できます。

```
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
class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)  # OK

# API層はService層に依存
@router.post("/users")
async def create_user(service: UserServiceDep):  # OK
    return await service.create_user(...)
```

### 悪い例

```python
# API層がRepository層に直接依存（Service層をスキップ）
@router.post("/users")
async def create_user(db: DatabaseDep):
    repository = UserRepository(db)  # NG: Service層を経由すべき
    return await repository.create(...)

# Model層がService層に依存
class User(Base):
    def send_email(self):
        # NG: モデルはビジネスロジックを持つべきでない
        email_service.send(...)
```

## トランザクション管理

トランザクションはService層で管理します。

```python
# src/app/services/user.py
class UserService:
    async def register_user_with_profile(
        self,
        user_data: UserCreate,
        profile_data: ProfileCreate,
    ) -> User:
        """ユーザーとプロフィールを同時に作成（トランザクション）。"""
        # 複数のリポジトリ操作を1つのトランザクションで実行
        try:
            # ユーザー作成
            user = await self.user_repo.create(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hash_password(user_data.password),
            )

            # プロフィール作成
            await self.profile_repo.create(
                user_id=user.id,
                **profile_data.model_dump(),
            )

            # トランザクションは get_db() の finally ブロックでコミットされる
            return user

        except Exception as e:
            # エラーが発生した場合、get_db() がロールバックを実行
            raise
```

データベースセッションの管理:

```python
# src/app/database.py
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
class UserService:
    async def get_user(self, user_id: int) -> User:
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
