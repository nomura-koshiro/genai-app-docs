"""アプリケーションのカスタム例外."""

from typing import Any


class AppException(Exception):
    """アプリケーション基底例外."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """リソース未検出例外."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(AppException):
    """バリデーションエラー例外."""

    def __init__(self, message: str = "Validation error", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class AuthenticationError(AppException):
    """認証エラー例外."""

    def __init__(
        self, message: str = "Authentication failed", details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AppException):
    """認可エラー例外."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=403, details=details)


class DatabaseError(AppException):
    """データベース操作エラー例外."""

    def __init__(
        self, message: str = "Database operation failed", details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=500, details=details)


class ExternalServiceError(AppException):
    """外部サービスエラー例外."""

    def __init__(
        self, message: str = "External service error", details: dict[str, Any] | None = None
    ):
        super().__init__(message, status_code=502, details=details)
