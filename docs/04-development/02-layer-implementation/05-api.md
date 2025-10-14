# API層（API Routes）

FastAPIエンドポイントの実装について説明します。

## 概要

API層は、HTTPリクエストを受け取り、サービス層を呼び出し、レスポンスを返します。

**責務**:
- HTTPリクエストの受け取り
- 入力バリデーション（Pydanticスキーマ）
- サービス層の呼び出し
- レスポンスの整形
- エラーハンドリング

---

## 基本的なエンドポイント

```python
# src/app/api/routes/users.py
from fastapi import APIRouter, status
from app.api.dependencies import CurrentUserDep, UserServiceDep
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.core.security import create_access_token

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録"
)
async def register(
    user_data: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """新しいユーザーを登録。"""
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    user_service: UserServiceDep,
) -> Token:
    """ログイン。"""
    user = await user_service.authenticate(
        login_data.email,
        login_data.password
    )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUserDep,
) -> UserResponse:
    """現在のユーザー情報を取得。"""
    return UserResponse.model_validate(current_user)
```

---

## パスパラメータとクエリパラメータ

```python
from fastapi import Query, Path


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., gt=0, description="ユーザーID"),
    user_service: UserServiceDep = None,
) -> UserResponse:
    """ユーザー詳細を取得。"""
    user = await user_service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="スキップ件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    user_service: UserServiceDep = None,
) -> list[UserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]
```

---

## ルーターの統合

```python
# src/app/main.py
from fastapi import FastAPI
from app.api.routes import users, agents, files

app = FastAPI(title="Backend API")

# ルーター登録
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
```

---

## ベストプラクティス

1. **response_modelを必ず指定**
2. **依存性注入を活用**
3. **HTTPステータスコードを適切に設定**
4. **OpenAPIドキュメント用のメタデータを追加**

---

次のセクション: [../03-database/01-sqlalchemy-basics.md](../03-database/01-sqlalchemy-basics.md)
