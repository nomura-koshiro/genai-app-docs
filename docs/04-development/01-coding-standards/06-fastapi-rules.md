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
# src/app/api/routes/users.py
from fastapi import APIRouter, status
from app.api.dependencies import CurrentUserDep, UserServiceDep
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録",
    description="新しいユーザーアカウントを作成します"
)
async def register(
    user_data: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """ユーザー登録エンドポイント。

    Args:
        user_data: ユーザー作成データ
        user_service: ユーザーサービス

    Returns:
        作成されたユーザー情報
    """
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="現在のユーザー情報取得"
)
async def get_current_user_info(
    current_user: CurrentUserDep,
) -> UserResponse:
    """認証済みユーザーの情報を取得。"""
    return UserResponse.model_validate(current_user)
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

## 2. 依存性注入

### 依存性の定義

```python
# src/app/api/dependencies.py
from typing import Annotated
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.user import UserService

# データベース依存性
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# サービス依存性
def get_user_service(db: DatabaseDep) -> UserService:
    """UserServiceインスタンスを取得。"""
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


# 認証依存性
async def get_current_user(
    authorization: str | None = Header(None),
    user_service: UserServiceDep = None,
) -> User:
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


CurrentUserDep = Annotated[User, Depends(get_current_user)]
```

### 依存性の使用

```python
# src/app/api/routes/agents.py
from app.api.dependencies import CurrentUserOptionalDep, SessionServiceDep

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_service: SessionServiceDep = None,
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

## 3. async/awaitの使用

### 非同期エンドポイント

データベースやI/O操作を行う場合は必ず`async def`を使用します。

```python
# ✅ 良い例：非同期エンドポイント
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserServiceDep,
) -> UserResponse:
    """ユーザー詳細を取得。"""
    user = await user_service.get_user(user_id)
    return UserResponse.model_validate(user)


# ✅ 良い例：複数の非同期操作
@router.get("/users/{user_id}/dashboard", response_model=DashboardResponse)
async def get_user_dashboard(
    user_id: int,
    user_service: UserServiceDep,
    session_service: SessionServiceDep,
    file_service: FileServiceDep,
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

## 4. レスポンスモデル

### response_modelの指定

すべてのエンドポイントに`response_model`を指定します。

```python
# ✅ 良い例
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """ユーザーを作成。"""
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserServiceDep,
) -> list[UserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


# ❌ 悪い例：response_modelなし
@router.post("/users")
async def create_user(user_data: UserCreate, user_service: UserServiceDep):
    return await user_service.create_user(user_data)
```

### Pydanticスキーマの使用

```python
# src/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    """ベースユーザースキーマ。"""

    email: EmailStr = Field(..., description="メールアドレス")
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")


class UserCreate(UserBase):
    """ユーザー作成スキーマ。"""

    password: str = Field(..., min_length=8, max_length=100, description="パスワード")


class UserUpdate(BaseModel):
    """ユーザー更新スキーマ。"""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None


class UserResponse(UserBase):
    """ユーザーレスポンススキーマ。"""

    id: int = Field(..., description="ユーザーID")
    is_active: bool = Field(..., description="アクティブ状態")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        """Pydantic設定。"""
        from_attributes = True  # SQLAlchemyモデルから変換可能
```

---

## 5. エラーハンドリング

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
async def get_user(user_id: int, user_service: UserServiceDep):
    """ユーザーを取得。"""
    try:
        user = await user_service.get_user(user_id)
        return UserResponse.model_validate(user)
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

## 6. バリデーション

### クエリパラメータ

```python
from fastapi import Query

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    is_active: bool | None = Query(None, description="アクティブ状態でフィルタ"),
    user_service: UserServiceDep = None,
) -> list[UserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    return [UserResponse.model_validate(user) for user in users]
```

### パスパラメータ

```python
from fastapi import Path

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., gt=0, description="ユーザーID"),
    user_service: UserServiceDep = None,
) -> UserResponse:
    """ユーザー詳細を取得。"""
    user = await user_service.get_user(user_id)
    return UserResponse.model_validate(user)
```

### リクエストボディ

```python
from fastapi import Body

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate = Body(..., description="ユーザー作成データ"),
    user_service: UserServiceDep = None,
) -> UserResponse:
    """ユーザーを作成。"""
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)
```

---

## 7. ミドルウェア

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
    return db.query(User).filter(User.id == user_id).first()

# ✅ 良い例
@router.get("/users/{user_id}")
async def get_user(user_id: int, user_service: UserServiceDep):
    return await user_service.get_user(user_id)
```

### 間違い2: response_modelの欠如

```python
# ❌ 悪い例
@router.post("/users")
async def create_user(data: UserCreate):
    return await service.create_user(data)

# ✅ 良い例
@router.post("/users", response_model=UserResponse)
async def create_user(data: UserCreate, service: UserServiceDep):
    user = await service.create_user(data)
    return UserResponse.model_validate(user)
```

### 間違い3: 依存性注入を使わない

```python
# ❌ 悪い例
@router.post("/users")
async def create_user(data: UserCreate):
    db = SessionLocal()  # 手動でセッション作成
    service = UserService(db)
    return await service.create_user(data)

# ✅ 良い例
@router.post("/users")
async def create_user(
    data: UserCreate,
    service: UserServiceDep,  # 依存性注入
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
