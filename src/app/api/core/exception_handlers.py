"""RFC 9457準拠のカスタム例外ハンドラー。

このモジュールは、FastAPIアプリケーション全体で発生する例外を捕捉し、
RFC 9457 Problem Details for HTTP APIs標準に準拠したレスポンスに変換します。

主な役割:
    1. **AppException処理**: ビジネスロジック層で発生したカスタム例外の処理
    2. **RFC 9457準拠レスポンス**: 標準化されたエラーレスポンス形式の提供

Reference:
    RFC 9457: https://www.rfc-editor.org/rfc/rfc9457.html

Usage:
    >>> from app.api.exception_handlers import register_exception_handlers
    >>> from fastapi import FastAPI
    >>>
    >>> app = FastAPI()
    >>> register_exception_handlers(app)
"""

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
    """RFC 9457準拠のエラーレスポンスを返すグローバルハンドラー。

    アプリケーション内で発生したAppException（またはそのサブクラス）を捕捉し、
    RFC 9457 Problem Details for HTTP APIs標準に準拠したレスポンスに変換します。

    RFC 9457レスポンス形式:
        {
          "type": "about:blank",
          "title": "Not Found",
          "status": 404,
          "detail": "User with ID 12345 was not found",
          "instance": "/api/v1/users/12345",
          "user_id": "12345"  // カスタムフィールド（exc.detailsから追加）
        }

    Args:
        request (Request): FastAPIリクエストオブジェクト
            - URL、ヘッダー等のリクエスト情報
        exc (Exception): 発生した例外（実行時は AppException のインスタンス）
            - status_code: HTTPステータスコード
            - message: エラーメッセージ（detailフィールドになる）
            - details: 追加のカスタムフィールド

    Returns:
        JSONResponse: RFC 9457準拠のエラーレスポンス
            - Content-Type: application/problem+json
            - ステータスコード: exc.status_code

    Example:
        >>> # サービス層でAppExceptionを発生させる
        >>> from app.core.exceptions import NotFoundError
        >>> raise NotFoundError("User not found", details={"user_id": "12345"})
        >>>
        >>> # このハンドラーが以下のレスポンスを返す
        >>> # HTTP 404 Not Found
        >>> # Content-Type: application/problem+json
        >>> # {
        >>> #   "type": "about:blank",
        >>> #   "title": "Not Found",
        >>> #   "status": 404,
        >>> #   "detail": "User not found",
        >>> #   "instance": "/api/v1/users/12345",
        >>> #   "user_id": "12345"
        >>> # }

    Reference:
        RFC 9457: https://www.rfc-editor.org/rfc/rfc9457.html

    Note:
        - RFC 9457は拡張フィールド（user_id等）の追加を許可しています
        - typeフィールドはデフォルトで"about:blank"（一般的なHTTPエラー）
        - カスタム問題タイプURIは将来的に実装予定
    """
    # FastAPIの型定義に合わせるため Exception 型で受け取るが、
    # 実行時は必ず AppException のインスタンスが渡される
    assert isinstance(exc, AppException), "Expected AppException instance"

    # RFC 9457準拠のレスポンスボディを構築
    problem_details = {
        "type": "about:blank",  # デフォルトの問題タイプURI
        "title": STATUS_CODE_TITLES.get(exc.status_code, "Error"),
        "status": exc.status_code,
        "detail": exc.message,
        "instance": str(request.url.path),  # リクエストパスのみ（クエリパラメータを除く）
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
    """FastAPIアプリケーションにカスタム例外ハンドラーを登録します。

    Args:
        app (FastAPI): FastAPIアプリケーションインスタンス

    Example:
        >>> from fastapi import FastAPI
        >>> from app.api.exception_handlers import register_exception_handlers
        >>>
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(AppException, app_exception_handler)
