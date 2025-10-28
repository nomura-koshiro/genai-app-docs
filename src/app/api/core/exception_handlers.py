"""カスタム例外ハンドラー。

このモジュールは、FastAPIアプリケーション全体で発生する例外を捕捉し、
統一的なJSON形式のレスポンスに変換します。

主な役割:
    1. **AppException処理**: ビジネスロジック層で発生したカスタム例外の処理
    2. **統一エラーレスポンス**: 一貫したエラーレスポンス形式の提供

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


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """カスタムアプリケーション例外（AppException）のグローバルハンドラー。

    アプリケーション内で発生したAppException（またはそのサブクラス）を捕捉し、
    適切なHTTPレスポンスに変換します。ビジネスロジック層で発生した例外を
    統一的なJSON形式でクライアントに返します。

    処理フロー:
        1. AppExceptionが発生
        2. このハンドラーが捕捉
        3. status_code、error、detailsをJSONレスポンスに変換
        4. クライアントに返却

    Args:
        request (Request): FastAPIリクエストオブジェクト
            - 現在のリクエスト情報（URL、ヘッダー等）
        exc (Exception): 発生した例外（実行時は AppException のインスタンス）
            - status_code: HTTPステータスコード（例: 400, 404, 500）
            - message: エラーメッセージ
            - details: 追加のエラー詳細（辞書形式）

    Returns:
        JSONResponse: JSON形式のエラーレスポンス
            {
              "error": "エラーメッセージ",
              "details": {"key": "value"}  // オプション
            }

    Example:
        >>> # サービス層でAppExceptionを発生させる
        >>> from app.core.exceptions import NotFoundException
        >>> raise NotFoundException("User not found", details={"user_id": 123})
        >>>
        >>> # このハンドラーが捕捉し、以下のレスポンスを返す
        >>> # HTTP 404 Not Found
        >>> # {
        >>> #   "error": "User not found",
        >>> #   "details": {"user_id": 123}
        >>> # }

    Note:
        - AppException以外の例外（ValueError等）は ErrorHandlerMiddleware で処理されます
        - ビジネスロジックでは raise AppException を使用してください
        - このハンドラーは @app.exception_handler デコレータで自動登録されます
        - 型アノテーションは Exception ですが、実行時は必ず AppException が渡されます
    """
    # FastAPIの型定義に合わせるため Exception 型で受け取るが、
    # 実行時は必ず AppException のインスタンスが渡される
    assert isinstance(exc, AppException), "Expected AppException instance"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
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
