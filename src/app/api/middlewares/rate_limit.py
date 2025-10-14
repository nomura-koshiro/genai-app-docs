"""レート制限ミドルウェア。"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """リクエストのレート制限用ミドルウェア。"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        """レート制限を初期化します。

        Args:
            app: FastAPIアプリケーション
            calls: 期間ごとに許可されるコール数
            period: 期間（秒単位）
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """レート制限をチェックし、リクエストを処理します。

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラ

        Returns:
            HTTPレスポンス
        """
        # Skip rate limiting in development
        if settings.DEBUG:
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Clean old entries
        current_time = time.time()
        self.clients[client_ip] = [
            timestamp
            for timestamp in self.clients[client_ip]
            if current_time - timestamp < self.period
        ]

        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "details": {
                        "limit": self.calls,
                        "period": self.period,
                        "retry_after": self.period,
                    },
                },
                headers={"Retry-After": str(self.period)},
            )

        # Add current request
        self.clients[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.clients[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))

        return response
