"""HTTPリクエスト/レスポンスのロギングミドルウェア。

このモジュールは、すべてのHTTPリクエストとレスポンスを構造化ログとして記録します。
リクエストの開始時と完了時にログを出力し、処理時間をヘッダーに追加します。

主な機能:
    1. **リクエストログ**: メソッド、パス、クエリパラメータ、クライアントIP
    2. **レスポンスログ**: ステータスコード、処理時間
    3. **処理時間ヘッダー**: X-Process-Time ヘッダーに処理時間を追加

ログ形式:
    開発環境: structlog カラー付きコンソール出力（キー-値ペア）
    本番環境: structlog JSON構造化ログ

使用方法:
    app.main.pyで自動的にミドルウェアスタックに登録されます:
        >>> app.add_middleware(LoggingMiddleware)

ログ出力例:
    リクエスト開始（開発環境）:
        Request started: GET /api/v1/agents/chat method=GET path=/api/v1/agents/chat client=127.0.0.1

    リクエスト完了（開発環境）:
        Request completed: GET /api/v1/agents/chat - 200 method=GET path=/api/v1/agents/chat
        status_code=200 duration=0.234s

    本番環境（JSON）:
        {"event": "Request started: GET /api/v1/agents/chat", "method": "GET", ...}

Note:
    - 機密情報（パスワード、トークン等）はログに含めないよう注意してください
    - 本番環境ではstructlog JSON出力がCloudWatch/ELKなどで集約・分析されます
    - 処理時間はX-Process-Timeヘッダーとしてクライアントにも返されます
    - ログ形式はapp/core/logging.pyのstructlog設定に従います
"""

import time
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTPリクエストとレスポンスをロギングするミドルウェア。

    すべてのHTTPリクエストの開始時と完了時にログを出力し、
    処理時間を計測してX-Process-Timeヘッダーに追加します。

    ミドルウェアチェーン内での実行順序:
        RateLimitMiddleware → LoggingMiddleware → ErrorHandlerMiddleware → ...

    Note:
        - Starlette BaseHTTPMiddlewareを継承
        - 非同期処理に対応（async/await）
        - すべてのエンドポイントに自動適用
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストとレスポンスをログに記録し、処理時間を計測します。

        実行フロー:
            1. 処理開始時刻を記録
            2. リクエスト開始ログを出力（メソッド、パス、IP等）
            3. 次のミドルウェア/ハンドラーを呼び出し
            4. レスポンス取得後、処理時間を計算
            5. リクエスト完了ログを出力（ステータス、処理時間）
            6. X-Process-Timeヘッダーを追加してレスポンス返却

        Args:
            request (Request): FastAPI/Starletteリクエストオブジェクト
                - method: HTTPメソッド（GET, POST等）
                - url: リクエストURL
                - headers: リクエストヘッダー
                - client: クライアント情報（IPアドレス等）
            call_next (Callable): 次のミドルウェアまたはエンドポイントハンドラー
                - 非同期関数（await call_next(request)で呼び出し）

        Returns:
            Response: HTTPレスポンスオブジェクト
                - X-Process-Timeヘッダー付き（処理時間、秒単位）

        Example:
            >>> # リクエスト: GET /api/v1/agents/chat?session_id=123
            >>> # ログ出力（リクエスト開始）:
            >>> # INFO - Request started: GET /api/v1/agents/chat
            >>> # extra: {
            >>> #   "method": "GET",
            >>> #   "path": "/api/v1/agents/chat",
            >>> #   "query_params": "session_id=123",
            >>> #   "client": "192.168.1.100"
            >>> # }
            >>>
            >>> # ログ出力（リクエスト完了）:
            >>> # INFO - Request completed: GET /api/v1/agents/chat - 200
            >>> # extra: {
            >>> #   "method": "GET",
            >>> #   "path": "/api/v1/agents/chat",
            >>> #   "status_code": 200,
            >>> #   "duration": "0.234s"
            >>> # }
            >>>
            >>> # レスポンスヘッダー:
            >>> # X-Process-Time: 0.234

        Note:
            - 処理時間はtime.time()で計測（精度: マイクロ秒）
            - ログはstructlog構造化ログ形式（キー-値ペア）
            - 本番環境ではstructlog JSONフォーマットでログ集約システムに送信
        """
        # タイマーを開始
        start_time = time.time()

        # リクエストをログ記録
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client": request.client.host if request.client else None,
            },
        )

        # リクエストを処理
        response = await call_next(request)

        # 処理時間を計算
        duration = time.time() - start_time

        # レスポンスをログ記録
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": f"{duration:.3f}s",
            },
        )

        # カスタムヘッダーを追加
        response.headers["X-Process-Time"] = str(duration)

        return response
