"""集中エラーハンドリングミドルウェア。

このモジュールは、アプリケーション全体で発生する例外を捕捉し、
統一されたJSON形式のエラーレスポンスに変換します。

主な機能:
    1. **カスタム例外処理**: AppExceptionを捕捉し、適切なステータスコードでレスポンス
    2. **予期しない例外処理**: すべての例外を500エラーとして処理
    3. **エラーログ記録**: 構造化ログとしてエラー情報を記録
    4. **統一レスポンス形式**: すべてのエラーを {error, details} 形式で返却

エラーレスポンス形式:
    {
      "error": "エラーメッセージ",
      "details": {
        "追加情報": "値"
      }
    }

使用方法:
    app.main.pyで自動的にミドルウェアスタックに登録されます:
        >>> app.add_middleware(ErrorHandlerMiddleware)

処理される例外タイプ:
    1. AppException（カスタム例外）:
       - NotFoundException: 404
       - ValidationException: 400
       - UnauthorizedException: 401
       - その他のAppExceptionサブクラス

    2. 予期しない例外（Exception）:
       - ValueError, TypeError, AttributeError等
       - すべて500エラーとして処理

Note:
    - エラーログには元の例外トレースバックも含まれます
    - 本番環境では詳細なエラー情報をクライアントに返さないよう注意
    - このミドルウェアは他のミドルウェアより後に登録されます（最後の砦）
"""

from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """集中エラーハンドリング用ミドルウェア。

    アプリケーション全体で発生するすべての例外を捕捉し、
    統一されたJSON形式のエラーレスポンスに変換します。

    例外処理の優先順位:
        1. AppException（カスタム例外） → 適切なHTTPステータスコード
        2. その他の例外 → 500 Internal Server Error

    Note:
        - すべてのエラーレスポンスは {error, details} 形式
        - エラー発生時は必ずログ記録（WARNING or ERROR）
        - ミドルウェアチェーンの最後の砦として機能
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理し、発生した例外を捕捉してエラーレスポンスに変換します。

        実行フロー:
            1. try-exceptブロックでcall_next()を呼び出し
            2. AppException発生時:
               - WARNINGレベルでログ記録
               - exc.status_codeを使用してJSONレスポンス返却
            3. その他の例外発生時:
               - ERRORレベルでログ記録（トレースバック含む）
               - 500エラーとしてJSONレスポンス返却
            4. 例外なし:
               - そのままレスポンス返却

        Args:
            request (Request): HTTPリクエストオブジェクト
                - エラーログのコンテキスト情報として使用
                - url.path: エンドポイントパス
                - method: HTTPメソッド
            call_next (Callable): 次のミドルウェア/ハンドラー
                - 例外が発生する可能性がある

        Returns:
            Response: HTTPレスポンス
                - 正常時: 元のレスポンス
                - エラー時: JSONエラーレスポンス

        Example:
            >>> # カスタム例外の場合
            >>> # サービス層で発生:
            >>> raise NotFoundException("User not found", details={"user_id": 123})
            >>>
            >>> # ログ出力:
            >>> # WARNING - AppException: User not found
            >>> # extra: {
            >>> #   "path": "/api/v1/users/123",
            >>> #   "method": "GET",
            >>> #   "status_code": 404,
            >>> #   "details": {"user_id": 123}
            >>> # }
            >>>
            >>> # レスポンス（HTTP 404）:
            >>> {
            >>>   "error": "User not found",
            >>>   "details": {"user_id": 123}
            >>> }
            >>>
            >>> # 予期しない例外の場合
            >>> # コード内で発生:
            >>> raise ValueError("Invalid input")
            >>>
            >>> # ログ出力:
            >>> # ERROR - Unexpected error: Invalid input
            >>> # （スタックトレース付き）
            >>> # extra: {
            >>> #   "path": "/api/v1/chat",
            >>> #   "method": "POST"
            >>> # }
            >>>
            >>> # レスポンス（HTTP 500）:
            >>> {
            >>>   "error": "Internal server error",
            >>>   "details": {"message": "Invalid input"}
            >>> }

        Note:
            - AppException以外の例外は詳細情報をクライアントに返しません（セキュリティ）
            - logger.exception()により自動的にトレースバックが記録されます
            - 本番環境では500エラーの詳細をログで確認してください
        """
        try:
            response = await call_next(request)
            return response
        except AppException as exc:
            # カスタムアプリケーション例外を処理
            logger.warning(
                f"アプリケーション例外: {exc.message}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                    "details": exc.details,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.message, "details": exc.details},
            )
        except Exception as exc:
            # 予期しない例外を処理
            logger.exception(
                f"予期しないエラー: {str(exc)}",
                extra={"path": request.url.path, "method": request.method},
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "details": {"message": str(exc)},
                },
            )
