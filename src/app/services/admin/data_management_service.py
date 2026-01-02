"""データ管理サービス。

このモジュールは、データクリーンアップと保持ポリシー管理機能を提供します。
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.logging import get_logger
from app.repositories.admin.audit_log_repository import AuditLogRepository
from app.repositories.admin.system_setting_repository import SystemSettingRepository
from app.repositories.admin.user_activity_repository import UserActivityRepository
from app.repositories.admin.user_session_repository import UserSessionRepository
from app.schemas.admin.data_management import (
    CleanupExecuteResponse,
    CleanupPreviewItem,
    CleanupPreviewResponse,
    CleanupResultItem,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
)

logger = get_logger(__name__)


class DataManagementService:
    """データ管理サービス。

    データクリーンアップと保持ポリシー管理機能を提供します。

    メソッド:
        - preview_cleanup: クリーンアップをプレビュー
        - execute_cleanup: クリーンアップを実行
        - get_retention_policy: 保持ポリシーを取得
        - update_retention_policy: 保持ポリシーを更新
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.activity_repository = UserActivityRepository(db)
        self.audit_repository = AuditLogRepository(db)
        self.session_repository = UserSessionRepository(db)
        self.setting_repository = SystemSettingRepository(db)

    @measure_performance
    async def preview_cleanup(
        self,
        target_types: list[str],
        retention_days: int,
    ) -> CleanupPreviewResponse:
        """クリーンアップをプレビューします。

        Args:
            target_types: 対象種別
            retention_days: 保持日数

        Returns:
            CleanupPreviewResponse: プレビュー結果
        """
        logger.info(
            "クリーンアッププレビューを実行中",
            target_types=target_types,
            retention_days=retention_days,
            action="preview_cleanup",
        )

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        preview_items: list[CleanupPreviewItem] = []
        total_record_count = 0
        total_estimated_size_bytes = 0

        for target_type in target_types:
            item = await self._get_cleanup_preview_item(target_type, cutoff_date)
            if item:
                preview_items.append(item)
                total_record_count += item.record_count
                total_estimated_size_bytes += item.estimated_size_bytes

        return CleanupPreviewResponse(
            preview=preview_items,
            total_record_count=total_record_count,
            total_estimated_size_bytes=total_estimated_size_bytes,
            total_estimated_size_display=self._format_bytes(total_estimated_size_bytes),
            retention_days=retention_days,
            cutoff_date=cutoff_date,
        )

    async def _get_cleanup_preview_item(
        self,
        target_type: str,
        cutoff_date: datetime,
    ) -> CleanupPreviewItem | None:
        """対象種別ごとのプレビューアイテムを取得します。"""
        target_type_display_map = {
            "ACTIVITY_LOGS": "操作履歴",
            "AUDIT_LOGS": "監査ログ",
            "SESSION_LOGS": "セッションログ",
        }

        oldest_record_at: datetime | None = None
        newest_record_at: datetime | None = None

        if target_type == "ACTIVITY_LOGS":
            count = await self.activity_repository.count_with_filters(
                end_date=cutoff_date,
            )
            estimated_size = count * 500  # 推定1レコード500バイト
            oldest_record_at, newest_record_at = await self.activity_repository.get_date_range(
                end_date=cutoff_date,
            )
        elif target_type == "AUDIT_LOGS":
            count = await self.audit_repository.count_with_filters(
                end_date=cutoff_date,
            )
            estimated_size = count * 1000  # 推定1レコード1000バイト
            oldest_record_at, newest_record_at = await self.audit_repository.get_date_range(
                end_date=cutoff_date,
            )
        elif target_type == "SESSION_LOGS":
            # セッションログのカウント（非アクティブかつ期限切れ）
            count = await self.session_repository.count_expired(cutoff_date)
            estimated_size = count * 300
            oldest_record_at, newest_record_at = await self.session_repository.get_expired_date_range(
                cutoff_date,
            )
        else:
            return None

        return CleanupPreviewItem(
            target_type=target_type,
            target_type_display=target_type_display_map.get(target_type, target_type),
            record_count=count,
            oldest_record_at=oldest_record_at,
            newest_record_at=newest_record_at,
            estimated_size_bytes=estimated_size,
            estimated_size_display=self._format_bytes(estimated_size),
        )

    @measure_performance
    @transactional
    async def execute_cleanup(
        self,
        target_types: list[str],
        retention_days: int,
        performed_by: uuid.UUID,
    ) -> CleanupExecuteResponse:
        """クリーンアップを実行します。

        Args:
            target_types: 対象種別
            retention_days: 保持日数
            performed_by: 実行者ID

        Returns:
            CleanupExecuteResponse: 実行結果
        """
        logger.info(
            "クリーンアップを実行中",
            target_types=target_types,
            retention_days=retention_days,
            performed_by=str(performed_by),
            action="execute_cleanup",
        )

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        results: list[CleanupResultItem] = []
        total_deleted_count = 0
        total_freed_bytes = 0

        for target_type in target_types:
            result = await self._execute_cleanup_for_type(target_type, cutoff_date)
            if result:
                results.append(result)
                total_deleted_count += result.deleted_count
                total_freed_bytes += result.freed_bytes

        logger.warning(
            "クリーンアップを完了しました",
            total_deleted_count=total_deleted_count,
            total_freed_bytes=total_freed_bytes,
            performed_by=str(performed_by),
        )

        return CleanupExecuteResponse(
            success=True,
            results=results,
            total_deleted_count=total_deleted_count,
            total_freed_bytes=total_freed_bytes,
            total_freed_display=self._format_bytes(total_freed_bytes),
            executed_at=datetime.now(UTC),
        )

    async def _execute_cleanup_for_type(
        self,
        target_type: str,
        cutoff_date: datetime,
    ) -> CleanupResultItem | None:
        """対象種別ごとのクリーンアップを実行します。"""
        if target_type == "ACTIVITY_LOGS":
            deleted_count = await self.activity_repository.delete_old_records(cutoff_date)
            freed_bytes = deleted_count * 500
        elif target_type == "AUDIT_LOGS":
            deleted_count = await self.audit_repository.delete_old_records(cutoff_date)
            freed_bytes = deleted_count * 1000
        elif target_type == "SESSION_LOGS":
            deleted_count = await self.session_repository.cleanup_expired(cutoff_date)
            freed_bytes = deleted_count * 300
        else:
            return None

        return CleanupResultItem(
            target_type=target_type,
            deleted_count=deleted_count,
            freed_bytes=freed_bytes,
        )

    @measure_performance
    async def get_retention_policy(self) -> RetentionPolicyResponse:
        """保持ポリシーを取得します。

        Returns:
            RetentionPolicyResponse: 保持ポリシー
        """
        logger.info("保持ポリシーを取得中", action="get_retention_policy")

        activity_logs_days = await self.setting_repository.get_value("RETENTION", "activity_logs_days", default=90)
        audit_logs_days = await self.setting_repository.get_value("RETENTION", "audit_logs_days", default=365)
        deleted_projects_days = await self.setting_repository.get_value("RETENTION", "deleted_projects_days", default=30)
        session_logs_days = await self.setting_repository.get_value("RETENTION", "session_logs_days", default=30)

        return RetentionPolicyResponse(
            activity_logs_days=activity_logs_days,
            audit_logs_days=audit_logs_days,
            deleted_projects_days=deleted_projects_days,
            session_logs_days=session_logs_days,
        )

    @measure_performance
    @transactional
    async def update_retention_policy(
        self,
        policy: RetentionPolicyUpdate,
        updated_by: uuid.UUID,
    ) -> RetentionPolicyResponse:
        """保持ポリシーを更新します。

        Args:
            policy: 保持ポリシー更新データ
            updated_by: 更新者ID

        Returns:
            RetentionPolicyResponse: 更新された保持ポリシー
        """
        logger.info(
            "保持ポリシーを更新中",
            updated_by=str(updated_by),
            action="update_retention_policy",
        )

        if policy.activity_logs_days is not None:
            await self.setting_repository.set_value("RETENTION", "activity_logs_days", policy.activity_logs_days, updated_by)

        if policy.audit_logs_days is not None:
            await self.setting_repository.set_value("RETENTION", "audit_logs_days", policy.audit_logs_days, updated_by)

        if policy.deleted_projects_days is not None:
            await self.setting_repository.set_value("RETENTION", "deleted_projects_days", policy.deleted_projects_days, updated_by)

        if policy.session_logs_days is not None:
            await self.setting_repository.set_value("RETENTION", "session_logs_days", policy.session_logs_days, updated_by)

        logger.info("保持ポリシーを更新しました", updated_by=str(updated_by))

        return await self.get_retention_policy()

    def _format_bytes(self, bytes_value: int) -> str:
        """バイト数を人間が読める形式に変換します。"""
        value: float = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"
