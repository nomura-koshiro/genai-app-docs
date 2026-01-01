"""SystemSetting シーダー。"""

import uuid
from typing import Any

from app.models.system.system_setting import SystemSetting

from .base import BaseSeeder


class SystemSettingSeederMixin(BaseSeeder):
    """SystemSetting作成用Mixin。"""

    async def create_system_setting(
        self,
        *,
        category: str = "GENERAL",
        key: str | None = None,
        value: Any = None,
        value_type: str = "STRING",
        description: str = "Test setting",
        is_secret: bool = False,
        is_editable: bool = True,
    ) -> SystemSetting:
        """テスト用システム設定を作成。"""
        unique_id = uuid.uuid4().hex[:8]
        setting = SystemSetting(
            category=category,
            key=key or f"test_key_{unique_id}",
            value=value if value is not None else f"test_value_{unique_id}",
            value_type=value_type,
            description=description,
            is_secret=is_secret,
            is_editable=is_editable,
        )
        self.db.add(setting)
        await self.db.flush()
        await self.db.refresh(setting)
        return setting

    async def create_app_name_setting(self) -> SystemSetting:
        """アプリケーション名設定を作成。"""
        return await self.create_system_setting(
            category="GENERAL",
            key="app_name",
            value="GenAI App",
            value_type="STRING",
            description="アプリケーション名",
        )

    async def create_maintenance_mode_setting(self) -> SystemSetting:
        """メンテナンスモード設定を作成。"""
        return await self.create_system_setting(
            category="MAINTENANCE",
            key="maintenance_mode",
            value=False,
            value_type="BOOLEAN",
            description="メンテナンスモード有効フラグ",
        )

    async def create_maintenance_message_setting(self) -> SystemSetting:
        """メンテナンスメッセージ設定を作成。"""
        return await self.create_system_setting(
            category="MAINTENANCE",
            key="maintenance_message",
            value="",
            value_type="STRING",
            description="メンテナンスメッセージ",
        )

    async def create_allow_admin_access_setting(self) -> SystemSetting:
        """管理者アクセス許可設定を作成。"""
        return await self.create_system_setting(
            category="MAINTENANCE",
            key="allow_admin_access",
            value=True,
            value_type="BOOLEAN",
            description="メンテナンス中の管理者アクセス許可",
        )

    async def create_debug_mode_setting(self) -> SystemSetting:
        """デバッグモード設定を作成。"""
        return await self.create_system_setting(
            category="DEBUG",
            key="debug_mode",
            value=False,
            value_type="BOOLEAN",
            description="デバッグモード有効フラグ",
        )

    async def create_retention_policy_settings(self) -> list[SystemSetting]:
        """保持ポリシー設定を作成。"""
        return [
            await self.create_system_setting(
                category="RETENTION",
                key="activity_logs_days",
                value=90,
                value_type="NUMBER",
                description="アクティビティログ保持日数",
            ),
            await self.create_system_setting(
                category="RETENTION",
                key="audit_logs_days",
                value=365,
                value_type="NUMBER",
                description="監査ログ保持日数",
            ),
            await self.create_system_setting(
                category="RETENTION",
                key="session_logs_days",
                value=30,
                value_type="NUMBER",
                description="セッションログ保持日数",
            ),
        ]

    async def seed_default_settings(self) -> list[SystemSetting]:
        """デフォルトのシステム設定をシード。"""
        settings = [
            await self.create_app_name_setting(),
            await self.create_maintenance_mode_setting(),
            await self.create_maintenance_message_setting(),
            await self.create_allow_admin_access_setting(),
            await self.create_debug_mode_setting(),
        ]
        retention_settings = await self.create_retention_policy_settings()
        settings.extend(retention_settings)
        await self.db.commit()
        return settings
