"""監査ログミドルウェア。

重要なデータ変更操作を監査ログに記録します。
"""

import re
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.database.session import get_async_session_context
from app.models.admin import AuditEventType, AuditLog, AuditSeverity
from app.repositories.admin import AuditLogRepository

logger = get_logger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """監査ログミドルウェア。

    データ変更・セキュリティイベントを監査ログに記録します。

    Attributes:
        AUDIT_TARGETS: 監査対象のパスパターンと設定
    """

    # 監査対象のパスパターンと設定
    AUDIT_TARGETS: list[dict[str, Any]] = [
        # プロジェクト変更
        {
            "pattern": re.compile(r"^/api/v1/projects?/([0-9a-f-]{36})$"),
            "methods": {"PUT", "PATCH", "DELETE"},
            "resource_type": "PROJECT",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.INFO,
        },
        # ユーザー変更
        {
            "pattern": re.compile(r"^/api/v1/user_accounts?/([0-9a-f-]{36})$"),
            "methods": {"PUT", "PATCH", "DELETE"},
            "resource_type": "USER",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.INFO,
        },
        # システム設定変更
        {
            "pattern": re.compile(r"^/api/v1/admin/settings/"),
            "methods": {"PATCH", "POST"},
            "resource_type": "SYSTEM_SETTING",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.WARNING,
        },
        # セッション終了（強制ログアウト）
        {
            "pattern": re.compile(r"^/api/v1/admin/sessions/.*/terminate"),
            "methods": {"POST"},
            "resource_type": "SESSION",
            "event_type": AuditEventType.SECURITY,
            "severity": AuditSeverity.WARNING,
        },
        # 一括操作
        {
            "pattern": re.compile(r"^/api/v1/admin/bulk/"),
            "methods": {"POST"},
            "resource_type": "BULK_OPERATION",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.WARNING,
        },
        # データ削除
        {
            "pattern": re.compile(r"^/api/v1/admin/data/cleanup/execute"),
            "methods": {"POST"},
            "resource_type": "DATA_CLEANUP",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.CRITICAL,
        },
        # 代行操作
        {
            "pattern": re.compile(r"^/api/v1/admin/impersonate/"),
            "methods": {"POST"},
            "resource_type": "IMPERSONATION",
            "event_type": AuditEventType.SECURITY,
            "severity": AuditSeverity.CRITICAL,
        },
    ]

    def __init__(self, app: ASGIApp) -> None:
        """ミドルウェアを初期化します。

        Args:
            app: ASGIアプリケーション
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """リクエストを処理し、必要に応じて監査ログを記録します。

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/エンドポイント

        Returns:
            Response: HTTPレスポンス
        """
        path = request.url.path
        method = request.method

        # 監査対象かチェック
        audit_config = self._get_audit_config(path, method)
        if not audit_config:
            return await call_next(request)

        # リクエストボディを取得
        request_body: dict[str, Any] | None = None
        if method in {"POST", "PUT", "PATCH"}:
            try:
                request_body = await request.json()
            except Exception:
                pass

        # リクエスト処理
        response = await call_next(request)

        # 成功時のみ監査ログを記録（2xxのみ）
        if 200 <= response.status_code < 300:
            await self._record_audit_log(
                request=request,
                request_body=request_body,
                response=response,
                audit_config=audit_config,
            )

        return response

    def _get_audit_config(self, path: str, method: str) -> dict[str, Any] | None:
        """パスとメソッドから監査設定を取得します。

        Args:
            path: URLパス
            method: HTTPメソッド

        Returns:
            dict | None: 監査設定（該当なしの場合None）
        """
        for config in self.AUDIT_TARGETS:
            if method in config["methods"] and config["pattern"].match(path):
                return config
        return None

    def _extract_resource_id(self, path: str, pattern: re.Pattern[str]) -> str | None:
        """パスからリソースIDを抽出します。

        Args:
            path: URLパス
            pattern: 正規表現パターン

        Returns:
            str | None: リソースID
        """
        match = pattern.search(path)
        if match and match.groups():
            return match.group(1)
        return None

    def _infer_action(self, method: str) -> str:
        """HTTPメソッドからアクションを推定します。

        Args:
            method: HTTPメソッド

        Returns:
            str: アクション種別
        """
        mapping = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        return mapping.get(method, "OTHER")

    def _get_changed_fields(
        self,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
    ) -> list[str]:
        """変更されたフィールドを特定します。

        Args:
            old_value: 変更前の値
            new_value: 変更後の値

        Returns:
            list[str]: 変更されたフィールド名のリスト
        """
        if not old_value or not new_value:
            return []

        changed = []
        all_keys = set(old_value.keys()) | set(new_value.keys())

        for key in all_keys:
            old_val = old_value.get(key)
            new_val = new_value.get(key)
            if old_val != new_val:
                changed.append(key)

        return changed

    async def _record_audit_log(
        self,
        request: Request,
        request_body: dict[str, Any] | None,
        response: Response,
        audit_config: dict[str, Any],
    ) -> None:
        """監査ログを記録します。

        Args:
            request: HTTPリクエスト
            request_body: リクエストボディ
            response: HTTPレスポンス
            audit_config: 監査設定
        """
        try:
            # リソースIDを抽出
            resource_id_str = self._extract_resource_id(
                request.url.path,
                audit_config["pattern"],
            )

            # ユーザーIDを取得
            user_id = None
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id

            # 監査ログを作成
            audit_log = AuditLog(
                user_id=user_id,
                event_type=audit_config["event_type"].value,
                action=self._infer_action(request.method),
                resource_type=audit_config["resource_type"],
                resource_id=uuid.UUID(resource_id_str) if resource_id_str else None,
                old_value=None,  # 変更前の値は別途取得が必要
                new_value=request_body,
                changed_fields=list(request_body.keys()) if request_body else None,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", "")[:500],
                severity=audit_config["severity"].value,
                metadata={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                },
            )

            # DB保存
            async with get_async_session_context() as session:
                repository = AuditLogRepository(session)
                await repository.create(audit_log)
                await session.commit()

        except Exception as e:
            logger.error(
                "監査ログの記録に失敗しました",
                error=str(e),
                path=request.url.path,
            )

    def _get_client_ip(self, request: Request) -> str | None:
        """クライアントIPアドレスを取得します。

        Args:
            request: HTTPリクエスト

        Returns:
            str | None: クライアントIPアドレス
        """
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return None
