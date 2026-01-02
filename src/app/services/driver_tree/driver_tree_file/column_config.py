"""カラム設定モジュール。

カラム設定の更新機能を提供します。
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.driver_tree import DriverTreeFileRepository
from app.repositories.project import ProjectFileRepository
from app.schemas.driver_tree import DriverTreeColumnSetupItem

logger = get_logger(__name__)


class ColumnConfigMixin:
    """カラム設定機能を提供するMixinクラス。

    Attributes:
        db: データベースセッション
        file_repository: DriverTreeFileリポジトリ
        project_file_repository: ProjectFileリポジトリ
    """

    db: AsyncSession
    file_repository: DriverTreeFileRepository
    project_file_repository: ProjectFileRepository

    @transactional
    @measure_performance
    async def update_column_config(
        self,
        project_id: uuid.UUID,
        file_id: uuid.UUID,
        sheet_id: uuid.UUID,
        columns: list[DriverTreeColumnSetupItem],
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """各シートのデータカラムの役割を設定します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            sheet_id: シートID
            columns: カラム設定リスト
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 設定結果
                - success: bool - 成功フラグ
                - columns: list[dict] - カラム情報リスト

        Raises:
            NotFoundError: ファイルまたはシートが見つからない場合
            ValidationError: 不正なカラム設定の場合
        """
        logger.info(
            "カラム設定更新リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            column_count=len(columns),
            action="update_column_config",
        )

        # 1. ProjectFileを取得
        project_file = await self.project_file_repository.get(file_id)
        if not project_file:
            raise NotFoundError(
                "ファイル見つかりません",
                details={"file_id": str(file_id)},
            )

        # 2. プロジェクトIDの確認
        if project_file.project_id != project_id:
            raise NotFoundError(
                "このプロジェクト内で該当ファイルが見つかりません",
                details={"file_id": str(file_id), "project_id": str(project_id)},
            )

        # 3. DriverTreeFileを取得（sheet_id = DriverTreeFile.id）
        driver_tree_file = await self.file_repository.get(sheet_id)
        if not driver_tree_file:
            raise NotFoundError(
                "シートが見つかりません",
                details={"sheet_id": str(sheet_id)},
            )

        # 4. DriverTreeFileがProjectFileに紐づいているか確認
        if driver_tree_file.project_file_id != file_id:
            raise NotFoundError(
                "このファイル内で該当シートが見つかりません",
                details={"sheet_id": str(sheet_id), "file_id": str(file_id)},
            )

        # 5. axis_config を更新
        updated_axis_config = {}
        for column_id, config in driver_tree_file.axis_config.items():
            updated_config = dict(config)
            for column_item in columns:
                if column_item.column_id == uuid.UUID(column_id):
                    updated_config["role"] = column_item.role.value
                    break
            updated_axis_config[column_id] = updated_config

        # 全てのカラムが存在するか確認
        for column_item in columns:
            if str(column_item.column_id) not in updated_axis_config:
                raise NotFoundError(
                    "カラム設定に該当カラムIDが見つかりません",
                    details={
                        "sheet_id": str(sheet_id),
                        "file_id": str(file_id),
                        "column_id": str(column_item.column_id),
                    },
                )

        # 6. DriverTreeFileのaxis_configを更新
        await self.file_repository.update(driver_tree_file, axis_config=updated_axis_config)

        # 7. レスポンス用のcolumns配列を構築（更新後のaxis_configを使用）
        columns_after = []
        for column_id, config in updated_axis_config.items():
            config_info = config.copy()
            config_info["column_id"] = column_id
            columns_after.append(config_info)

        logger.info(
            "カラム設定を更新しました",
            sheet_id=str(sheet_id),
            columns=len(columns),
        )

        return {"success": True, "columns": columns_after}
