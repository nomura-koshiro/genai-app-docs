"""カスタムミドルウェアモジュール。

このパッケージは、FastAPIアプリケーションで使用されるカスタムミドルウェアを提供します。
すべてのミドルウェアはapp.main.pyで登録され、リクエスト処理パイプラインの一部として機能します。

提供されるミドルウェア:
    1. **LoggingMiddleware**: HTTPリクエスト/レスポンスのロギング
       - すべてのリクエストの開始と完了を記録
       - 処理時間をX-Process-Timeヘッダーに追加
       - 構造化ログ（JSON形式、本番環境）

    2. **ErrorHandlerMiddleware**: 集中エラーハンドリング
       - AppExceptionを適切なHTTPステータスコードに変換
       - 予期しない例外を500エラーとして処理
       - すべてのエラーを統一JSON形式で返却

    3. **PrometheusMetricsMiddleware**: パフォーマンスメトリクス収集
       - リクエスト数、処理時間、サイズをPrometheus形式で記録
       - /metricsエンドポイントから取得可能
       - Grafanaダッシュボードと連携

    4. **RateLimitMiddleware**: レート制限
       - Redisベーススライディングウィンドウアルゴリズム
       - デフォルト: 100リクエスト/60秒
       - クライアント識別: ユーザーID、APIキー、IPアドレス

ミドルウェア実行順序（app.main.pyでの登録順の逆）:
    リクエスト →
        CORS →
        RateLimitMiddleware →
        LoggingMiddleware →
        ErrorHandlerMiddleware →
        PrometheusMetricsMiddleware →
        エンドポイント処理

使用方法:
    >>> from app.api.middlewares import LoggingMiddleware, RateLimitMiddleware
    >>>
    >>> app.add_middleware(LoggingMiddleware)
    >>> app.add_middleware(RateLimitMiddleware, calls=100, period=60)

Note:
    - ミドルウェアは後に追加したものが先に実行されます
    - すべてのミドルウェアは非同期（async/await）対応
    - Starlette BaseHTTPMiddlewareを継承
"""

from app.api.middlewares.error_handler import ErrorHandlerMiddleware
from app.api.middlewares.logging import LoggingMiddleware
from app.api.middlewares.metrics import PrometheusMetricsMiddleware
from app.api.middlewares.rate_limit import RateLimitMiddleware
from app.api.middlewares.security_headers import SecurityHeadersMiddleware

__all__ = [
    "ErrorHandlerMiddleware",
    "LoggingMiddleware",
    "PrometheusMetricsMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]
