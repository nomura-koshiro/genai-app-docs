"""一括操作サービス。

このモジュールは、ユーザーやプロジェクトの一括操作機能を提供します。
"""

import csv
import io
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.logging import get_logger
from app.models import Project, UserAccount
from app.models.audit.user_activity import UserActivity
from app.schemas.admin.bulk_operation import (
    BulkArchivePreviewItem,
    BulkArchiveResponse,
    BulkDeactivatePreviewItem,
    BulkDeactivateResponse,
    BulkImportResponse,
    BulkImportResult,
)

logger = get_logger(__name__)


@dataclass
class BulkOperationContext:
    """一括操作コンテキスト。

    一括操作の実行情報を保持します。

    Attributes:
        operation_id: 操作を一意に識別するID
        operation_type: 操作種別（IMPORT/DEACTIVATE/ARCHIVE/CLEANUP等）
        started_at: 操作開始日時
        performed_by: 実行者ユーザーID
        target_count: 対象レコード数
        processed_count: 処理済みレコード数
        success_count: 成功件数
        failure_count: 失敗件数
        metadata: 追加メタデータ
    """

    operation_id: uuid.UUID
    operation_type: str
    started_at: datetime
    performed_by: uuid.UUID
    target_count: int = 0
    processed_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        operation_type: str,
        performed_by: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> "BulkOperationContext":
        """新しい操作コンテキストを作成します。"""
        return cls(
            operation_id=uuid.uuid4(),
            operation_type=operation_type,
            started_at=datetime.now(UTC),
            performed_by=performed_by,
            metadata=metadata,
        )


