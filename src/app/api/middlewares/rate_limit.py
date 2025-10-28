"""Redisベースのレート制限ミドルウェア。

このモジュールは、スライディングウィンドウアルゴリズムを使用して
リクエストレート制限を実装します。複数ワーカー環境と分散環境に対応しています。

主な機能:
    1. **スライディングウィンドウ**: 固定ウィンドウより精度が高い
    2. **クライアント識別**: ユーザーID、APIキー、IPアドレスで識別
    3. **Redis使用**: 複数ワーカー/サーバー間で共有
    4. **グレースフルデグラデーション**: Redis障害時は制限をスキップ

レート制限の仕組み:
    - デフォルト: 100リクエスト/60秒
    - Redis Sorted Setを使用してタイムスタンプ管理
    - 期間外のリクエストは自動削除

クライアント識別の優先順位:
    1. 認証済みユーザーのuser_id
    2. X-API-Keyヘッダー（SHA256ハッシュ化）
    3. IPアドレス（X-Forwarded-For対応）

レート制限超過時のレスポンス:
    HTTP 429 Too Many Requests
    {
      "error": "Rate limit exceeded",
      "details": {
        "limit": 100,
        "period": 60,
        "retry_after": 60
      }
    }
    Headers:
      Retry-After: 60

レート制限ヘッダー（すべてのレスポンスに追加）:
    - X-RateLimit-Limit: リクエスト制限数
    - X-RateLimit-Remaining: 残りリクエスト数
    - X-RateLimit-Reset: リセット時刻（Unixタイムスタンプ）

Note:
    - 開発環境（DEBUG=True）では制限は無効化されます
    - Redis接続エラー時は制限をスキップします（可用性優先）
    - プロキシ経由の場合はX-Forwarded-Forヘッダーを使用してください
"""

