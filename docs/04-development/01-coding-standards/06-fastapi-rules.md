# FastAPI規約

FastAPIを使用したAPI開発における規約とベストプラクティスについて説明します。

## 概要

本プロジェクトでは以下のFastAPI規約を遵守します：

- **エンドポイント設計**
- **依存性注入の活用**
- **async/awaitの適切な使用**
- **レスポンスモデルの定義**
- **エラーハンドリング**

---

## 1. エンドポイント設計

### ルーターの使用

各リソースごとにルーターを分割します。

```python
# src/app/api/routes/sample_users.py
from fastapi import APIRouter, status
from app.api.core import CurrentSampleUserDep, SampleUserServiceDep
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=SampleUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録",
    description="新しいユーザーアカウントを作成します"
)
async def register(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """ユーザー登録エンドポイント。

    Args:
        user_data: ユーザー作成データ
        user_service: ユーザーサービス

    Returns:
        作成されたユーザー情報
    """
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(sample_user)


@router.get(
    "/me",
    response_model=SampleUserResponse,
    summary="現在のユーザー情報取得"
)
async def get_current_user_info(
    current_user: CurrentSampleUserDep,
) -> SampleUserResponse:
    """認証済みユーザーの情報を取得。"""
    return SampleUserResponse.model_validate(current_user)
```

### エンドポイントの命名

RESTful原則に従います。

```python
# ✅ 良い例
@router.get("/users")              # 一覧取得
@router.post("/users")             # 作成
@router.get("/users/{user_id}")    # 詳細取得
@router.put("/users/{user_id}")    # 更新
@router.delete("/users/{user_id}") # 削除

# サブリソース
@router.get("/users/{user_id}/sessions")
@router.get("/users/{user_id}/files")

# アクション
@router.post("/users/register")
@router.post("/users/login")


# ❌ 悪い例
@router.get("/getUsers")           # 動詞を含めない
@router.post("/createUser")
```

---

## 2. メソッド配置順序（RESTful標準順序）

### 基本原則

すべてのエンドポイント、サービスメソッド、リポジトリメソッドは **RESTful標準順序** で配置します。

**標準順序:** GET → POST → PATCH → DELETE → OTHER（プライベートメソッド等）

この順序により：
- コードの可読性が向上
- メソッドの検索が容易
- コードレビューが効率化
- チーム全体で一貫した構造

### API Routesでの配置順序

```python
# src/app/api/routes/v1/users.py
from fastapi import APIRouter, status

router = APIRouter()


# ========================================
# GET エンドポイント（一覧・詳細取得）
# ========================================

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserServiceDep = None,
) -> list[UserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: CurrentUserDep,
) -> UserResponse:
    """現在のユーザー情報を取得。"""
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserServiceDep,
) -> UserResponse:
    """特定ユーザーを取得。"""
    user = await user_service.get_user(user_id)
    return UserResponse.model_validate(user)


# ========================================
# POST エンドポイント（作成・アクション）
# ========================================

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """ユーザーを作成。"""
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


# ========================================
# PATCH エンドポイント（部分更新）
# ========================================

@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserResponse:
    """現在のユーザー情報を更新。"""
    user = await user_service.update_user(current_user.id, user_data)
    return UserResponse.model_validate(user)


# ========================================
# DELETE エンドポイント（削除）
# ========================================

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """ユーザーを削除。"""
    await user_service.delete_user(user_id)
```

### Servicesでの配置順序

