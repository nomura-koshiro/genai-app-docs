# API設計ガイドライン

## RESTful原則

- **リソース指向**: URL はリソースを表現
- **HTTPメソッド**: GET/POST/PUT/DELETE を適切に使用
- **ステータスコード**: 適切なHTTPステータスコードを返却
- **統一レスポンス**: 一貫したレスポンス形式

## URL設計

| 操作 | メソッド | URL | 説明 |
|------|----------|-----|------|
| 一覧取得 | GET | `/api/v1/users` | ユーザー一覧 |
| 詳細取得 | GET | `/api/v1/users/{id}` | 特定ユーザー |
| 作成 | POST | `/api/v1/users` | ユーザー作成 |
| 更新 | PUT | `/api/v1/users/{id}` | ユーザー更新 |
| 削除 | DELETE | `/api/v1/users/{id}` | ユーザー削除 |

## ステータスコード

| コード | 説明 | 使用場面 |
|--------|------|----------|
| 200 | OK | 正常なGET/PUT/DELETE |
| 201 | Created | POST成功 |
| 204 | No Content | 削除成功（レスポンスなし） |
| 400 | Bad Request | 不正なリクエスト |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | 認可エラー |
| 404 | Not Found | リソースなし |
| 422 | Unprocessable Entity | バリデーションエラー |
| 500 | Internal Server Error | サーバーエラー |

## エンドポイント実装

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_service import UserService

router = APIRouter()

@router.get("/", response_model=List[User])
def get_users(
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> List[User]:
    """
    ユーザー一覧を取得

    - **skip**: スキップするレコード数
    - **limit**: 取得する最大レコード数
    """
    service = UserService(db)
    return service.get_multi(skip=skip, limit=limit)

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user = Depends(deps.get_current_superuser),
) -> User:
    """
    新しいユーザーを作成

    - **user_in**: ユーザー作成データ
    """
    service = UserService(db)
    return service.create(user_in)

@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> User:
    """
    IDによるユーザー取得

    - **user_id**: ユーザーID
    """
    service = UserService(db)
    user = service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
```

## レスポンス形式

### 成功レスポンス

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 一覧レスポンス

```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

### エラーレスポンス（RFC 9457準拠）

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "User not found",
  "instance": "/api/v1/users/999"
}
```

## バリデーション

```python
from pydantic import BaseModel, Field, EmailStr, field_validator

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(..., description="有効なメールアドレス")
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字が必要です')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字が必要です')
        return v
```

## ページネーション

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool
```

## 認証・認可

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """JWTトークンからユーザーを取得"""
    ...

def get_current_active_user(current_user = Depends(get_current_user)):
    """アクティブなユーザーのみ許可"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_superuser(current_user = Depends(get_current_user)):
    """管理者ユーザーのみ許可"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
```

## ドキュメント参照

詳細は以下のドキュメントを参照：

- [API概要](docs/developer-guide/04-development/05-api-design/01-api-overview.md)
- [エンドポイント設計](docs/developer-guide/04-development/05-api-design/02-endpoint-design.md)
- [バリデーション](docs/developer-guide/04-development/05-api-design/03-validation.md)
- [レスポンス設計](docs/developer-guide/04-development/05-api-design/04-response-design.md)
- [ページネーション](docs/developer-guide/04-development/05-api-design/05-pagination.md)
- [エラーレスポンス](docs/developer-guide/04-development/05-api-design/06-error-responses.md)
- [API仕様書](docs/specifications/07-api/01-api-specifications.md)
- [OpenAPI](docs/api/openapi.json)