import hashlib
import time
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache_manager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redisベースのリクエストレート制限ミドルウェア。

    スライディングウィンドウアルゴリズムを使用してレート制限を実装します。
    Redis Sorted Setでタイムスタンプ付きリクエストを管理し、
    複数ワーカー/サーバー環境でも正確に動作します。

    アルゴリズム:
        1. 現在のウィンドウ開始時刻を計算（現在時刻 - period）
        2. ウィンドウ外の古いリクエストを削除（ZREMRANGEBYSCORE）
        3. 現在のリクエスト数をカウント（ZCARD）
        4. 制限超過チェック
        5. 新しいリクエストを追加（ZADD）
        6. TTL設定（EXPIRE）

    Note:
        - Redis Sorted Set使用（key: rate_limit:{client_id}, score: timestamp）
        - 開発環境では自動的に無効化
        - Redis障害時はグレースフルにスキップ
    """

    def __init__(self, app, calls: int = 100, period: int = 60):
        """レート制限を初期化します。

        Args:
            app: FastAPIアプリケーションインスタンス
                - BaseHTTPMiddlewareに渡される
            calls (int): 期間ごとに許可されるリクエスト数
                - デフォルト: 100
                - 例: calls=100で100リクエスト/periodまで許可
            period (int): レート制限の期間（秒単位）
                - デフォルト: 60
                - 例: period=60で60秒間のウィンドウ

        Example:
            >>> # 厳しい制限: 10リクエスト/分
            >>> app.add_middleware(RateLimitMiddleware, calls=10, period=60)
            >>>
            >>> # 緩い制限: 1000リクエスト/10分
            >>> app.add_middleware(RateLimitMiddleware, calls=1000, period=600)

        Note:
            - main.pyでは calls=100, period=60 で登録されています
            - 本番環境では適切な値に調整してください
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        # Redisが利用できない場合のインメモリフォールバック
        # 形式: {client_id: [timestamp1, timestamp2, ...]}
        self._memory_store: dict[str, list[float]] = {}

    def _get_client_identifier(self, request: Request) -> str:
        """クライアント識別子を取得します。

        リクエストからクライアントを一意に識別するための文字列を生成します。
        複数の識別方法を優先順位に従って試行します。

        優先順位:
            1. **認証済みユーザー**: request.state.user.id
               → フォーマット: "user:{user_id}"
               → 最も信頼性が高い識別子

            2. **APIキー**: X-API-Keyヘッダー
               → フォーマット: "apikey:{SHA256ハッシュ}"
               → セキュリティのためハッシュ化

            3. **IPアドレス**: request.client.host または X-Forwarded-For
               → フォーマット: "ip:{ip_address}"
               → プロキシ経由の場合は実IPを取得

        Args:
            request (Request): HTTPリクエストオブジェクト
                - state.user: 認証済みユーザー（存在する場合）
                - headers: X-API-Key, X-Forwarded-Forヘッダー
                - client.host: クライアントIPアドレス

        Returns:
            str: クライアント識別子
                - 形式: "{type}:{value}"
                - 例: "user:123", "apikey:abc...", "ip:192.168.1.100"

        Example:
            >>> # 認証済みユーザーの場合
            >>> request.state.user = User(id=123)
            >>> self._get_client_identifier(request)
            "user:123"
            >>>
            >>> # APIキーの場合
            >>> request.headers["X-API-Key"] = "secret-key-123"
            >>> self._get_client_identifier(request)
            "apikey:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
            >>>
            >>> # プロキシ経由IPの場合
            >>> request.headers["X-Forwarded-For"] = "203.0.113.1, 198.51.100.1"
            >>> self._get_client_identifier(request)
            "ip:203.0.113.1"

        Note:
            - APIキーはSHA256でハッシュ化されます（ログ漏洩対策）
            - X-Forwarded-Forの最初のIPが実クライアントIP
            - プロキシ設定が正しくないと誤ったIPが取得される可能性があります
        """
        # 認証済みユーザーの場合はuser_idを使用
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # プロキシ経由の場合は X-Forwarded-For を確認
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 最初のIPアドレスを取得（クライアントの実IP）
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # API キーがある場合は優先
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()}"

        return f"ip:{client_ip}"

    def _check_rate_limit_memory(self, client_identifier: str, current_time: float) -> tuple[bool, int]:
        """インメモリストアを使用してレート制限をチェックします。

        Redisが利用できない場合のフォールバック機能です。
        シンプルなスライディングウィンドウアルゴリズムを実装しています。

        警告:
            - 複数ワーカー間で共有されません
            - サーバー再起動でリセットされます
            - メモリ使用量が増加する可能性があります

        Args:
            client_identifier (str): クライアント識別子
            current_time (float): 現在のタイムスタンプ

        Returns:
            tuple[bool, int]: (制限超過か, 現在のリクエスト数)
                - True: 制限超過
                - False: 制限内
        """
        # 古いエントリをクリーンアップ
        window_start = current_time - self.period
        if client_identifier in self._memory_store:
            self._memory_store[client_identifier] = [ts for ts in self._memory_store[client_identifier] if ts > window_start]

        # 現在のリクエスト数を取得
        request_count = len(self._memory_store.get(client_identifier, []))

        # 制限チェック
        if request_count >= self.calls:
            return True, request_count

        # 新しいリクエストを追加
        if client_identifier not in self._memory_store:
            self._memory_store[client_identifier] = []
        self._memory_store[client_identifier].append(current_time)

        return False, request_count

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """レート制限をチェックし、超過していなければリクエストを処理します。

        実行フロー:
            1. 開発環境チェック（DEBUG=Trueなら制限スキップ）
            2. クライアント識別子を取得
            3. Redisキー生成（rate_limit:{client_id}）
            4. スライディングウィンドウで古いエントリ削除
            5. 現在のリクエスト数をカウント
            6. 制限超過チェック:
               - 超過: HTTP 429エラー返却
               - OK: 新しいリクエストをRedisに追加
            7. レスポンスにレート制限ヘッダーを追加
            8. レスポンス返却

        Args:
            request (Request): HTTPリクエストオブジェクト
            call_next (Callable): 次のミドルウェア/ハンドラー

        Returns:
            Response: HTTPレスポンス
                - 制限内: 元のレスポンス + レート制限ヘッダー
                - 制限超過: HTTP 429 + Retry-Afterヘッダー

        Example:
            >>> # 正常なリクエスト（50/100）
            >>> # レスポンスヘッダー:
            >>> # X-RateLimit-Limit: 100
            >>> # X-RateLimit-Remaining: 50
            >>> # X-RateLimit-Reset: 1634567890
            >>>
            >>> # 制限超過（101/100）
            >>> # レスポンス（HTTP 429）:
            >>> {
            >>>   "error": "Rate limit exceeded",
            >>>   "details": {
            >>>     "limit": 100,
            >>>     "period": 60,
            >>>     "retry_after": 60
            >>>   }
            >>> }
            >>> # ヘッダー:
            >>> # Retry-After: 60

        Note:
            - 開発環境（DEBUG=True）では自動的にスキップ
            - Redis接続エラー時もスキップ（可用性優先）
            - スライディングウィンドウ: 固定ウィンドウより精度が高い
            - Redis Sorted Set使用: 複数ワーカー/サーバー間で共有
        """
        # 開発環境ではレート制限をスキップ
        if settings.DEBUG:
            return await call_next(request)

        # クライアント識別子を取得
        client_identifier = self._get_client_identifier(request)
        cache_key = f"rate_limit:{client_identifier}"

        # Redisから現在のカウントを取得
        current_time = int(time.time())
        window_start = current_time - self.period

        try:
            # Redisが利用できない場合はインメモリフォールバックを使用
            if not cache_manager._redis:
                logger.warning("Redisが利用できません。インメモリレート制限にフォールバックします")
                is_limited, request_count = self._check_rate_limit_memory(client_identifier, current_time)
                if is_limited:
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
                response = await call_next(request)
                remaining = max(0, self.calls - request_count - 1)
                response.headers["X-RateLimit-Limit"] = str(self.calls)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
                return response

            # Redis Sorted Setを使用したスライディングウィンドウアルゴリズム
            # 古いエントリを削除
            await cache_manager._redis.zremrangebyscore(cache_key, 0, window_start)

            # 現在のリクエスト数をカウント
            request_count = await cache_manager._redis.zcard(cache_key)

            if request_count >= self.calls:
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

            # 現在のリクエストを追加
            request_id = f"{current_time}:{hashlib.sha256(str(time.time()).encode()).hexdigest()}"
            await cache_manager._redis.zadd(cache_key, {request_id: current_time})
            await cache_manager._redis.expire(cache_key, self.period)

            # リクエストを処理
            response = await call_next(request)

            # レート制限ヘッダーを追加
            remaining = max(0, self.calls - request_count - 1)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(current_time + self.period)

            return response

        except Exception as e:
            logger.exception(
                "レート制限エラー",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            # エラー時はインメモリフォールバックを使用
            logger.warning("Redisエラー、インメモリレート制限にフォールバックします")
            is_limited, request_count = self._check_rate_limit_memory(client_identifier, current_time)
            if is_limited:
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
            response = await call_next(request)
            remaining = max(0, self.calls - request_count - 1)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
            return response