```python
# src/app/services/user.py
class UserService:
    """ユーザーサービス。"""

    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    # ========================================
    # GET メソッド（取得系）
    # ========================================

    async def get_user(self, user_id: int) -> User:
        """ユーザーを取得。"""
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得。"""
        return await self.repository.get_by_email(email)

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """ユーザー一覧を取得。"""
        return await self.repository.get_multi(skip=skip, limit=limit)

    # ========================================
    # POST メソッド（作成系）
    # ========================================

    async def create_user(self, user_data: UserCreate) -> User:
        """ユーザーを作成。"""
        # バリデーション
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValidationError("Email already exists")

        # パスワードハッシュ化
        hashed_password = hash_password(user_data.password)

        # 作成
        return await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

    # ========================================
    # PATCH メソッド（更新系）
    # ========================================

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """ユーザー情報を更新。"""
        user = await self.get_user(user_id)
        return await self.repository.update(user, user_data.model_dump(exclude_unset=True))

    # ========================================
    # DELETE メソッド（削除系）
    # ========================================

    async def delete_user(self, user_id: int) -> None:
        """ユーザーを削除。"""
        user = await self.get_user(user_id)
        await self.repository.delete(user)

    # ========================================
    # OTHER メソッド（プライベート・ヘルパー）
    # ========================================

    async def _check_user_access(self, user_id: int, current_user: User) -> bool:
        """ユーザーアクセス権限をチェック（プライベートメソッド）。"""
        return user_id == current_user.id or current_user.is_superuser
```

### Repositoriesでの配置順序

```python
# src/app/repositories/user.py
class UserRepository(BaseRepository[User]):
    """ユーザーリポジトリ。"""

    # ========================================
    # GET メソッド（取得系）
    # ========================================

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得。"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_azure_oid(self, azure_oid: str) -> User | None:
        """Azure OIDでユーザーを取得。"""
        query = select(User).where(User.azure_oid == azure_oid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_users(self) -> list[User]:
        """アクティブユーザー一覧を取得。"""
        query = select(User).where(User.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================
    # POST メソッド（作成系）
    # ========================================
    # BaseRepositoryのcreateメソッドを使用

    # ========================================
    # PATCH メソッド（更新系）
    # ========================================
    # BaseRepositoryのupdateメソッドを使用

    # ========================================
    # DELETE メソッド（削除系）
    # ========================================
    # BaseRepositoryのdeleteメソッドを使用
```

### 順序を守るメリット

1. **可読性の向上**
   - 同じパターンですべてのファイルが構成される
   - 目的のメソッドを素早く見つけられる

2. **保守性の向上**
   - 新しいメソッドを追加する場所が明確
   - コードレビューが容易

3. **一貫性の確保**
   - チーム全体で同じ構造
   - 学習コストの削減

4. **RESTful原則との整合**
   - API設計のベストプラクティスに準拠
   - HTTPメソッドの標準的な使用順序と一致

### 注意点

```python
# ✅ 良い例：RESTful順序を守る
class UserService:
    async def get_user(self, user_id: int): pass       # GET
    async def list_users(self): pass                   # GET
    async def create_user(self, data): pass            # POST
    async def update_user(self, user_id, data): pass   # PATCH
    async def delete_user(self, user_id): pass         # DELETE
    async def _validate_email(self, email): pass       # PRIVATE


# ❌ 悪い例：順序がバラバラ
class UserService:
    async def create_user(self, data): pass            # POST
    async def _validate_email(self, email): pass       # PRIVATE
    async def delete_user(self, user_id): pass         # DELETE
    async def get_user(self, user_id: int): pass       # GET
    async def update_user(self, user_id, data): pass   # PATCH
    async def list_users(self): pass                   # GET
```


## 3. 依存性注入

### 依存性の定義

```python
# src/app/api/dependencies.py
from typing import Annotated
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.sample_user import SampleUserService

# データベース依存性
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# サービス依存性
def get_user_service(db: DatabaseDep) -> UserService:
    """UserServiceインスタンスを取得。"""
    return SampleUserService(db)


SampleUserServiceDep = Annotated[UserService, Depends(get_user_service)]


# 認証依存性
async def get_current_user(
    authorization: str | None = Header(None),
    user_service: SampleUserServiceDep = None,
) -> SampleUser:
    """現在の認証済みユーザーを取得。"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # トークン検証
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid scheme")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = await user_service.get_user(int(user_id))
    return user


CurrentSampleUserDep = Annotated[User, Depends(get_current_user)]
```

### 依存性の使用

