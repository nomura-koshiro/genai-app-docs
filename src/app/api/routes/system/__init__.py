"""システムエンドポイント。

このパッケージには、インフラストラクチャ関連のエンドポイントが含まれています。
これらのエンドポイントはAPIバージョンに依存しない基盤機能を提供します。

提供されるエンドポイント:
    - GET /: ルートエンドポイント（API情報）
    - GET /health: ヘルスチェック（アプリケーションとデータベースの状態確認）
    - GET /metrics: Prometheusメトリクス（パフォーマンス監視用）

使用例:
    >>> # ヘルスチェック
    >>> GET /health
    >>> {"status": "healthy", "database": "connected"}
    >>>
    >>> # メトリクス確認
    >>> GET /metrics
    >>> # HELP http_requests_total Total number of HTTP requests
    >>> # TYPE http_requests_total counter
    >>> http_requests_total{method="GET",endpoint="/health"} 42
"""

from app.api.routes.system.health import router as health_router
from app.api.routes.system.metrics import router as metrics_router
from app.api.routes.system.root import router as root_router

__all__ = ["health_router", "metrics_router", "root_router"]
