# エラーレスポンス

統一されたエラーハンドリングとレスポンスについて説明します。

## RFC 9457準拠のエラーレスポンス

このプロジェクトは、**RFC 9457 Problem Details for HTTP APIs**標準に準拠したエラーレスポンス形式を採用しています。

### RFC 9457とは

RFC 9457は、HTTP APIのエラーレスポンスを標準化するための仕様です。以下の利点があります：

- **標準化**: クライアントが一貫した形式でエラーを処理できる
- **相互運用性**: 異なるAPIでも同じ形式でエラーを扱える
- **デバッグ性**: 詳細な問題情報を構造化して提供できる

### エラーレスポンス形式

**Content-Type**: `application/problem+json`

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "User with ID 12345 was not found",
  "instance": "/api/v1/users/12345",
  "user_id": "12345"
}
```

**必須フィールド**:

| フィールド | 型 | 説明 |
|----------|---|------|
| `type` | string | 問題タイプを識別するURI（デフォルト: "about:blank"） |
| `title` | string | 人間が読める短い要約（HTTPステータスコードに対応） |
| `status` | integer | HTTPステータスコード（100-599） |

**オプションフィールド**:

| フィールド | 型 | 説明 |
|----------|---|------|
| `detail` | string | この問題発生の具体的な説明 |
| `instance` | string | この問題が発生したリクエストパス |
| カスタムフィールド | any | 追加の詳細情報（`user_id`, `field`など） |

### 参考リンク

- [RFC 9457仕様](https://www.rfc-editor.org/rfc/rfc9457.html)

---

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

## RFC 9457準拠の例外ハンドラー

```python
# src/app/api/core/exception_handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException

# HTTPステータスコードからtitleへのマッピング（RFC 9457推奨）
STATUS_CODE_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """RFC 9457準拠のエラーレスポンスを返すグローバルハンドラー。"""
    assert isinstance(exc, AppException), "Expected AppException instance"

    # RFC 9457準拠のレスポンスボディを構築
    problem_details = {
        "type": "about:blank",  # デフォルトの問題タイプURI
        "title": STATUS_CODE_TITLES.get(exc.status_code, "Error"),
        "status": exc.status_code,
        "detail": exc.message,
        "instance": str(request.url.path),  # リクエストパスのみ
    }

    # 追加の詳細情報をマージ（RFC 9457は拡張フィールドを許可）
    if exc.details:
        problem_details.update(exc.details)

    return JSONResponse(
        status_code=exc.status_code,
        content=problem_details,
        media_type="application/problem+json",  # RFC 9457準拠のContent-Type
    )


def register_exception_handlers(app: FastAPI):
    """FastAPIアプリケーションにカスタム例外ハンドラーを登録します。"""
    app.add_exception_handler(AppException, app_exception_handler)


# src/app/main.py
from app.api.core.exception_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

## 使用例

```python
# サービス層
from app.core.exceptions import NotFoundError, ValidationError


class SampleUserService:
    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError(
                "User not found",
                details={"user_id": str(user_id)}
            )
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.repository.get_by_email(user_data.email):
            raise ValidationError(
                "Email already exists",
                details={"email": user_data.email, "field": "email"}
            )
        return await self.repository.create(**user_data.model_dump())


# RFC 9457準拠のエラーレスポンス例
# HTTP 404 Not Found
# Content-Type: application/problem+json
# {
#   "type": "about:blank",
#   "title": "Not Found",
#   "status": 404,
#   "detail": "User not found",
#   "instance": "/api/v1/users/12345678-1234-1234-1234-123456789abc",
#   "user_id": "12345678-1234-1234-1234-123456789abc"
# }
```

---

## エラーハンドリングデコレータ（推奨）

**実装場所**: `src/app/api/decorators.py`

### デコレータパターン

すべてのAPIエンドポイントで統一的なエラーハンドリングを適用するため、
`@handle_service_errors` デコレータを使用します。

```python
# src/app/api/decorators.py
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)

def handle_service_errors[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """サービス層のエラーを統一的にHTTPExceptionに変換するデコレータ。

    変換ルール:
        - ValidationError → 400 Bad Request
        - AuthenticationError → 401 Unauthorized
        - AuthorizationError → 403 Forbidden
        - NotFoundError → 404 Not Found
        - その他のException → 500 Internal Server Error
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": e.message, "details": e.details},
            ) from e
        except AuthenticationError as e:
            raise HTTPException(
                status_code=401,
                detail={"error": e.message, "details": e.details},
            ) from e
        except AuthorizationError as e:
            raise HTTPException(
                status_code=403,
                detail={"error": e.message, "details": e.details},
            ) from e
        except NotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail={"error": e.message, "details": e.details},
            ) from e
        except HTTPException:
            # FastAPIのHTTPExceptionはそのまま再送出
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal server error", "details": None},
            ) from e
    return wrapper
```

### エンドポイントでの使用例

```python
# src/app/api/routes/v1/sample_users.py
from fastapi import APIRouter, status
from app.api.decorators import handle_service_errors
from app.api.core import SampleUserServiceDep
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse

router = APIRouter()

@router.post("", response_model=SampleUserResponse, status_code=status.HTTP_201_CREATED)
@handle_service_errors  # デコレータを適用
async def create_user(
    user_data: SampleUserCreate,
    user_service: SampleUserServiceDep,
) -> SampleUserResponse:
    """新しいユーザーアカウントを作成します。

    デコレータがエラーハンドリングを自動的に行うため、
    try/exceptブロックは不要です。
    """
    # サービス層から例外が発生しても、デコレータが自動的に処理
    user = await user_service.create_user(user_data)
    return SampleUserResponse.model_validate(user)
```

### デコレータのメリット

1. **DRY原則**: エラーハンドリングコードの重複を排除
2. **一貫性**: すべてのエンドポイントで統一的なエラーレスポンス
3. **保守性**: エラーハンドリングロジックを一箇所で管理
4. **可読性**: ビジネスロジックに集中できる（try/exceptノイズなし）

### Before/After比較

**Before（デコレータなし）**:

```python
@router.post("/users")
async def create_user(user_data: UserCreate, service: SampleUserServiceDep):
    try:
        user = await service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        logger.warning(f"Not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**After（デコレータあり）**:

```python
@router.post("/users")
@handle_service_errors  # エラーハンドリングはデコレータが担当
async def create_user(user_data: UserCreate, service: SampleUserServiceDep):
    user = await service.create_user(user_data)
    return UserResponse.model_validate(user)
```

**コード削減**: 約60%のコード削減（16行 → 6行）

---

## 参考リンク

- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Python Decorators](https://peps.python.org/pep-0318/)