```python
# src/app/api/routes/agents.py
from app.api.core import CurrentUserOptionalDep, SampleSessionServiceDep

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_service: SampleSessionServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> ChatResponse:
    """エージェントとチャット。

    認証はオプション（ゲストも使用可能）。
    """
    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
    else:
        user_id = current_user.id if current_user else None
        session = await session_service.create_session(
            user_id=user_id,
            metadata=request.context
        )

    # Add user message
    await session_service.add_message(
        session_id=session.session_id,
        role="user",
        content=request.message,
    )

    # Process with agent (placeholder)
    agent_response = f"Echo: {request.message}"

    # Add assistant message
    await session_service.add_message(
        session_id=session.session_id,
        role="assistant",
        content=agent_response,
    )

    return ChatResponse(
        response=agent_response,
        session_id=session.session_id,
    )
```

---

## 4. async/awaitの使用

### 非同期エンドポイント

データベースやI/O操作を行う場合は必ず`async def`を使用します。

```python
# ✅ 良い例：非同期エンドポイント
@router.get("/users/{user_id}", response_model=SampleUserResponse)
async def get_user(
    user_id: int,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """ユーザー詳細を取得。"""
    user = await user_service.get_user(user_id)
    return SampleUserResponse.model_validate(sample_user)


# ✅ 良い例：複数の非同期操作
@router.get("/users/{user_id}/dashboard", response_model=DashboardResponse)
async def get_user_dashboard(
    user_id: int,
    user_service: SampleUserServiceDep,
    session_service: SampleSessionServiceDep,
    file_service: SampleFileServiceDep,
) -> DashboardResponse:
    """ユーザーダッシュボードデータを取得。"""
    # 並列実行で高速化
    user, sessions, files = await asyncio.gather(
        user_service.get_user(user_id),
        session_service.list_user_sessions(user_id),
        file_service.list_user_files(user_id),
    )

    return DashboardResponse(
        user=user,
        sessions=sessions,
        files=files,
    )


# ❌ 悪い例：同期エンドポイント（DB操作があるのに）
@router.get("/users/{user_id}")
def get_user(user_id: int):  # asyncがない
    user = user_service.get_user(user_id)  # awaitがない
    return user
```

---

## 5. レスポンスモデル

### response_modelの指定

すべてのエンドポイントに`response_model`を指定します。

```python
# ✅ 良い例
@router.post("/users", response_model=SampleUserResponse, status_code=201)
async def create_user(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """ユーザーを作成。"""
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(sample_user)


@router.get("/users", response_model=list[SampleUserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_service: SampleUserServiceDep,
) -> list[SampleUserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(skip=skip, limit=limit)
    return [SampleUserResponse.model_validate(sample_user) for user in users]


# ❌ 悪い例：response_modelなし
@router.post("/users")
async def create_user(user_data: SampleUserCreate, user_service: SampleUserServiceDep):
    return await user_service.create_user(user_data)
```

### Pydanticスキーマの使用

```python
# src/app/schemas/sample_user.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime


class SampleUserBase(BaseModel):
    """ベースユーザースキーマ。"""

    email: EmailStr = Field(..., description="メールアドレス")
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")


class SampleUserCreate(SampleUserBase):
    """ユーザー作成スキーマ。"""

    password: str = Field(..., min_length=8, max_length=100, description="パスワード")


class SampleUserUpdate(BaseModel):
    """ユーザー更新スキーマ。"""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None


class SampleUserResponse(SampleUserBase):
    """ユーザーレスポンススキーマ。"""

    id: int = Field(..., description="ユーザーID")
    is_active: bool = Field(..., description="アクティブ状態")
    created_at: datetime = Field(..., description="作成日時")

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemyモデルから変換可能
```

---

## 6. エラーハンドリング

### カスタム例外ハンドラー

```python
# src/app/api/middlewares/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """アプリケーション例外ハンドラー。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        },
    )


# src/app/main.py
from app.api.middlewares.error_handler import app_exception_handler
from app.core.exceptions import AppException

app = FastAPI(title="Backend API")

# 例外ハンドラー登録
app.add_exception_handler(AppException, app_exception_handler)
```

