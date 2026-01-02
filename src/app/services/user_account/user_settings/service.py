"""ユーザー設定サービスの実装。

このモジュールは、ユーザー設定の取得・更新機能を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.user_account import UserSettings
from app.schemas.user_account import (
    DisplaySettingsInfo,
    NotificationSettingsInfo,
    UserSettingsResponse,
    UserSettingsUpdate,
)

logger = get_logger(__name__)


class UserSettingsService:
    """ユーザー設定サービス。

    ユーザー設定の取得・更新機能を提供します。
    """

    def __init__(self, db: AsyncSession):
        """ユーザー設定サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db

    async def get_user_settings(self, user_id: uuid.UUID) -> UserSettingsResponse:
        """ユーザー設定を取得します。

        設定が存在しない場合はデフォルト設定を作成して返します。

        Args:
            user_id: ユーザーID

        Returns:
            UserSettingsResponse: ユーザー設定
        """
        settings = await self._get_or_create_settings(user_id)
        return self._to_response(settings)

    async def update_user_settings(
        self,
        user_id: uuid.UUID,
        update_data: UserSettingsUpdate,
    ) -> UserSettingsResponse:
        """ユーザー設定を更新します。

        Args:
            user_id: ユーザーID
            update_data: 更新データ

        Returns:
            UserSettingsResponse: 更新後のユーザー設定
        """
        settings = await self._get_or_create_settings(user_id)

        # 基本設定の更新
        if update_data.theme is not None:
            settings.theme = update_data.theme.value
        if update_data.language is not None:
            settings.language = update_data.language.value
        if update_data.timezone is not None:
            settings.timezone = update_data.timezone

        # 通知設定の更新
        if update_data.notifications is not None:
            notif = update_data.notifications
            if notif.email_enabled is not None:
                settings.email_enabled = notif.email_enabled
            if notif.project_invite is not None:
                settings.project_invite = notif.project_invite
            if notif.session_complete is not None:
                settings.session_complete = notif.session_complete
            if notif.tree_update is not None:
                settings.tree_update = notif.tree_update
            if notif.system_announcement is not None:
                settings.system_announcement = notif.system_announcement

        # 表示設定の更新
        if update_data.display is not None:
            disp = update_data.display
            if disp.items_per_page is not None:
                settings.items_per_page = disp.items_per_page
            if disp.default_project_view is not None:
                settings.default_project_view = disp.default_project_view.value
            if disp.show_welcome_message is not None:
                settings.show_welcome_message = disp.show_welcome_message

        await self.db.commit()
        await self.db.refresh(settings)

        logger.info(
            "ユーザー設定を更新しました",
            user_id=str(user_id),
        )

        return self._to_response(settings)

    async def _get_or_create_settings(self, user_id: uuid.UUID) -> UserSettings:
        """ユーザー設定を取得または作成します。

        Args:
            user_id: ユーザーID

        Returns:
            UserSettings: ユーザー設定
        """
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings is None:
            # デフォルト設定を作成
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
            logger.info(
                "ユーザー設定を作成しました",
                user_id=str(user_id),
            )

        return settings

    def _to_response(self, settings: UserSettings) -> UserSettingsResponse:
        """UserSettingsモデルをレスポンススキーマに変換します。

        Args:
            settings: ユーザー設定モデル

        Returns:
            UserSettingsResponse: ユーザー設定レスポンス
        """
        from app.schemas.user_account.user_settings import LanguageEnum, ProjectViewEnum, ThemeEnum

        return UserSettingsResponse(
            theme=ThemeEnum(settings.theme),
            language=LanguageEnum(settings.language),
            timezone=settings.timezone,
            notifications=NotificationSettingsInfo(
                email_enabled=settings.email_enabled,
                project_invite=settings.project_invite,
                session_complete=settings.session_complete,
                tree_update=settings.tree_update,
                system_announcement=settings.system_announcement,
            ),
            display=DisplaySettingsInfo(
                items_per_page=settings.items_per_page,
                default_project_view=ProjectViewEnum(settings.default_project_view),
                show_welcome_message=settings.show_welcome_message,
            ),
        )
