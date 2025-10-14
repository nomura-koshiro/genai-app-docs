# エラーレスポンス

統一されたエラーハンドリングとレスポンスについて説明します。

## カスタム例外

```python
# src/app/core/exceptions.py
from typing import Any


class AppException(Exception):
    """アプリケーション基底例外。"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """リソース未検出例外。"""
    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(AppException):
    """バリデーションエラー例外。"""
    def __init__(self, message: str = "Validation error", details: dict | None = None):
        super().__init__(message, status_code=422, details=details)


class AuthenticationError(AppException):
    """認証エラー例外。"""
    def __init__(self, message: str = "Authentication failed", details: dict | None = None):
        super().__init__(message, status_code=401, details=details)
```

## 例外ハンドラー

```python
# src/app/api/middlewares/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """アプリケーション例外ハンドラー。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )


# src/app/main.py
from app.api.middlewares.error_handler import app_exception_handler
from app.core.exceptions import AppException

app = FastAPI()
app.add_exception_handler(AppException, app_exception_handler)
```

## 使用例

```python
# サービス層
class UserService:
    async def get_user(self, user_id: int) -> User:
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError(
                f"User not found",
                details={"user_id": user_id}
            )
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.repository.get_by_email(user_data.email):
            raise ValidationError(
                "Email already exists",
                details={"email": user_data.email}
            )
        return await self.repository.create(**user_data.model_dump())


# エラーレスポンス例
# {
#   "error": "User not found",
#   "details": {"user_id": 123}
# }
```

## 参考リンク

- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
