"""カスタムミドルウェアモジュール。

このパッケージは、FastAPIアプリケーションで使用されるカスタムミドルウェアを提供します。
すべてのミドルウェアはapp.main.pyで登録され、リクエスト処理パイプラインの一部として機能します。

提供されるミドルウェア:
    1. **LoggingMiddleware**: HTTPリクエスト/レスポンスのロギング
       - すべてのリクエストの開始と完了を記録
       - 処理時間をX-Process-Timeヘッダーに追加
       - 構造化ログ（JSON形式、本番環境）

    2. **PrometheusMetricsMiddleware**: パフォーマンスメトリクス収集
       - リクエスト数、処理時間、サイズをPrometheus形式で記録
       - /metricsエンドポイントから取得可能
       - Grafanaダッシュボードと連携

    3. **RateLimitMiddleware**: レート制限
       - Redisベーススライディングウィンドウアルゴリズム
       - デフォルト: 100リクエスト/60秒
       - クライアント識別: ユーザーID、APIキー、IPアドレス

ミドルウェア実行順序（app_factory.pyでの登録順の逆）:
    リクエスト →
        CORS →
        SecurityHeadersMiddleware →
        RateLimitMiddleware →
        LoggingMiddleware →
        PrometheusMetricsMiddleware →
        エンドポイント処理 →
        Exception Handlers (RFC 9457) →
        レスポンス

使用方法:
    >>> from app.api.middlewares import LoggingMiddleware, RateLimitMiddleware
    >>>
    >>> app.add_middleware(LoggingMiddleware)
    >>> app.add_middleware(RateLimitMiddleware, calls=100, period=60)

エラーハンドリング:
    - エラーハンドリングはミドルウェアではなく、Exception Handlers で実装
    - RFC 9457 (Problem Details for HTTP APIs) 準拠
    - app.api.core.exception_handlers.register_exception_handlers() で登録
    - 詳細は app/api/core/exception_handlers.py を参照

Note:
    - ミドルウェアは後に追加したものが先に実行されます
    - すべてのミドルウェアは非同期（async/await）対応
    - Starlette BaseHTTPMiddlewareを継承
"""

from app.api.middlewares.logging import LoggingMiddleware
from app.api.middlewares.metrics import PrometheusMetricsMiddleware
from app.api.middlewares.rate_limit import RateLimitMiddleware
from app.api.middlewares.security_headers import SecurityHeadersMiddleware

__all__ = [
    "LoggingMiddleware",
    "PrometheusMetricsMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]
