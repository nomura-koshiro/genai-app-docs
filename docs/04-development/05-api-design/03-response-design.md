# レスポンス設計

APIレスポンスの統一フォーマットについて説明します。

## 基本的なレスポンス

```python
from pydantic import BaseModel, ConfigDict


class SampleUserResponse(BaseModel):
    """ユーザーレスポンス。"""
    id: int
    email: str
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemyモデルから変換


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス。"""
    message: str


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int):
    # 削除処理
    return MessageResponse(message=f"User {user_id} deleted successfully")
```

## リストレスポンス

```python
from pydantic import BaseModel, ConfigDict


class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンス。"""
    items: list[SampleUserResponse]
    total: int
    skip: int
    limit: int


@router.get("/users", response_model=PaginatedResponse)
async def list_users(skip: int = 0, limit: int = 100):
    users = await service.list_users(skip, limit)
    total = await service.count_users()
    return PaginatedResponse(
        items=[SampleUserResponse.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit
    )
```

## エラーレスポンス

```python
# カスタム例外
class AppException(Exception):
    def __init__(self, message: str, status_code: int, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}


# エラーハンドラー
from fastapi import Request
from fastapi.responses import JSONResponse

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )
```
