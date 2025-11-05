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
# src/app/api/routes/sample_users.py
from fastapi import APIRouter, status
from app.api.core import CurrentSampleUserDep, SampleUserServiceDep
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse, SampleUserLogin, Token
from app.core.security import create_access_token

router = APIRouter()


@router.post(
    "/register",
    response_model=SampleUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録"
)
async def register(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """新しいユーザーを登録。"""
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(sample_user)


@router.post("/login", response_model=Token)
async def login(
    login_data: SampleUserLogin,
    user_service: SampleUserServiceDep,
) -> Token:
    """ログイン。"""
    user = await user_service.authenticate(
        login_data.email,
        login_data.password
    )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=SampleUserResponse)
async def get_current_user_info(
    current_user: CurrentSampleUserDep,
) -> SampleUserResponse:
    """現在のユーザー情報を取得。"""
    return SampleUserResponse.model_validate(current_user)
```

---

## パスパラメータとクエリパラメータ

```python
from fastapi import Query, Path


@router.get("/users/{user_id}", response_model=SampleUserResponse)
async def get_user(
    user_id: int = Path(..., gt=0, description="ユーザーID"),
    user_service: SampleUserServiceDep = None,
) -> SampleUserResponse:
    """ユーザー詳細を取得。"""
    user = await user_service.get_user(user_id)
    return SampleUserResponse.model_validate(sample_user)


@router.get("/users", response_model=list[SampleUserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="スキップ件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    user_service: SampleUserServiceDep = None,
) -> list[SampleUserResponse]:
    """ユーザー一覧を取得。"""
    users = await user_service.list_users(skip=skip, limit=limit)
    return [SampleUserResponse.model_validate(sample_user) for user in users]
```

---

## ルーターの統合

```python
# src/app/main.py
from fastapi import FastAPI
from app.api.routes import users, agents, files

app = FastAPI(title="Backend API")

# ルーター登録
app.include_router(users.router, prefix="/api/sample-users", tags=["users"])
app.include_router(agents.router, prefix="/api/sample-agents", tags=["agents"])
app.include_router(files.router, prefix="/api/sample-files", tags=["files"])
```

---

## エラーハンドリング

### 推奨: デコレータパターン

**実装場所**: `src/app/api/decorators.py`

すべてのエンドポイントに `@handle_service_errors` デコレータを適用します。

```python
from fastapi import APIRouter, status
from app.api.decorators import handle_service_errors
from app.api.core import SampleUserServiceDep
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse

router = APIRouter()

@router.post("", response_model=SampleUserResponse, status_code=status.HTTP_201_CREATED)
@handle_service_errors  # エラーハンドリングデコレータ
async def create_user(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """新しいユーザーを作成します。

    デコレータが以下のエラーを自動的に処理します:
    - ValidationError → 400 Bad Request
    - AuthenticationError → 401 Unauthorized
    - AuthorizationError → 403 Forbidden
    - NotFoundError → 404 Not Found
    - Exception → 500 Internal Server Error
    """
    # try/exceptは不要 - デコレータが処理
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(user)
```

**メリット**:

1. コード重複の排除（DRY原則）
2. 統一的なエラーレスポンス形式
3. ビジネスロジックに集中できる
4. 約60%のコード削減

詳細: [エラーレスポンス](../../04-api-desig./06-error-responses.md#エラーハンドリングデコレータ推奨)

---

## ベストプラクティス

1. **response_modelを必ず指定**
2. **依存性注入を活用**
3. **HTTPステータスコードを適切に設定**
4. **OpenAPIドキュメント用のメタデータを追加**
5. **@handle_service_errors デコレータを使用**（エラーハンドリング統一）

---

次のセクション: [../03-database/01-sqlalchemy-basics.md](../03-database/01-sqlalchemy-basics.md)
