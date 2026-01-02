"""システム設定サービス。

このモジュールは、システム設定の管理機能を提供します。
"""

import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.admin.system_setting_repository import SystemSettingRepository
from app.schemas.admin.system_setting import (
    MaintenanceModeEnable,
    MaintenanceModeResponse,
    SystemSettingResponse,
    SystemSettingsByCategoryResponse,
)

logger = get_logger(__name__)


class SystemSettingService:
    """システム設定サービス。

    システム設定の取得・更新機能を提供します。

    メソッド:
        - get_all_settings: 全設定を取得
        - get_settings_by_category: カテゴリ別設定を取得
        - update_setting: 設定を更新
        - enable_maintenance_mode: メンテナンスモードを有効化
        - disable_maintenance_mode: メンテナンスモードを無効化
        - get_maintenance_status: メンテナンスモード状態を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.repository = SystemSettingRepository(db)

    @measure_performance
    async def get_all_settings(self) -> SystemSettingsByCategoryResponse:
        """全設定をカテゴリ別に取得します。

        Returns:
            SystemSettingsByCategoryResponse: カテゴリ別設定
        """
        logger.info("全設定を取得中", action="get_all_settings")

        grouped = await self.repository.list_all_grouped()

        categories = {}
        for category, settings in grouped.items():
            categories[category] = [
                SystemSettingResponse(
                    key=s.key,
                    value=s.value if not s.is_secret else "***",
                    value_type=s.value_type,
                    description=s.description,
                    is_editable=s.is_editable,
                )
                for s in settings
            ]

        return SystemSettingsByCategoryResponse(categories=categories)

    @measure_performance
    async def get_settings_by_category(
        self,
        category: str,
    ) -> list[SystemSettingResponse]:
        """カテゴリ別設定を取得します。

        Args:
            category: カテゴリ

        Returns:
            list[SystemSettingResponse]: 設定リスト
        """
        logger.info(
            "カテゴリ別設定を取得中",
            category=category,
            action="get_settings_by_category",
        )

        settings = await self.repository.list_by_category(category)

        return [
            SystemSettingResponse(
                key=s.key,
                value=s.value if not s.is_secret else "***",
                value_type=s.value_type,
                description=s.description,
                is_editable=s.is_editable,
            )
            for s in settings
        ]

    @measure_performance
    @transactional
    async def update_setting(
        self,
        category: str,
        key: str,
        value: Any,
        updated_by: uuid.UUID,
    ) -> SystemSettingResponse:
        """設定を更新します。

        Args:
            category: カテゴリ
            key: 設定キー
            value: 新しい値
            updated_by: 更新者ID

        Returns:
            SystemSettingResponse: 更新された設定

        Raises:
            NotFoundError: 設定が見つからない場合
            ValidationError: 編集不可の設定の場合
        """
        logger.info(
            "設定を更新中",
            category=category,
            key=key,
            updated_by=str(updated_by),
            action="update_setting",
        )

        setting = await self.repository.get_by_category_and_key(category, key)
        if setting is None:
            raise NotFoundError(
                "設定が見つかりません",
                details={"category": category, "key": key},
            )

        if not setting.is_editable:
            raise ValidationError(
                "この設定は編集できません",
                details={"category": category, "key": key},
            )

        # 型に応じた値の変換・検証
        validated_value = self._validate_value(value, setting.value_type)

        updated = await self.repository.set_value(
            category=category,
            key=key,
            value=validated_value,
            updated_by=updated_by,
        )

        logger.info(
            "設定を更新しました",
            category=category,
            key=key,
        )

        return SystemSettingResponse(
            key=updated.key,
            value=updated.value if not updated.is_secret else "***",
            value_type=updated.value_type,
            description=updated.description,
            is_editable=updated.is_editable,
        )

    @measure_performance
    @transactional
    async def enable_maintenance_mode(
        self,
        params: MaintenanceModeEnable,
        updated_by: uuid.UUID,
    ) -> MaintenanceModeResponse:
        """メンテナンスモードを有効化します。

        Args:
            params: メンテナンスモードパラメータ
            updated_by: 更新者ID

        Returns:
            MaintenanceModeResponse: メンテナンスモード状態
        """
        logger.info(
            "メンテナンスモードを有効化中",
            updated_by=str(updated_by),
            action="enable_maintenance_mode",
        )

        # 3つの設定更新を並行実行
        await asyncio.gather(
            self.repository.set_value(
                category="MAINTENANCE",
                key="maintenance_mode",
                value=True,
                updated_by=updated_by,
            ),
            self.repository.set_value(
                category="MAINTENANCE",
                key="maintenance_message",
                value=params.message,
                updated_by=updated_by,
            ),
            self.repository.set_value(
                category="MAINTENANCE",
                key="allow_admin_access",
                value=params.allow_admin_access,
                updated_by=updated_by,
            ),
        )

        logger.warning(
            "メンテナンスモードが有効化されました",
            message=params.message,
            updated_by=str(updated_by),
        )

        return MaintenanceModeResponse(
            enabled=True,
            message=params.message,
            allow_admin_access=params.allow_admin_access,
        )

    @measure_performance
    @transactional
    async def disable_maintenance_mode(
        self,
        updated_by: uuid.UUID,
    ) -> MaintenanceModeResponse:
        """メンテナンスモードを無効化します。

        Args:
            updated_by: 更新者ID

        Returns:
            MaintenanceModeResponse: メンテナンスモード状態
        """
        logger.info(
            "メンテナンスモードを無効化中",
            updated_by=str(updated_by),
            action="disable_maintenance_mode",
        )

        await self.repository.set_value(
            category="MAINTENANCE",
            key="maintenance_mode",
            value=False,
            updated_by=updated_by,
        )

        logger.info(
            "メンテナンスモードが無効化されました",
            updated_by=str(updated_by),
        )

        return MaintenanceModeResponse(
            enabled=False,
            message=None,
            allow_admin_access=True,
        )

    @measure_performance
    async def get_maintenance_status(self) -> MaintenanceModeResponse:
        """メンテナンスモード状態を取得します。

        Returns:
            MaintenanceModeResponse: メンテナンスモード状態
        """
        # 3つの設定取得を並行実行
        enabled, message, allow_admin = await asyncio.gather(
            self.repository.get_value("MAINTENANCE", "maintenance_mode", default=False),
            self.repository.get_value("MAINTENANCE", "maintenance_message", default=None),
            self.repository.get_value("MAINTENANCE", "allow_admin_access", default=True),
        )

        return MaintenanceModeResponse(
            enabled=enabled,
            message=message if enabled else None,
            allow_admin_access=allow_admin,
        )

    def _validate_value(self, value: Any, value_type: str) -> Any:
        """値を検証・変換します。"""
        if value_type == "NUMBER":
            try:
                return float(value) if "." in str(value) else int(value)
            except (ValueError, TypeError) as err:
                raise ValidationError(
                    "数値形式が不正です",
                    details={"value": value},
                ) from err
        elif value_type == "BOOLEAN":
            if isinstance(value, bool):
                return value
            if str(value).lower() in ("true", "1", "yes"):
                return True
            if str(value).lower() in ("false", "0", "no"):
                return False
            raise ValidationError(
                "真偽値形式が不正です",
                details={"value": value},
            )
        elif value_type == "JSON":
            if isinstance(value, dict | list):
                return value
            raise ValidationError(
                "JSON形式が不正です",
                details={"value": value},
            )
        else:
            return str(value)
