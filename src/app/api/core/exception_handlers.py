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
from app.core.logging import get_logger

logger = get_logger(__name__)

# HTTPステータスコードからtitleへのマッピング（RFC 9457推奨）
STATUS_CODE_TITLES = {
    # Client errors (4xx)
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    # Server errors (5xx)
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
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

    # 例外をログに記録
    logger.warning(
        "アプリケーション例外発生",
        exc_type=type(exc).__name__,
        status_code=exc.status_code,
        message=exc.message,
        path=str(request.url.path),
        details=exc.details,
    )

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


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全ての予期しない例外を捕捉する最終防衛線ハンドラー。

    AppExceptionでラップされていない例外をキャッチし、
    内部エラーとして適切に処理します。これにより、未処理の例外が
    クライアントに漏洩することを防ぎます。

    Args:
        request (Request): FastAPIリクエストオブジェクト
        exc (Exception): 予期しない例外

    Returns:
        JSONResponse: RFC 9457準拠の500エラーレスポンス

    Example:
        >>> # 予期しない例外が発生した場合
        >>> raise ValueError("Unexpected error")
        >>>
        >>> # このハンドラーが以下のレスポンスを返す
        >>> # HTTP 500 Internal Server Error
        >>> # {
        >>> #   "type": "about:blank",
        >>> #   "title": "Internal Server Error",
        >>> #   "status": 500,
        >>> #   "detail": "内部エラーが発生しました",
        >>> #   "instance": "/api/v1/endpoint"
        >>> # }

    Note:
        - 本番環境では詳細なエラーメッセージを隠蔽します（セキュリティ）
        - 開発環境では詳細なエラーメッセージを表示します（デバッグ用）
        - すべての例外は構造化ログに記録されます
    """
    from app.core.config import settings

    # 詳細なログを記録（本番環境でも記録）
    logger.exception(
        "予期しない例外が発生しました",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        path=str(request.url.path),
        method=request.method,
    )

    # 本番環境では詳細を隠す、開発環境では表示
    detail = str(exc) if settings.DEBUG else "内部エラーが発生しました"

    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": detail,
            "instance": str(request.url.path),
        },
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """FastAPIアプリケーションにカスタム例外ハンドラーを登録します。

    この関数は以下のハンドラーを登録します：
    1. AppException用ハンドラー: ビジネスロジック層の例外処理
    2. グローバル例外ハンドラー: 予期しない例外の最終防衛線

    Args:
        app (FastAPI): FastAPIアプリケーションインスタンス

    Example:
        >>> from fastapi import FastAPI
        >>> from app.api.exception_handlers import register_exception_handlers
        >>>
        >>> app = FastAPI()
        >>> register_exception_handlers(app)

    Note:
        - ハンドラーの登録順序は重要です
        - より具体的な例外（AppException）を先に登録
        - 最後に汎用的な例外（Exception）を登録
    """
    # AppException用ハンドラー（優先）
    app.add_exception_handler(AppException, app_exception_handler)
    # 全ての例外をキャッチ（最終防衛線）
    app.add_exception_handler(Exception, global_exception_handler)
