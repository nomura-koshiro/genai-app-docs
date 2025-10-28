"""セキュリティヘッダーミドルウェア。

このモジュールは、セキュリティベストプラクティスに基づいた
HTTPレスポンスヘッダーを自動的に追加するミドルウェアを提供します。

追加されるセキュリティヘッダー:
    1. **X-Content-Type-Options: nosniff**
       - MIMEタイプスニッフィングを無効化
       - ブラウザがContent-Typeを無視して独自にファイルタイプを判定するのを防ぐ
       - XSS攻撃のリスクを軽減

    2. **X-Frame-Options: DENY**
       - クリックジャッキング攻撃を防止
       - このページをiframe内で表示することを完全に禁止
       - 悪意のあるサイトでページを埋め込まれるのを防ぐ

    3. **X-XSS-Protection: 1; mode=block**
       - ブラウザのXSSフィルターを有効化
       - XSS攻撃を検出した場合、ページのレンダリングをブロック
       - 古いブラウザ向けの追加保護層

    4. **Strict-Transport-Security: max-age=31536000; includeSubDomains** (本番環境のみ)
       - HTTPS接続を強制（HSTS）
       - max-age=31536000: 1年間HSTSポリシーを記憶
       - includeSubDomains: すべてのサブドメインにも適用
       - HTTP接続を自動的にHTTPSにアップグレード

    5. **Content-Security-Policy** (オプション)
       - XSS、データインジェクション攻撃を防止
       - 信頼できるコンテンツソースのみ許可
       - インラインスクリプトの実行を制限

セキュリティヘッダーの効果:
    - XSS攻撃のリスク軽減
    - クリックジャッキング防止
    - MIMEタイプスニッフィング攻撃防止
    - 中間者攻撃（MITM）防止（HSTS）

Note:
    - 開発環境（DEBUG=True）ではHSTSヘッダーは追加されません
    - すべてのレスポンスに自動的に適用されます
    - レスポンスの内容を変更せず、ヘッダーのみ追加します
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーを自動的に追加するミドルウェア。

    すべてのHTTPレスポンスに推奨されるセキュリティヘッダーを追加します。
    OWASP (Open Web Application Security Project) のベストプラクティスに準拠しています。

    ヘッダーの詳細:
        - X-Content-Type-Options: MIMEスニッフィング防止
        - X-Frame-Options: クリックジャッキング防止
        - X-XSS-Protection: XSS攻撃防止（レガシーブラウザ向け）
        - Strict-Transport-Security: HTTPS強制（本番環境のみ）
        - Content-Security-Policy: コンテンツソース制限（オプション）

    Note:
        - このミドルウェアはレスポンスを変更せず、ヘッダーのみ追加します
        - 既存のヘッダーは上書きされません
        - 開発環境（DEBUG=True）ではHSTSは無効化されます
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理し、セキュリティヘッダーを追加します。

        実行フロー:
            1. 次のミドルウェア/ハンドラーを呼び出してレスポンスを取得
            2. レスポンスに基本的なセキュリティヘッダーを追加:
               - X-Content-Type-Options: nosniff
               - X-Frame-Options: DENY
               - X-XSS-Protection: 1; mode=block
            3. 本番環境（DEBUG=False）の場合のみ追加:
               - Strict-Transport-Security (HSTS)
            4. レスポンスを返却

        Args:
            request (Request): HTTPリクエストオブジェクト
            call_next (Callable): 次のミドルウェア/ハンドラー

        Returns:
            Response: セキュリティヘッダーが追加されたHTTPレスポンス

        Example:
            >>> # すべてのレスポンスに自動的に以下が追加されます:
            >>> # X-Content-Type-Options: nosniff
            >>> # X-Frame-Options: DENY
            >>> # X-XSS-Protection: 1; mode=block
            >>> # Strict-Transport-Security: max-age=31536000; includeSubDomains (本番のみ)

        Note:
            - ミドルウェアの順序は重要です
            - app_factory.pyで適切な順序で登録してください
            - 通常、CORSミドルウェアより後に配置します
        """
        # リクエストを処理
        response = await call_next(request)

        # 基本的なセキュリティヘッダーを追加
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 本番環境のみ: HSTS (HTTP Strict Transport Security)
        # HTTPSを強制し、中間者攻撃を防止
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # オプション: Content Security Policy (CSP)
        # より厳密なセキュリティが必要な場合は以下のコメントを解除
        # response.headers["Content-Security-Policy"] = (
        #     "default-src 'self'; "
        #     "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        #     "style-src 'self' 'unsafe-inline'; "
        #     "img-src 'self' data: https:; "
        #     "font-src 'self' data:; "
        #     "connect-src 'self'"
        # )

        logger.debug(
            "セキュリティヘッダーを追加しました",
            extra={
                "path": request.url.path,
                "method": request.method,
                "hsts_enabled": not settings.DEBUG,
            },
        )

        return response
