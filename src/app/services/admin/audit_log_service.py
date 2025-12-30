"""監査ログサービス。

このモジュールは、監査ログの記録・検索機能を提供します。
"""

import csv
import io
import json
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.models.enums.admin_enums import AuditEventType, AuditSeverity
from app.repositories.admin.audit_log_repository import AuditLogRepository
from app.schemas.admin.audit_log import (
    AuditLogExportFilter,
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogResponse,
)

logger = get_logger(__name__)


class AuditLogService:
    """監査ログサービス。

    監査ログの記録・検索・エクスポート機能を提供します。

    メソッド:
        - record_data_change: データ変更を記録
        - record_access: アクセスを記録
        - record_security_event: セキュリティイベントを記録
        - list_audit_logs: 監査ログ一覧を取得
        - list_by_event_type: イベント種別で取得
        - list_by_resource: リソースで取得
        - export: エクスポート
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.repository = AuditLogRepository(db)

    async def record_data_change(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None,
        old_value: dict | None,
        new_value: dict | None,
        changed_fields: list[str] | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        severity: str = AuditSeverity.INFO.value,
        metadata: dict | None = None,
    ) -> None:
        """データ変更を記録します。

        Args:
            user_id: ユーザーID
            action: アクション（CREATE/UPDATE/DELETE）
            resource_type: リソース種別
            resource_id: リソースID
            old_value: 変更前の値
            new_value: 変更後の値
            changed_fields: 変更フィールド
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            severity: 重要度
            metadata: メタデータ
        """
        try:
            await self.repository.create(
                user_id=user_id,
                event_type=AuditEventType.DATA_CHANGE.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_value=old_value,
                new_value=new_value,
                changed_fields=changed_fields,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                metadata=metadata,
            )
            await self.db.commit()

            logger.info(
                "データ変更を記録しました",
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
            )
        except Exception as e:
            logger.error(
                "データ変更の記録に失敗しました",
                error=str(e),
                resource_type=resource_type,
            )

    async def record_access(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """アクセスを記録します。

        Args:
            user_id: ユーザーID
            action: アクション（LOGIN_SUCCESS/LOGIN_FAILED/LOGOUT等）
            resource_type: リソース種別
            resource_id: リソースID
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            metadata: メタデータ
        """
        try:
            await self.repository.create(
                user_id=user_id,
                event_type=AuditEventType.ACCESS.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=AuditSeverity.INFO.value,
                metadata=metadata,
            )
            await self.db.commit()
        except Exception as e:
            logger.error(
                "アクセス記録に失敗しました",
                error=str(e),
                action=action,
            )

    async def record_security_event(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        severity: str = AuditSeverity.WARNING.value,
        metadata: dict | None = None,
    ) -> None:
        """セキュリティイベントを記録します。

        Args:
            user_id: ユーザーID
            action: アクション
            resource_type: リソース種別
            resource_id: リソースID
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            severity: 重要度
            metadata: メタデータ
        """
        try:
            await self.repository.create(
                user_id=user_id,
                event_type=AuditEventType.SECURITY.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                metadata=metadata,
            )
            await self.db.commit()

            logger.warning(
                "セキュリティイベントを記録しました",
                action=action,
                severity=severity,
                user_id=str(user_id) if user_id else None,
            )
        except Exception as e:
            logger.error(
                "セキュリティイベントの記録に失敗しました",
                error=str(e),
                action=action,
            )

    @measure_performance
    async def list_audit_logs(
        self,
        filter_params: AuditLogFilter,
    ) -> AuditLogListResponse:
        """監査ログ一覧を取得します。

        Args:
            filter_params: フィルタパラメータ

        Returns:
            AuditLogListResponse: 監査ログ一覧
        """
        logger.info(
            "監査ログ一覧を取得中",
            filters=filter_params.model_dump(exclude_unset=True),
            action="list_audit_logs",
        )

        logs = await self.repository.list_with_filters(
            event_type=filter_params.event_type,
            user_id=filter_params.user_id,
            resource_type=filter_params.resource_type,
            resource_id=filter_params.resource_id,
            severity=filter_params.severity,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            skip=(filter_params.page - 1) * filter_params.limit,
            limit=filter_params.limit,
        )

        total = await self.repository.count_with_filters(
            event_type=filter_params.event_type,
            user_id=filter_params.user_id,
            resource_type=filter_params.resource_type,
            resource_id=filter_params.resource_id,
            severity=filter_params.severity,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
        )

        total_pages = (total + filter_params.limit - 1) // filter_params.limit

        items = [self._to_response(log) for log in logs]

        return AuditLogListResponse(
            items=items,
            total=total,
            page=filter_params.page,
            limit=filter_params.limit,
            total_pages=total_pages,
        )

    @measure_performance
    async def list_by_event_type(
        self,
        event_type: str,
        filter_params: AuditLogFilter,
    ) -> AuditLogListResponse:
        """イベント種別で監査ログを取得します。

        Args:
            event_type: イベント種別
            filter_params: フィルタパラメータ

        Returns:
            AuditLogListResponse: 監査ログ一覧
        """
        filter_params.event_type = event_type
        return await self.list_audit_logs(filter_params)

    @measure_performance
    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        filter_params: AuditLogFilter,
    ) -> AuditLogListResponse:
        """リソースで監査ログを取得します。

        Args:
            resource_type: リソース種別
            resource_id: リソースID
            filter_params: フィルタパラメータ

        Returns:
            AuditLogListResponse: 監査ログ一覧
        """
        filter_params.resource_type = resource_type
        filter_params.resource_id = resource_id
        return await self.list_audit_logs(filter_params)

    @measure_performance
    async def export(
        self,
        filter_params: AuditLogExportFilter,
    ) -> str:
        """監査ログをエクスポートします。

        Args:
            filter_params: エクスポートフィルタ

        Returns:
            str: エクスポートデータ（CSV or JSON）
        """
        logger.info(
            "監査ログをエクスポート中",
            format=filter_params.format,
            action="export_audit_logs",
        )

        logs = await self.repository.list_with_filters(
            event_type=filter_params.event_type,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            skip=0,
            limit=10000,
        )

        if filter_params.format == "json":
            return self._export_to_json(logs)
        else:
            return self._export_to_csv(logs)

    def _to_response(self, log) -> AuditLogResponse:
        """モデルをレスポンスに変換します。"""
        return AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.display_name if log.user else None,
            user_email=log.user.email if log.user else None,
            event_type=log.event_type,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_value=log.old_value,
            new_value=log.new_value,
            changed_fields=log.changed_fields,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            severity=log.severity,
            metadata=log.metadata,
            created_at=log.created_at,
        )

    def _export_to_csv(self, logs) -> str:
        """CSV形式でエクスポートします。"""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "ID", "日時", "イベント種別", "アクション", "ユーザーID",
            "ユーザー名", "リソース種別", "リソースID", "重要度",
            "変更フィールド", "IPアドレス",
        ])

        for log in logs:
            writer.writerow([
                str(log.id),
                log.created_at.isoformat(),
                log.event_type,
                log.action,
                str(log.user_id) if log.user_id else "",
                log.user.display_name if log.user else "",
                log.resource_type,
                str(log.resource_id) if log.resource_id else "",
                log.severity,
                ",".join(log.changed_fields) if log.changed_fields else "",
                log.ip_address or "",
            ])

        return output.getvalue()

    def _export_to_json(self, logs) -> str:
        """JSON形式でエクスポートします。"""
        data = [
            {
                "id": str(log.id),
                "created_at": log.created_at.isoformat(),
                "event_type": log.event_type,
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "changed_fields": log.changed_fields,
                "severity": log.severity,
                "ip_address": log.ip_address,
                "metadata": log.metadata,
            }
            for log in logs
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)
