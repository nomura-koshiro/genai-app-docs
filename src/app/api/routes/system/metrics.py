"""Prometheusメトリクスエンドポイント。

このモジュールは、Prometheus監視システムが収集可能な形式で
アプリケーションのパフォーマンスメトリクスを公開します。

Endpoints:
    GET /metrics: Prometheusメトリクス
"""

from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """Prometheusメトリクスエンドポイント - アプリケーションのパフォーマンスメトリクスを公開します。

    Prometheus監視システムが収集できる形式（テキストベース）でメトリクスを出力します。
    PrometheusMetricsMiddlewareによって自動収集されたHTTPリクエストの統計情報
    （リクエスト数、レスポンスタイム、エラー率等）を提供します。

    収集されるメトリクス（PrometheusMetricsMiddlewareによる）:
        - http_requests_total: HTTPリクエスト総数（method, endpoint, status_codeでラベリング）
        - http_request_duration_seconds: リクエスト処理時間のヒストグラム
        - http_requests_in_progress: 現在処理中のリクエスト数

    出力形式:
        Prometheus Exposition Format（テキスト形式）
        Content-Type: text/plain; version=0.0.4

    Returns:
        Response: Prometheusメトリクスのテキストレスポンス
            - メトリクス名、ラベル、値のリスト

    Example:
        >>> # cURLでアクセス
        >>> $ curl http://localhost:8000/metrics
        >>> # HELP http_requests_total Total HTTP requests
        >>> # TYPE http_requests_total counter
        >>> http_requests_total{method="GET",endpoint="/health",status_code="200"} 42.0
        >>> http_requests_total{method="POST",endpoint="/api/v1/agents/chat",status_code="200"} 15.0
        >>> # HELP http_request_duration_seconds HTTP request duration
        >>> # TYPE http_request_duration_seconds histogram
        >>> http_request_duration_seconds_bucket{le="0.1"} 50.0
        >>> http_request_duration_seconds_bucket{le="0.5"} 55.0
        >>> http_request_duration_seconds_sum 12.5
        >>> http_request_duration_seconds_count 57.0

    Note:
        - 認証不要のパブリックエンドポイントです
        - Prometheusサーバーの設定例（prometheus.yml）:
          ```yaml
          scrape_configs:
            - job_name: 'fastapi-app'
              static_configs:
                - targets: ['localhost:8000']
              metrics_path: '/metrics'
          ```
        - Grafanaダッシュボードと連携して可視化できます
        - セキュリティ: 本番環境では認証を追加することを推奨します
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
