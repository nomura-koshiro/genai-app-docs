"""エラーハンドリングミドルウェア。"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """集中エラーハンドリング用のミドルウェア。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理し、例外をキャッチします。

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラ

        Returns:
            HTTPレスポンス
        """
        try:
            response = await call_next(request)
            return response
        except AppException as exc:
            # Handle custom application exceptions
            logger.warning(
                f"AppException: {exc.message}",
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
            # Handle unexpected exceptions
            logger.exception(
                f"Unexpected error: {str(exc)}",
                extra={"path": request.url.path, "method": request.method},
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "details": {"message": str(exc)},
                },
            )
