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
