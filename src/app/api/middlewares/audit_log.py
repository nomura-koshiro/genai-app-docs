"""監査ログミドルウェア。

重要なデータ変更操作を監査ログに記録します。
"""

import asyncio
import json
import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from enum import Enum
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.database import get_async_session_context
from app.core.logging import get_logger
from app.models import AuditEventType, AuditLog, AuditSeverity
from app.models.project import Project
from app.models.system import SystemSetting
from app.models.user_account import UserAccount
from app.utils import RequestHelper
from app.utils.sensitive_data import mask_sensitive_data

logger = get_logger(__name__)


# リソースタイプとモデルのマッピング
RESOURCE_MODEL_MAPPING: dict[str, type] = {
    "PROJECT": Project,
    "USER": UserAccount,
    "SYSTEM_SETTING": SystemSetting,
    # 必要に応じて追加
}


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
        call_next: Callable[[Request], Awaitable[Response]],
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

        # 変更前の値を取得（リクエスト処理の前に実行）
        old_value: dict[str, Any] | None = None
        resource_id_str: str | None = None
        if method in {"PUT", "PATCH", "DELETE"}:
            resource_id_str = self._extract_resource_id(path, audit_config["pattern"])
            if resource_id_str:
                try:
                    old_value = await self._get_old_value(
                        resource_type=audit_config["resource_type"],
                        resource_id=uuid.UUID(resource_id_str),
                    )
                except Exception as e:
                    logger.warning("old_value取得エラー", error=str(e))

        # リクエストボディを取得
        request_body: dict[str, Any] | None = None
        if method in {"POST", "PUT", "PATCH"}:
            try:
                body_bytes = await request.body()
                request._body = body_bytes  # キャッシュして後続処理で再利用可能に
                request_body = json.loads(body_bytes)
            except Exception:
                pass

        # リクエスト処理
        response = await call_next(request)

        # 成功時のみ監査ログを記録（2xxのみ）- バックグラウンドタスクで実行
        if 200 <= response.status_code < 300:
            asyncio.create_task(
                self._record_audit_log(
                    request=request,
                    request_body=request_body,
                    old_value=old_value,
                    response=response,
                    audit_config=audit_config,
                )
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

    def _mask_request_body(self, body: dict[str, Any] | None) -> dict[str, Any] | None:
        """リクエストボディから機密情報をマスクします。

        共通モジュールのmask_sensitive_dataを使用して、
        ネストされた辞書やリストも再帰的に処理します。

        Args:
            body: リクエストボディ

        Returns:
            dict | None: マスク処理済みのリクエストボディ
        """
        if not body:
            return None

        return mask_sensitive_data(body)

    def _serialize_value(self, value: Any) -> Any:
        """値をシリアライズ可能な形式に変換します。

        Args:
            value: シリアライズする値

        Returns:
            Any: シリアライズされた値
        """
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        return value

    async def _get_old_value(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        """変更前の値を取得します。

        Args:
            resource_type: リソースタイプ
            resource_id: リソースID

        Returns:
            変更前の値の辞書、または取得できない場合はNone
        """
        try:
            model = RESOURCE_MODEL_MAPPING.get(resource_type)
            if not model:
                return None

            async with get_async_session_context() as session:
                result = await session.get(model, resource_id)  # type: ignore[func-returns-value]
                if not result:
                    return None

                # モデルを辞書に変換してから機密情報を再帰的にマスク
                raw_dict = {
                    key: self._serialize_value(value)
                    for key, value in result.__dict__.items()
                    if not key.startswith("_")
                }
                return mask_sensitive_data(raw_dict)
        except Exception as e:
            logger.warning(
                "変更前の値の取得に失敗",
                error=str(e),
                resource_type=resource_type,
                resource_id=str(resource_id),
            )
            return None

    async def _record_audit_log(
        self,
        request: Request,
        request_body: dict[str, Any] | None,
        old_value: dict[str, Any] | None,
        response: Response,
        audit_config: dict[str, Any],
    ) -> None:
        """監査ログを記録します。

        Args:
            request: HTTPリクエスト
            request_body: リクエストボディ
            old_value: 変更前の値（リクエスト処理前に取得済み）
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

            # リクエストボディから機密情報をマスク
            masked_request_body = self._mask_request_body(request_body)

            # 変更されたフィールドを特定
            changed_fields = self._get_changed_fields(old_value, request_body)
            if not changed_fields and request_body:
                changed_fields = list(request_body.keys())

            # 監査ログを作成
            audit_log = AuditLog(
                user_id=user_id,
                event_type=audit_config["event_type"].value,
                action=self._infer_action(request.method),
                resource_type=audit_config["resource_type"],
                resource_id=uuid.UUID(resource_id_str) if resource_id_str else None,
                old_value=old_value,
                new_value=masked_request_body,  # マスク処理済みのデータを使用
                changed_fields=changed_fields,
                ip_address=RequestHelper.get_client_ip(request),
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
                session.add(audit_log)
                await session.commit()

        except Exception as e:
            # NOTE: バックグラウンドタスクでは例外は親に伝播しないため、
            # 失敗時はエラーログを記録して監視システムでアラート検知する
            logger.error(
                "監査ログの記録に失敗しました（要調査）",
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
                method=request.method,
                resource_type=audit_config.get("resource_type"),
                severity="CRITICAL",  # 監視システムでアラート対象とする
            )
