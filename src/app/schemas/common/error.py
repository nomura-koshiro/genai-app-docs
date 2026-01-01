"""共通エラーレスポンススキーマ。

このモジュールは、全APIで使用する標準エラーレスポンスを定義します。
"""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


class ErrorDetail(BaseCamelCaseModel):
    """エラー詳細情報。

    Attributes:
        field (str | None): エラーが発生したフィールド名
        message (str): エラーメッセージ
        code (str | None): エラーコード
    """

    field: str | None = Field(default=None, description="エラーが発生したフィールド名")
    message: str = Field(..., description="エラーメッセージ")
    code: str | None = Field(default=None, description="エラーコード")


class ErrorResponse(BaseCamelCaseModel):
    """標準エラーレスポンススキーマ。

    全APIエンドポイントで統一されたエラーレスポンス形式。

    Attributes:
        error (str): エラー種別
        message (str): ユーザー向けエラーメッセージ
        details (list[ErrorDetail] | None): 詳細エラー情報
        request_id (str | None): リクエストID（トレーシング用）
        timestamp (datetime): エラー発生日時
    """

    error: str = Field(..., description="エラー種別")
    message: str = Field(..., description="ユーザー向けエラーメッセージ")
    details: list[ErrorDetail] | None = Field(default=None, description="詳細エラー情報")
    request_id: str | None = Field(default=None, description="リクエストID")
    timestamp: datetime = Field(default_factory=datetime.now, description="エラー発生日時")


class NotFoundErrorResponse(ErrorResponse):
    """リソース未発見エラーレスポンス。

    HTTP 404 エラー用のレスポンス。
    """

    error: str = Field(default="NotFound", description="エラー種別")


class ValidationErrorResponse(ErrorResponse):
    """バリデーションエラーレスポンス。

    HTTP 400/422 エラー用のレスポンス。
    """

    error: str = Field(default="ValidationError", description="エラー種別")


class AuthorizationErrorResponse(ErrorResponse):
    """認可エラーレスポンス。

    HTTP 403 エラー用のレスポンス。
    """

    error: str = Field(default="AuthorizationError", description="エラー種別")


class AuthenticationErrorResponse(ErrorResponse):
    """認証エラーレスポンス。

    HTTP 401 エラー用のレスポンス。
    """

    error: str = Field(default="AuthenticationError", description="エラー種別")


class ConflictErrorResponse(ErrorResponse):
    """競合エラーレスポンス。

    HTTP 409 エラー用のレスポンス。
    """

    error: str = Field(default="ConflictError", description="エラー種別")


class InternalErrorResponse(ErrorResponse):
    """内部エラーレスポンス。

    HTTP 500 エラー用のレスポンス。
    """

    error: str = Field(default="InternalError", description="エラー種別")
    message: str = Field(
        default="サーバー内部でエラーが発生しました",
        description="ユーザー向けエラーメッセージ",
    )