### HTTPExceptionの使用

```python
from fastapi import HTTPException, status

@router.get("/users/{user_id}")
async def get_user(user_id: int, user_service: SampleUserServiceDep):
    """ユーザーを取得。"""
    try:
        user = await user_service.get_user(user_id)
        return SampleUserResponse.model_validate(sample_user)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
```

---

## 7. バリデーション

### クエリパラメータ

```python
from fastapi import Query

@router.get("/users", response_model=list[SampleUserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    is_active: bool | None = Query(None, description="アクティブ状態でフィルタ"),
    user_service: SampleUserServiceDep = None,
) -> list[SampleUserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    return [SampleUserResponse.model_validate(sample_user) for user in users]
```

### パスパラメータ

```python
from fastapi import Path

@router.get("/users/{user_id}", response_model=SampleUserResponse)
async def get_user(
    user_id: int = Path(..., gt=0, description="ユーザーID"),
    user_service: SampleUserServiceDep = None,
) -> SampleUserResponse:
    """ユーザー詳細を取得。"""
    user = await user_service.get_user(user_id)
    return SampleUserResponse.model_validate(sample_user)
```

### リクエストボディ

```python
from fastapi import Body

@router.post("/users", response_model=SampleUserResponse)
async def create_user(
    user_data: SampleUserCreate = Body(..., description="ユーザー作成データ"),
    user_service: SampleUserServiceDep = None,
) -> SampleUserResponse:
    """ユーザーを作成。"""
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(sample_user)
```

---

---

## 8. ミドルウェア

### ログミドルウェア

```python
# src/app/api/middlewares/logging.py
import time
from fastapi import Request
from app.core.logging import logger


async def log_requests(request: Request, call_next):
    """リクエストログミドルウェア。"""
    start_time = time.time()

    # リクエスト情報をログ
    logger.info(f"Request: {request.method} {request.url.path}")

    # エンドポイント処理
    response = await call_next(request)

    # レスポンス時間を計算
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"({process_time:.3f}s)"
    )

    return response
```

### エラーハンドリングミドルウェア

```python
# src/app/api/middlewares/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException
from app.core.logging import logger


async def catch_exceptions_middleware(request: Request, call_next):
    """例外キャッチミドルウェア。"""
    try:
        return await call_next(request)
    except AppException as e:
        logger.warning(f"App exception: {e.message}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.message, "details": e.details}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
```

---

## よくある間違いとその対処法

### 間違い1: 同期関数でDB操作

```python
# ❌ 悪い例
@router.get("/users/{user_id}")
def get_user(user_id: int):  # asyncがない
    return db.query(User).filter(SampleUser.id == user_id).first()

# ✅ 良い例
@router.get("/users/{user_id}")
async def get_user(user_id: int, user_service: SampleUserServiceDep):
    return await user_service.get_user(user_id)
```

### 間違い2: response_modelの欠如

```python
# ❌ 悪い例
@router.post("/users")
async def create_user(data: SampleUserCreate):
    return await service.create_user(data)

# ✅ 良い例
@router.post("/users", response_model=SampleUserResponse)
async def create_user(data: SampleUserCreate, service: SampleUserServiceDep):
    user = await service.create_user(data)
    return SampleUserResponse.model_validate(sample_user)
```

### 間違い3: 依存性注入を使わない

```python
# ❌ 悪い例
@router.post("/users")
async def create_user(data: SampleUserCreate):
    db = SessionLocal()  # 手動でセッション作成
    service = SampleUserService(db)
    return await service.create_user(data)

# ✅ 良い例
@router.post("/users")
async def create_user(
    data: SampleUserCreate,
    service: SampleUserServiceDep,  # 依存性注入
):
    return await service.create_user(data)
```

---

## 参考リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

次のセクション: [07-tools-setup.md](./07-tools-setup.md)
