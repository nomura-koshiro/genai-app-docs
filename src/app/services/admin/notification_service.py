"""通知管理サービス。

このモジュールは、お知らせ・アラート・通知テンプレートの管理機能を提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin.announcement_repository import AnnouncementRepository
from app.repositories.admin.notification_template_repository import NotificationTemplateRepository
from app.repositories.admin.system_alert_repository import SystemAlertRepository
from app.schemas.admin.announcement import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.schemas.admin.notification_template import (
    NotificationTemplateListResponse,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
)
from app.schemas.admin.system_alert import (
    SystemAlertCreate,
    SystemAlertListResponse,
    SystemAlertResponse,
    SystemAlertUpdate,
)

logger = get_logger(__name__)


class NotificationService:
    """通知管理サービス。

    お知らせ・アラート・通知テンプレートの管理機能を提供します。

    メソッド:
        - list_alerts: アラート一覧を取得
        - create_alert: アラートを作成
        - update_alert: アラートを更新
        - delete_alert: アラートを削除
        - list_templates: テンプレート一覧を取得
        - update_template: テンプレートを更新
        - list_announcements: お知らせ一覧を取得
        - create_announcement: お知らせを作成
        - update_announcement: お知らせを更新
        - delete_announcement: お知らせを削除
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.alert_repository = SystemAlertRepository(db)
        self.template_repository = NotificationTemplateRepository(db)
        self.announcement_repository = AnnouncementRepository(db)

    # ================================================================================
    # アラート管理
    # ================================================================================

    @measure_performance
    async def list_alerts(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> SystemAlertListResponse:
        """アラート一覧を取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            SystemAlertListResponse: アラート一覧
        """
        logger.info("アラート一覧を取得中", action="list_alerts")

        alerts = await self.alert_repository.list_all(skip=skip, limit=limit)

        items = [self._alert_to_response(a) for a in alerts]

        return SystemAlertListResponse(
            items=items,
            total=len(items),
        )

    @measure_performance
    @transactional
    async def create_alert(
        self,
        data: SystemAlertCreate,
        created_by: uuid.UUID,
    ) -> SystemAlertResponse:
        """アラートを作成します。

        Args:
            data: アラート作成データ
            created_by: 作成者ID

        Returns:
            SystemAlertResponse: 作成されたアラート
        """
        logger.info(
            "アラートを作成中",
            name=data.name,
            created_by=str(created_by),
            action="create_alert",
        )

        alert = await self.alert_repository.create(
            name=data.name,
            condition_type=data.condition_type,
            threshold=data.threshold,
            comparison_operator=data.comparison_operator,
            notification_channels=data.notification_channels,
            is_enabled=data.is_enabled,
            created_by=created_by,
        )

        logger.info("アラートを作成しました", alert_id=str(alert.id))

        return self._alert_to_response(alert)

    @measure_performance
    @transactional
    async def update_alert(
        self,
        alert_id: uuid.UUID,
        data: SystemAlertUpdate,
    ) -> SystemAlertResponse:
        """アラートを更新します。

        Args:
            alert_id: アラートID
            data: アラート更新データ

        Returns:
            SystemAlertResponse: 更新されたアラート

        Raises:
            NotFoundError: アラートが見つからない場合
        """
        logger.info(
            "アラートを更新中",
            alert_id=str(alert_id),
            action="update_alert",
        )

        alert = await self.alert_repository.get(alert_id)
        if alert is None:
            raise NotFoundError(
                "アラートが見つかりません",
                details={"alert_id": str(alert_id)},
            )

        update_data = data.model_dump(exclude_unset=True)
        updated = await self.alert_repository.update(alert, **update_data)

        logger.info("アラートを更新しました", alert_id=str(alert_id))

        return self._alert_to_response(updated)

    @measure_performance
    @transactional
    async def delete_alert(self, alert_id: uuid.UUID) -> bool:
        """アラートを削除します。

        Args:
            alert_id: アラートID

        Returns:
            bool: 削除成功フラグ

        Raises:
            NotFoundError: アラートが見つからない場合
        """
        logger.info(
            "アラートを削除中",
            alert_id=str(alert_id),
            action="delete_alert",
        )

        success = await self.alert_repository.delete(alert_id)
        if not success:
            raise NotFoundError(
                "アラートが見つかりません",
                details={"alert_id": str(alert_id)},
            )

        logger.info("アラートを削除しました", alert_id=str(alert_id))
        return True

    # ================================================================================
    # 通知テンプレート管理
    # ================================================================================

    @measure_performance
    async def list_templates(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> NotificationTemplateListResponse:
        """テンプレート一覧を取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            NotificationTemplateListResponse: テンプレート一覧
        """
        logger.info("通知テンプレート一覧を取得中", action="list_templates")

        templates = await self.template_repository.list_all(skip=skip, limit=limit)

        items = [self._template_to_response(t) for t in templates]

        return NotificationTemplateListResponse(
            items=items,
            total=len(items),
        )

    @measure_performance
    @transactional
    async def update_template(
        self,
        template_id: uuid.UUID,
        data: NotificationTemplateUpdate,
    ) -> NotificationTemplateResponse:
        """テンプレートを更新します。

        Args:
            template_id: テンプレートID
            data: テンプレート更新データ

        Returns:
            NotificationTemplateResponse: 更新されたテンプレート

        Raises:
            NotFoundError: テンプレートが見つからない場合
        """
        logger.info(
            "通知テンプレートを更新中",
            template_id=str(template_id),
            action="update_template",
        )

        template = await self.template_repository.get(template_id)
        if template is None:
            raise NotFoundError(
                "テンプレートが見つかりません",
                details={"template_id": str(template_id)},
            )

        update_data = data.model_dump(exclude_unset=True)
        updated = await self.template_repository.update(template, **update_data)

        logger.info("通知テンプレートを更新しました", template_id=str(template_id))

        return self._template_to_response(updated)

    # ================================================================================
    # お知らせ管理
    # ================================================================================

    @measure_performance
    async def list_announcements(
        self,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AnnouncementListResponse:
        """お知らせ一覧を取得します。

        Args:
            is_active: アクティブフィルタ
            skip: スキップ数
            limit: 取得件数

        Returns:
            AnnouncementListResponse: お知らせ一覧
        """
        logger.info("お知らせ一覧を取得中", action="list_announcements")

        announcements = await self.announcement_repository.list_all(
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

        items = [self._announcement_to_response(a) for a in announcements]

        return AnnouncementListResponse(
            items=items,
            total=len(items),
        )

    @measure_performance
    async def list_active_announcements(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> AnnouncementListResponse:
        """アクティブなお知らせ一覧を取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            AnnouncementListResponse: お知らせ一覧
        """
        logger.info("アクティブなお知らせ一覧を取得中", action="list_active_announcements")

        announcements = await self.announcement_repository.list_active(
            current_time=datetime.now(UTC),
            skip=skip,
            limit=limit,
        )

        items = [self._announcement_to_response(a) for a in announcements]

        return AnnouncementListResponse(
            items=items,
            total=len(items),
        )

    @measure_performance
    @transactional
    async def create_announcement(
        self,
        data: AnnouncementCreate,
        created_by: uuid.UUID,
    ) -> AnnouncementResponse:
        """お知らせを作成します。

        Args:
            data: お知らせ作成データ
            created_by: 作成者ID

        Returns:
            AnnouncementResponse: 作成されたお知らせ
        """
        logger.info(
            "お知らせを作成中",
            title=data.title,
            created_by=str(created_by),
            action="create_announcement",
        )

        announcement = await self.announcement_repository.create(
            title=data.title,
            content=data.content,
            announcement_type=data.announcement_type,
            target_roles=data.target_roles,
            start_at=data.start_at,
            end_at=data.end_at,
            priority=data.priority,
            is_active=True,  # デフォルトで有効
            created_by=created_by,
        )

        logger.info("お知らせを作成しました", announcement_id=str(announcement.id))

        return self._announcement_to_response(announcement)

    @measure_performance
    @transactional
    async def update_announcement(
        self,
        announcement_id: uuid.UUID,
        data: AnnouncementUpdate,
    ) -> AnnouncementResponse:
        """お知らせを更新します。

        Args:
            announcement_id: お知らせID
            data: お知らせ更新データ

        Returns:
            AnnouncementResponse: 更新されたお知らせ

        Raises:
            NotFoundError: お知らせが見つからない場合
        """
        logger.info(
            "お知らせを更新中",
            announcement_id=str(announcement_id),
            action="update_announcement",
        )

        announcement = await self.announcement_repository.get(announcement_id)
        if announcement is None:
            raise NotFoundError(
                "お知らせが見つかりません",
                details={"announcement_id": str(announcement_id)},
            )

        update_data = data.model_dump(exclude_unset=True)
        updated = await self.announcement_repository.update(announcement, **update_data)

        logger.info("お知らせを更新しました", announcement_id=str(announcement_id))

        return self._announcement_to_response(updated)

    @measure_performance
    @transactional
    async def delete_announcement(self, announcement_id: uuid.UUID) -> bool:
        """お知らせを削除します。

        Args:
            announcement_id: お知らせID

        Returns:
            bool: 削除成功フラグ

        Raises:
            NotFoundError: お知らせが見つからない場合
        """
        logger.info(
            "お知らせを削除中",
            announcement_id=str(announcement_id),
            action="delete_announcement",
        )

        success = await self.announcement_repository.delete(announcement_id)
        if not success:
            raise NotFoundError(
                "お知らせが見つかりません",
                details={"announcement_id": str(announcement_id)},
            )

        logger.info("お知らせを削除しました", announcement_id=str(announcement_id))
        return True

    # ================================================================================
    # ヘルパーメソッド
    # ================================================================================

    def _alert_to_response(self, alert) -> SystemAlertResponse:
        """アラートモデルをレスポンスに変換します。"""
        return SystemAlertResponse(
            id=alert.id,
            name=alert.name,
            condition_type=alert.condition_type,
            threshold=alert.threshold,
            comparison_operator=alert.comparison_operator,
            notification_channels=alert.notification_channels,
            is_enabled=alert.is_enabled,
            last_triggered_at=alert.last_triggered_at,
            trigger_count=alert.trigger_count,
            created_by=alert.created_by,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )

    def _template_to_response(self, template) -> NotificationTemplateResponse:
        """テンプレートモデルをレスポンスに変換します。"""
        return NotificationTemplateResponse(
            id=template.id,
            event_type=template.event_type,
            name=template.name,
            subject=template.subject,
            body=template.body,
            variables=template.variables or [],
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    def _announcement_to_response(self, announcement) -> AnnouncementResponse:
        """お知らせモデルをレスポンスに変換します。"""
        return AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            announcement_type=announcement.announcement_type,
            target_roles=announcement.target_roles,
            start_at=announcement.start_at,
            end_at=announcement.end_at,
            priority=announcement.priority,
            is_active=announcement.is_active,
            created_by=announcement.created_by,
            created_by_name=announcement.creator.display_name if announcement.creator else None,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at,
        )
