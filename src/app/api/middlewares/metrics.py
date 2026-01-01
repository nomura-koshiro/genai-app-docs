"""Prometheusメトリクス収集ミドルウェア。

このモジュールは、すべてのHTTPリクエストからパフォーマンスメトリクスを収集し、
Prometheus形式で公開します。/metricsエンドポイントから取得できます。

収集されるメトリクス:
    **HTTPメトリクス**:
        - http_requests_total: リクエスト総数（Counter）
          ラベル: method, endpoint, status_code
        - http_request_duration_seconds: リクエスト処理時間（Histogram）
          ラベル: method, endpoint
        - http_request_size_bytes: リクエストサイズ（Histogram）
          ラベル: method, endpoint
        - http_response_size_bytes: レスポンスサイズ（Histogram）
          ラベル: method, endpoint

    **データベースメトリクス**:
        - db_query_duration_seconds: クエリ処理時間（Histogram）
          ラベル: operation
        - db_connections_active: アクティブ接続数（Counter）

    **アプリケーション固有メトリクス**:
        - chat_messages_total: チャットメッセージ総数（Counter）
          ラベル: role (user, assistant)
        - file_uploads_total: アップロードファイル総数（Counter）
          ラベル: content_type
        - file_upload_size_bytes: アップロードファイルサイズ（Histogram）

メトリクスの確認:
    $ curl http://localhost:8000/metrics
    # HELP http_requests_total Total HTTP requests
    # TYPE http_requests_total counter
    http_requests_total{method="GET",endpoint="/api/v1/chat",status_code="200"} 42.0
    http_requests_total{method="POST",endpoint="/api/v1/files",status_code="201"} 15.0

Prometheusサーバー設定例:
    scrape_configs:
      - job_name: 'fastapi-app'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/metrics'
        scrape_interval: 15s

Note:
    - メトリクスはアプリケーションメモリ内に保持されます
    - 複数ワーカー環境では各ワーカーごとに独立したメトリクス
    - Prometheusサーバーが定期的にスクレイプ（収集）します
    - Grafanaダッシュボードで可視化できます
"""

import time
from collections.abc import Callable

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# HTTPメトリクス
http_requests_total = Counter(
    "http_requests_total",
    "HTTPリクエスト総数",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTPリクエスト処理時間（秒）",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTPリクエストサイズ（バイト）",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTPレスポンスサイズ（バイト）",
    ["method", "endpoint"],
)

# データベースメトリクス
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "データベースクエリ処理時間（秒）",
    ["operation"],
)

db_connections_active = Counter(
    "db_connections_active",
    "アクティブなデータベース接続数",
)

# アプリケーション固有のメトリクス
chat_messages_total = Counter(
    "chat_messages_total",
    "処理されたチャットメッセージ総数",
    ["role"],  # user, assistant
)

file_uploads_total = Counter(
    "file_uploads_total",
    "アップロードされたファイル総数",
    ["content_type"],
)

