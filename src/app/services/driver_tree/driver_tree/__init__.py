"""ドライバーツリーサービス。

このモジュールは、ドライバーツリーのツリー管理ビジネスロジックを提供します。

主な機能:
    - ツリーCRUD（作成、取得、削除、リセット）
    - 数式/データインポート
    - マスタデータ取得（業界分類、KPI、数式）
    - 計算・出力

サブモジュール:
    - base.py: 共通ヘルパー
    - crud.py: CRUD操作
    - master.py: マスタデータ取得
    - calculation.py: 計算・出力
"""

import uuid
from typing import Any

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.driver_tree.driver_tree.calculation import DriverTreeCalculationService
from app.services.driver_tree.driver_tree.crud import DriverTreeCrudService
from app.services.driver_tree.driver_tree.master import DriverTreeMasterService


class DriverTreeService:
    """ドライバーツリーのツリー管理ビジネスロジックを提供するサービスクラス。

    ツリーのCRUD、数式インポート、マスタデータ取得、計算・出力を提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """ドライバーツリーサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._crud_service = DriverTreeCrudService(db)
        self._master_service = DriverTreeMasterService(db)
        self._calculation_service = DriverTreeCalculationService(db)

    # ================================================================================
    # ツリー CRUD
    # ================================================================================

    async def create_tree(
        self,
        project_id: uuid.UUID,
        name: str,
        description: str | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """新規ツリーを作成します。"""
        return await self._crud_service.create_tree(project_id, name, description, user_id)

    async def list_trees(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーの一覧を取得します。"""
        return await self._crud_service.list_trees(project_id, user_id)

    async def get_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーの全体構造を取得します。"""
        return await self._crud_service.get_tree(project_id, tree_id, user_id)

    async def import_formula(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        position_x: int,
        position_y: int,
        formulas: list[str],
        sheet_id: uuid.UUID | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーに数式データをインポートします。"""
        return await self._crud_service.import_formula(project_id, tree_id, position_x, position_y, formulas, sheet_id, user_id)

    async def reset_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーを初期状態にリセットします。"""
        return await self._crud_service.reset_tree(project_id, tree_id, user_id)

    async def delete_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーを完全に削除します。"""
        return await self._crud_service.delete_tree(project_id, tree_id, user_id)

    async def duplicate_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """ドライバーツリーを複製します。"""
        return await self._crud_service.duplicate_tree(project_id, tree_id, user_id, new_name)

    async def get_tree_policies(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーに紐づく施策一覧を取得します。"""
        return await self._crud_service.get_tree_policies(project_id, tree_id, user_id)

    # ================================================================================
    # マスタデータ取得
    # ================================================================================

    async def get_categories(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """業界分類一覧を取得します。

        Returns:
            dict[str, Any]: Response schema に適合する形式
        """
        return await self._master_service.get_categories(project_id, user_id)

    async def get_formulas(
        self,
        project_id: uuid.UUID,
        driver_type_id: int,
        kpi: str,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """数式を取得します。

        Args:
            project_id: プロジェクトID
            driver_type_id: ドライバー型ID
            kpi: KPI
            user_id: ユーザーID

        Returns:
            dict[str, Any]: Response schema に適合する形式
        """
        return await self._master_service.get_formulas(project_id, driver_type_id, kpi, user_id)

    # ================================================================================
    # 計算・出力
    # ================================================================================

    async def get_tree_data(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリー全体の計算を実行し結果を取得します。"""
        return await self._calculation_service.get_tree_data(project_id, tree_id, user_id)

    async def download_simulation_output(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        format: str,
        user_id: uuid.UUID,
    ) -> StreamingResponse:
        """シミュレーション結果をExcel/CSV形式でエクスポートします。"""
        return await self._calculation_service.download_simulation_output(project_id, tree_id, format, user_id)


__all__ = ["DriverTreeService"]