class BulkOperationService:
    """一括操作サービス。

    ユーザーやプロジェクトの一括操作機能を提供します。

    メソッド:
        - import_users: ユーザーを一括インポート
        - export_users: ユーザーを一括エクスポート
        - deactivate_inactive_users: 非アクティブユーザーを一括無効化
        - archive_inactive_projects: 非アクティブプロジェクトを一括アーカイブ
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db

    @measure_performance
    @transactional
    async def import_users(
        self,
        csv_content: str,
        performed_by: uuid.UUID,
    ) -> BulkImportResponse:
        """ユーザーを一括インポートします。

        Args:
            csv_content: CSV形式のユーザーデータ
            performed_by: 実行者ID

        Returns:
            BulkImportResponse: インポート結果
        """
        ctx = BulkOperationContext.create(
            operation_type="USER_IMPORT",
            performed_by=performed_by,
        )

        logger.info(
            "ユーザー一括インポートを開始",
            operation_id=str(ctx.operation_id),
            performed_by=str(performed_by),
            action="import_users",
        )

        results: list[BulkImportResult] = []
        errors: list[str] = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(reader)
            ctx.target_count = len(rows)

            for row_num, row in enumerate(rows, start=2):  # ヘッダーを考慮して2から開始
                try:
                    # バリデーション
                    email = row.get("email", "").strip()
                    display_name = row.get("display_name", "").strip()

                    if not email:
                        raise ValueError("メールアドレスは必須です")
                    if not display_name:
                        raise ValueError("表示名は必須です")

                    # 重複チェック
                    existing = await self.db.execute(
                        select(UserAccount).where(UserAccount.email == email)
                    )
                    if existing.scalar_one_or_none():
                        raise ValueError(f"メールアドレス '{email}' は既に登録されています")

                    # ユーザー作成
                    user = UserAccount(
                        email=email,
                        display_name=display_name,
                        is_active=True,
                    )
                    self.db.add(user)

                    results.append(BulkImportResult(
                        row=row_num,
                        email=email,
                        success=True,
                        message="インポート成功",
                    ))
                    ctx.success_count += 1

                except Exception as e:
                    results.append(BulkImportResult(
                        row=row_num,
                        email=row.get("email", ""),
                        success=False,
                        message=str(e),
                    ))
                    errors.append(f"行 {row_num}: {str(e)}")
                    ctx.failure_count += 1

                ctx.processed_count += 1

            await self.db.flush()

        except Exception as e:
            logger.error(
                "ユーザー一括インポートに失敗",
                operation_id=str(ctx.operation_id),
                error=str(e),
            )
            raise

        logger.info(
            "ユーザー一括インポートを完了",
            operation_id=str(ctx.operation_id),
            success_count=ctx.success_count,
            failure_count=ctx.failure_count,
        )

        return BulkImportResponse(
            success=ctx.failure_count == 0,
            imported_count=ctx.success_count,
            error_count=ctx.failure_count,
            operation_id=ctx.operation_id,
            results=results,
            errors=errors if errors else None,
        )

    @measure_performance
    async def export_users(
        self,
        is_active: bool | None = None,
    ) -> str:
        """ユーザーを一括エクスポートします。

        Args:
            is_active: アクティブフィルタ

        Returns:
            str: CSV形式のユーザーデータ
        """
        logger.info(
            "ユーザー一括エクスポートを開始",
            is_active=is_active,
            action="export_users",
        )

        query = select(UserAccount)
        if is_active is not None:
            query = query.where(UserAccount.is_active == is_active)
        query = query.order_by(UserAccount.created_at)

        result = await self.db.execute(query)
        users = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow([
            "id",
            "email",
            "display_name",
            "is_active",
            "created_at",
            "updated_at",
        ])

        # データ行
        for user in users:
            writer.writerow([
                str(user.id),
                user.email,
                user.display_name,
                user.is_active,
                user.created_at.isoformat(),
                user.updated_at.isoformat() if user.updated_at else "",
            ])

        logger.info(
            "ユーザー一括エクスポートを完了",
            count=len(users),
        )

        return output.getvalue()

    @measure_performance
    @transactional
    async def deactivate_inactive_users(
        self,
        inactive_days: int,
        dry_run: bool = False,
        performed_by: uuid.UUID | None = None,
    ) -> BulkDeactivateResponse:
        """非アクティブユーザーを一括無効化します。

        Args:
            inactive_days: 非アクティブ日数
            dry_run: プレビューのみ
            performed_by: 実行者ID

        Returns:
            BulkDeactivateResponse: 無効化結果
        """
        ctx = BulkOperationContext.create(
            operation_type="USER_DEACTIVATE",
            performed_by=performed_by or uuid.uuid4(),
            metadata={"inactive_days": inactive_days, "dry_run": dry_run},
        )

        logger.info(
            "非アクティブユーザー一括無効化を開始",
            operation_id=str(ctx.operation_id),
            inactive_days=inactive_days,
            dry_run=dry_run,
            action="deactivate_inactive_users",
        )

        # 対象ユーザーを特定
        cutoff_date = datetime.now(UTC) - timedelta(days=inactive_days)

        # 最終アクティビティ日時を取得
        subquery = (
            select(
                UserActivity.user_id,
                func.max(UserActivity.created_at).label("last_activity")
            )
            .group_by(UserActivity.user_id)
        ).subquery()

        query = (
            select(UserAccount, subquery.c.last_activity)
            .outerjoin(subquery, UserAccount.id == subquery.c.user_id)
            .where(
                UserAccount.is_active == True,  # noqa: E712
                (subquery.c.last_activity < cutoff_date) | (subquery.c.last_activity.is_(None))
            )
        )

        result = await self.db.execute(query)
        target_users = result.all()
        ctx.target_count = len(target_users)

        preview_items = [
            BulkDeactivatePreviewItem(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                last_activity_at=last_activity,
            )
            for user, last_activity in target_users
        ]

        if dry_run:
            logger.info(
                "非アクティブユーザー一括無効化（プレビュー）を完了",
                operation_id=str(ctx.operation_id),
                target_count=ctx.target_count,
            )

            return BulkDeactivateResponse(
                success=True,
                deactivated_count=0,
                operation_id=ctx.operation_id,
                preview_items=preview_items,
            )

        # 実行
        for user, _ in target_users:
            user.is_active = False
            ctx.success_count += 1

        await self.db.flush()

        logger.warning(
            "非アクティブユーザー一括無効化を完了",
            operation_id=str(ctx.operation_id),
            deactivated_count=ctx.success_count,
        )

        return BulkDeactivateResponse(
            success=True,
            deactivated_count=ctx.success_count,
            operation_id=ctx.operation_id,
        )

    @measure_performance
    @transactional
    async def archive_inactive_projects(
        self,
        inactive_days: int,
        dry_run: bool = False,
        performed_by: uuid.UUID | None = None,
    ) -> BulkArchiveResponse:
        """非アクティブプロジェクトを一括アーカイブします。

        Args:
            inactive_days: 非アクティブ日数
            dry_run: プレビューのみ
            performed_by: 実行者ID

        Returns:
            BulkArchiveResponse: アーカイブ結果
        """
        ctx = BulkOperationContext.create(
            operation_type="PROJECT_ARCHIVE",
            performed_by=performed_by or uuid.uuid4(),
            metadata={"inactive_days": inactive_days, "dry_run": dry_run},
        )

        logger.info(
            "非アクティブプロジェクト一括アーカイブを開始",
            operation_id=str(ctx.operation_id),
            inactive_days=inactive_days,
            dry_run=dry_run,
            action="archive_inactive_projects",
        )

        # 対象プロジェクトを特定
        cutoff_date = datetime.now(UTC) - timedelta(days=inactive_days)

        query = (
            select(Project)
            .where(
                Project.is_active == True,  # noqa: E712
                Project.updated_at < cutoff_date,
            )
        )

        result = await self.db.execute(query)
        target_projects = result.scalars().all()
        ctx.target_count = len(target_projects)

        preview_items = [
            BulkArchivePreviewItem(
                project_id=project.id,
                name=project.name,
                last_updated_at=project.updated_at,
            )
            for project in target_projects
        ]

        if dry_run:
            logger.info(
                "非アクティブプロジェクト一括アーカイブ（プレビュー）を完了",
                operation_id=str(ctx.operation_id),
                target_count=ctx.target_count,
            )

            return BulkArchiveResponse(
                success=True,
                archived_count=0,
                operation_id=ctx.operation_id,
                preview_items=preview_items,
            )

        # 実行
        for project in target_projects:
            project.is_active = False
            ctx.success_count += 1

        await self.db.flush()

        logger.warning(
            "非アクティブプロジェクト一括アーカイブを完了",
            operation_id=str(ctx.operation_id),
            archived_count=ctx.success_count,
        )

        return BulkArchiveResponse(
            success=True,
            archived_count=ctx.success_count,
            operation_id=ctx.operation_id,
        )