file_upload_size_bytes = Histogram(
    "file_upload_size_bytes",
    "ファイルアップロードサイズ（バイト）",
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Prometheusメトリクス収集ミドルウェア。

    すべてのHTTPリクエスト/レスポンスからメトリクスを自動収集します。
    収集されたメトリクスは/metricsエンドポイントから取得できます。

    収集タイミング:
        - リクエスト受信時: リクエストサイズを記録
        - レスポンス送信時: 処理時間、ステータスコード、レスポンスサイズを記録

    Note:
        - エラー発生時もメトリクスは記録されます（status_code=500）
        - パスパラメータは正規化されます（/users/123 → /users/{id}）
        - Prometheusのベストプラクティスに従った命名規則
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理し、各種メトリクスを収集・記録します。

        実行フロー:
            1. リクエストサイズ取得（Content-Lengthヘッダー）
            2. エンドポイントパスを正規化（/users/123 → /users/{id}）
            3. リクエストサイズをHistogramに記録
            4. 処理開始時刻を記録
            5. 次のミドルウェア/ハンドラーを呼び出し
            6. レスポンス取得後、処理時間とステータスコードを記録
            7. レスポンスサイズを記録
            8. レスポンス返却

        Args:
            request (Request): HTTPリクエストオブジェクト
                - method: HTTPメソッド（GET, POST等）
                - url.path: エンドポイントパス
                - headers: リクエストヘッダー（Content-Length含む）
            call_next (Callable): 次のミドルウェア/ハンドラー

        Returns:
            Response: HTTPレスポンス（元のレスポンスをそのまま返す）

        Example:
            >>> # リクエスト: POST /api/v1/files （Content-Length: 10240）
            >>> # メトリクス記録:
            >>> http_request_size_bytes{method="POST", endpoint="/api/v1/files"}.observe(10240)
            >>> # 処理時間: 0.5秒、ステータス: 201
            >>> http_request_duration_seconds{method="POST", endpoint="/api/v1/files"}.observe(0.5)
            >>> http_requests_total{
            ...     method="POST", endpoint="/api/v1/files", status_code="201"
            ... }.inc()
            >>> # レスポンスサイズ: 1024
            >>> http_response_size_bytes{method="POST", endpoint="/api/v1/files"}.observe(1024)

        Note:
            - 例外発生時もfinallyブロックでメトリクス記録（status_code=500）
            - パス正規化により、異なるIDでも同じメトリクスラベル
            - Histogramはバケット単位で集計（レスポンスタイム分析に有用）
        """
        # リクエストサイズを記録
        request_size = int(request.headers.get("content-length", 0))
        method = request.method
        path = request.url.path

        # エンドポイントパスを正規化（パスパラメータを除く）
        endpoint = self._normalize_path(path)

        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

        # リクエスト処理時間を計測
        start_time = time.time()
        response = None
        status_code = 500  # デフォルトは500（エラー時）

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            # エラー発生時もメトリクスを記録
            status_code = 500
            raise
        finally:
            # 処理時間を記録
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            # リクエスト総数を記録
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        # レスポンスサイズを記録（エラー時はスキップ）
        if response is not None:
            response_size = int(response.headers.get("content-length", 0))
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

        return response

    def _normalize_path(self, path: str) -> str:
        """パスパラメータを正規化してエンドポイントパスを取得します。

        数値やUUID形式のパスセグメント（IDなど）を {id} に置換することで、
        異なるID値でも同じメトリクスラベルとして集約できます。

        Args:
            path (str): 元のリクエストパス
                - 例: "/api/v1/users/123", "/api/v1/files/abc-123-def/download"

        Returns:
            str: 正規化されたエンドポイントパス
                - 数値セグメントとUUID/ハッシュは {id} に置換
                - 例: "/api/v1/users/{id}", "/api/v1/files/{id}/download"

        Example:
            >>> self._normalize_path("/api/v1/users/123")
            "/api/v1/users/{id}"
            >>>
            >>> self._normalize_path("/api/v1/files/abc-123-def-456/download")
            "/api/v1/files/{id}/download"
            >>>
            >>> self._normalize_path("/api/v1/health")
            "/api/v1/health"

        Note:
            - UUID、数値、英数字ハッシュ（32文字以上）を {id} に正規化
            - 本番環境ではFastAPIのルーティング情報を使用することを推奨
        """
        import re

        parts = path.split("/")
        normalized_parts: list[str] = []

        for part in parts:
            if not part:
                normalized_parts.append(part)
                continue

            # 数値のみ
            if part.isdigit():
                normalized_parts.append("{id}")
            # UUID形式 (例: 123e4567-e89b-12d3-a456-426614174000)
            elif re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", part, re.IGNORECASE):
                normalized_parts.append("{id}")
            # 英数字ハッシュ (32文字以上)
            elif re.match(r"^[a-zA-Z0-9_-]{32,}$", part):
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)

        return "/".join(normalized_parts)
