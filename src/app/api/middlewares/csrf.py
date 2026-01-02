"""CSRF保護ミドルウェア。

このモジュールは、Cross-Site Request Forgery (CSRF) 攻撃からアプリケーションを保護します。

CSRF防御戦略:
    1. **SameSite Cookie属性**: lax または strict を設定し、クロスサイトリクエストでの
       Cookieの送信を制限
    2. **カスタムヘッダー検証**: ブラウザの Same-Origin Policy により、
       クロスオリジンからカスタムヘッダーを付与することは不可能
    3. **トークン比較**: Cookie内のトークンとヘッダー内のトークンを比較

セキュリティモデル:
    - **安全なメソッド** (GET, HEAD, OPTIONS, TRACE): CSRF検証をスキップ
      理由: これらは副作用のない操作とみなされる

    - **API認証** (Bearer token): CSRF検証をスキップ
      理由: APIクライアントはCookieベース認証を使用しない

    - **Cookie認証**: CSRF検証を実施
      理由: ブラウザが自動的にCookieを送信するため、CSRF攻撃のリスクがある

Usage:
    >>> from app.api.middlewares.csrf import CSRFMiddleware
    >>> from fastapi import FastAPI
    >>>
    >>> app = FastAPI()
    >>> app.add_middleware(
    ...     CSRFMiddleware,
    ...     secret_key="your-secret-key",
    ...     cookie_secure=True  # HTTPS環境では True
    ... )

セキュリティ設定:
    - **cookie_secure**: HTTPS環境では必ず True に設定
    - **httponly**: False（JavaScriptからアクセスする必要があるため）
    - **samesite**: "lax"（通常のナビゲーションは許可、フォーム送信は制限）

Note:
    - フロントエンドは、CSRFトークンをCookieから取得し、
      リクエストヘッダー（X-CSRF-Token）に含める必要があります
    - 本番環境では必ず HTTPS を使用し、cookie_secure=True に設定してください
"""

