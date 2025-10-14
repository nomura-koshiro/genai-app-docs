"""Prometheusメトリクスミドルウェア。"""

import time
from typing import Callable

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# HTTPメトリクス
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)

# データベースメトリクス
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)

db_connections_active = Counter(
    "db_connections_active",
    "Active database connections",
)

# アプリケーション固有のメトリクス
chat_messages_total = Counter(
    "chat_messages_total",
    "Total chat messages processed",
    ["role"],  # user, assistant
)

file_uploads_total = Counter(
    "file_uploads_total",
    "Total files uploaded",
    ["content_type"],
)

file_upload_size_bytes = Histogram(
    "file_upload_size_bytes",
    "File upload size in bytes",
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Prometheusメトリクス収集ミドルウェア。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理し、メトリクスを記録."""
        # リクエストサイズを記録
        request_size = int(request.headers.get("content-length", 0))
        method = request.method
        path = request.url.path

        # エンドポイントパスを正規化（パスパラメータを除く）
        endpoint = self._normalize_path(path)

        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(
            request_size
        )

        # リクエスト処理時間を計測
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # エラー発生時もメトリクスを記録
            status_code = 500
            raise
        finally:
            # 処理時間を記録
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            # リクエスト総数を記録
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()

        # レスポンスサイズを記録
        response_size = int(response.headers.get("content-length", 0))
        http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(
            response_size
        )

        return response

    def _normalize_path(self, path: str) -> str:
        """パスパラメータを正規化してエンドポイントパスを取得.

        例: /api/users/123 -> /api/users/{id}
        """
        # 簡易的な実装（本番環境ではルーティング情報を使用すべき）
        parts = path.split("/")
        normalized_parts = []

        for part in parts:
            if part and part.isdigit():
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)

        return "/".join(normalized_parts)
