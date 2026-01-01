"""システム設定リポジトリ。

このモジュールは、システム設定のデータアクセスを提供します。
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system.system_setting import SystemSetting
from app.repositories.base import BaseRepository


class SystemSettingRepository(BaseRepository[SystemSetting, uuid.UUID]):
    """システム設定リポジトリ。

    システム設定のCRUD操作を提供します。

    メソッド:
        - get_by_category_and_key: カテゴリとキーで取得
        - list_by_category: カテゴリで一覧取得
        - list_all_grouped: カテゴリ別にグループ化して取得
        - get_value: 設定値を取得
        - set_value: 設定値を設定
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(SystemSetting, db)

    async def get_by_category_and_key(
        self,
        category: str,
        key: str,
    ) -> SystemSetting | None:
        """カテゴリとキーで設定を取得します。

        Args:
            category: カテゴリ
            key: 設定キー

        Returns:
            SystemSetting | None: システム設定
        """
        query = select(SystemSetting).where(
            SystemSetting.category == category,
            SystemSetting.key == key,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_category(self, category: str) -> list[SystemSetting]:
        """カテゴリで設定一覧を取得します。

        Args:
            category: カテゴリ

        Returns:
            list[SystemSetting]: システム設定リスト
        """
        query = select(SystemSetting).where(SystemSetting.category == category).order_by(SystemSetting.key)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all_grouped(self) -> dict[str, list[SystemSetting]]:
        """全設定をカテゴリ別にグループ化して取得します。

        Returns:
            dict[str, list[SystemSetting]]: カテゴリ別設定
        """
        query = select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
        result = await self.db.execute(query)
        settings = list(result.scalars().all())

        grouped: dict[str, list[SystemSetting]] = {}
        for setting in settings:
            if setting.category not in grouped:
                grouped[setting.category] = []
            grouped[setting.category].append(setting)

        return grouped

    async def get_value(
        self,
        category: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """設定値を取得します。

        Args:
            category: カテゴリ
            key: 設定キー
            default: デフォルト値

        Returns:
            Any: 設定値
        """
        setting = await self.get_by_category_and_key(category, key)
        if setting is None:
            return default
        return setting.value

    async def set_value(
        self,
        category: str,
        key: str,
        value: Any,
        updated_by: uuid.UUID | None = None,
    ) -> SystemSetting:
        """設定値を設定します。

        Args:
            category: カテゴリ
            key: 設定キー
            value: 設定値
            updated_by: 更新者ID

        Returns:
            SystemSetting: 更新された設定
        """
        setting = await self.get_by_category_and_key(category, key)
        if setting is None:
            raise ValueError(f"Setting not found: {category}/{key}")

        setting.value = value
        if updated_by:
            setting.updated_by = updated_by

        await self.db.flush()
        await self.db.refresh(setting)
        return setting