import base64
import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF保護ミドルウェア。

    SameSite Cookie属性とカスタムヘッダー検証による二重防御を実装します。

    Attributes:
        SAFE_METHODS: CSRF検証をスキップする安全なHTTPメソッド
        CSRF_HEADER_NAME: CSRFトークンを含むカスタムヘッダー名
        CSRF_COOKIE_NAME: CSRFトークンを含むCookie名

    Args:
        app: FastAPIアプリケーションインスタンス
        secret_key: CSRF トークン生成用のシークレットキー（HMAC署名に使用）
        cookie_secure: Cookie の Secure 属性（HTTPS環境では True）

    Example:
        >>> app.add_middleware(
        ...     CSRFMiddleware,
        ...     secret_key=settings.SECRET_KEY,
        ...     cookie_secure=not settings.DEBUG
        ... )
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    CSRF_HEADER_NAME = "X-CSRF-Token"
    CSRF_COOKIE_NAME = "csrf_token"

    def __init__(self, app, secret_key: str, cookie_secure: bool = True) -> None:
        """CSRFミドルウェアを初期化します。

        Args:
            app: FastAPIアプリケーションインスタンス
            secret_key: CSRF トークン生成用のシークレットキー
            cookie_secure: Cookie の Secure 属性
        """
        super().__init__(app)
        self.secret_key = secret_key
        self.cookie_secure = cookie_secure

    async def dispatch(self, request: Request, call_next) -> Response:
        """リクエストを処理し、CSRF検証を実行します。

        処理フロー:
            1. 安全なメソッド → CSRFトークンを設定してスキップ
            2. Bearer token認証 → スキップ（APIクライアント）
            3. Cookie認証 → CSRFトークン検証を実施

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェアまたはエンドポイント

        Returns:
            Response: HTTPレスポンス（CSRFトークンCookieを含む）

        Raises:
            HTTPException: CSRFトークンが一致しない場合（403 Forbidden）
        """
        # 1. 安全なメソッドはCSRF検証をスキップ
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            # CSRFトークンをCookieに設定（フロントエンドで使用）
            self._set_csrf_cookie(response, request)
            return response

        # 2. API認証（Bearer token）の場合はCSRFチェックをスキップ
        # 理由: APIクライアントはCookieベース認証を使用しないため、CSRF攻撃のリスクがない
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            response = await call_next(request)
            self._set_csrf_cookie(response, request)
            return response

        # 3. Cookie認証の場合のみCSRFトークン検証
        csrf_cookie = request.cookies.get(self.CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(self.CSRF_HEADER_NAME)

        # Cookieにトークンがある場合は検証必須
        if csrf_cookie:
            if not csrf_header:
                raise HTTPException(
                    status_code=403, detail="CSRF token missing in request header"
                )
            # トークン一致チェック（タイミング攻撃対策）
            if not secrets.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(status_code=403, detail="CSRF token mismatch")

            # 有効期限と署名の検証（HMAC署名と有効期限のサーバー側検証）
            if not self._verify_csrf_token(csrf_cookie):
                raise HTTPException(
                    status_code=403, detail="CSRF token expired or invalid"
                )
        # 初回リクエスト（Cookieなし）の場合は、レスポンスでトークンを設定するだけ

        response = await call_next(request)
        self._set_csrf_cookie(response, request)
        return response

    def _generate_csrf_token(self) -> str:
        """有効期限付きHMAC署名CSRFトークンを生成します。

        トークン構造（base64エンコード前）:
            - timestamp (8 bytes): トークン生成時刻（Unix時間）
            - nonce (16 bytes): ランダムな値（リプレイ攻撃防止）
            - signature (32 bytes): HMAC-SHA256署名

        Returns:
            str: base64エンコードされたCSRFトークン（56バイトのバイナリデータ）

        Security:
            - HMAC-SHA256署名により、トークンの偽造を防止
            - タイムスタンプにより、サーバー側で有効期限を検証可能
            - ランダムnonceにより、同じタイムスタンプでも異なるトークンが生成される
        """
        timestamp = int(time.time())
        nonce = secrets.token_bytes(16)

        # トークンデータ: timestamp(8bytes) + nonce(16bytes)
        token_data = timestamp.to_bytes(8, "big") + nonce

        # HMAC署名（SHA256）
        signature = hmac.new(
            self.secret_key.encode(), token_data, hashlib.sha256
        ).digest()

        # 完全なトークン: データ + 署名
        full_token = token_data + signature

        # URL安全なbase64エンコード
        return base64.urlsafe_b64encode(full_token).decode()

    def _verify_csrf_token(self, token: str) -> bool:
        """CSRFトークンの有効性を検証します（署名と有効期限）。

        検証項目:
            1. トークン形式の妥当性（base64デコード、最小サイズ）
            2. HMAC署名の検証（トークンの改ざんチェック）
            3. 有効期限の検証（1時間以内に生成されたか）

        Args:
            token: 検証対象のCSRFトークン

        Returns:
            bool: トークンが有効な場合True、それ以外はFalse

        Security:
            - secrets.compare_digest によるタイミング攻撃対策
            - 有効期限チェックによるトークン再利用攻撃防止
            - 例外は全てFalseを返す（情報漏洩防止）
        """
        try:
            # base64デコード
            full_token = base64.urlsafe_b64decode(token.encode())

            # 最小サイズチェック（8 + 16 + 32 = 56 bytes）
            if len(full_token) < 56:
                return False

            # トークン構造の分解
            timestamp_bytes = full_token[:8]
            nonce = full_token[8:24]
            signature = full_token[24:]

            # タイムスタンプ復元
            timestamp = int.from_bytes(timestamp_bytes, "big")

            # 有効期限チェック（1時間 = 3600秒）
            current_time = int(time.time())
            if current_time - timestamp > 3600:
                return False

            # 未来のタイムスタンプを拒否（時刻同期問題を考慮して60秒の猶予）
            if timestamp - current_time > 60:
                return False

            # HMAC署名検証
            token_data = timestamp_bytes + nonce
            expected_signature = hmac.new(
                self.secret_key.encode(), token_data, hashlib.sha256
            ).digest()

            # タイミング攻撃対策の署名比較
            return secrets.compare_digest(signature, expected_signature)

        except Exception:
            # デコードエラーやその他の例外は全てFalseを返す
            # エラー詳細を返さないことで情報漏洩を防止
            return False

    def _set_csrf_cookie(self, response: Response, request: Request) -> None:
        """CSRFトークンをCookieに設定します（有効な場合は再利用）。

        トークン再利用ロジック:
            1. 既存のCookieからトークンを取得
            2. トークンが有効（署名OK & 有効期限内）なら再利用
            3. 無効または存在しない場合は新規生成

        セキュリティ設定:
            - httponly=False: JavaScriptからアクセス可能（ヘッダーに含める必要があるため）
            - secure: HTTPS環境では True（盗聴防止）
            - samesite="lax": クロスサイトリクエストでの送信を制限
              ・通常のナビゲーション（GET）は許可
              ・フォーム送信（POST）は同一サイトのみ
            - max_age=3600: ブラウザ側の有効期限（1時間）

        Args:
            response: HTTPレスポンス
            request: HTTPリクエスト（既存トークン取得用）

        Note:
            有効なトークンを再利用することで、以下のメリットがあります：
            - 不要なトークン再生成を防止（パフォーマンス向上）
            - クライアント側でのトークン更新頻度を削減
            - トークンの一貫性を保持
        """
        existing_token = request.cookies.get(self.CSRF_COOKIE_NAME)

        # 既存トークンが有効な場合は再利用、無効または存在しない場合は新規生成
        if existing_token and self._verify_csrf_token(existing_token):
            token = existing_token
        else:
            token = self._generate_csrf_token()

        response.set_cookie(
            key=self.CSRF_COOKIE_NAME,
            value=token,
            httponly=False,  # JavaScriptからアクセス可能にする
            secure=self.cookie_secure,  # HTTPS環境では True
            samesite="lax",  # クロスサイトリクエストでの送信を制限
            max_age=3600,  # 1時間の有効期限（ブラウザ側）
            # domain: 設定しない場合は現在のドメインのみ
            # path: デフォルトは "/" （全パスで有効）
        )
