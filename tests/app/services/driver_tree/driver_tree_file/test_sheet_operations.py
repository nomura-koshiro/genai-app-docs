"""シート操作サービスのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.driver_tree.driver_tree_file.sheet_operations import SheetOperationsMixin


class TestSheetOperationsMixin:
    """SheetOperationsMixinのテスト。"""

    def _create_mixin_instance(self, db_session):
        """テスト用にMixinインスタンスを作成。"""

        class TestService(SheetOperationsMixin):
            def __init__(self, db):
                self.db = db
                self.file_repository = MagicMock()
                self.data_frame_repository = MagicMock()
                self.project_file_repository = MagicMock()
                self.storage = MagicMock()
                self.container = "test-container"

        return TestService(db_session)

    @pytest.mark.asyncio
    async def test_list_selected_sheets_success(self, db_session: AsyncSession):
        """[test_sheet_operations-001] 選択済みシート一覧取得の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        service.project_file_repository.list_by_project = AsyncMock(return_value=[])

        # Act
        result = await service.list_selected_sheets(project_id, user_id)

        # Assert
        assert "files" in result
        assert result["files"] == []

    @pytest.mark.asyncio
    async def test_list_selected_sheets_with_files(self, db_session: AsyncSession):
        """[test_sheet_operations-002] ファイルがある場合のシート一覧取得。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_project_file = MagicMock()
        mock_project_file.id = uuid.uuid4()
        mock_project_file.original_filename = "test.xlsx"
        mock_project_file.uploaded_at = "2024-01-01T00:00:00"

        mock_driver_tree_file = MagicMock()
        mock_driver_tree_file.id = uuid.uuid4()
        mock_driver_tree_file.sheet_name = "Sheet1"
        mock_driver_tree_file.axis_config = {
            "col1": {
                "column_name": "年度",
                "role": "カテゴリ",
                "items": ["2023", "2024"],
            }
        }

        service.project_file_repository.list_by_project = AsyncMock(return_value=[mock_project_file])
        service.file_repository.list_by_project_file = AsyncMock(return_value=[mock_driver_tree_file])

        # Act
        result = await service.list_selected_sheets(project_id, user_id)

        # Assert
        assert "files" in result
        assert len(result["files"]) == 1
        assert result["files"][0]["filename"] == "test.xlsx"

    @pytest.mark.asyncio
    async def test_select_sheet_file_not_found(self, db_session: AsyncSession):
        """[test_sheet_operations-003] シート選択時にファイルが見つからない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        service.project_file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.select_sheet(project_id, file_id, sheet_id, user_id)

        assert "ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_select_sheet_project_mismatch(self, db_session: AsyncSession):
        """[test_sheet_operations-004] シート選択時にプロジェクトIDが一致しない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_project_file = MagicMock()
        mock_project_file.project_id = uuid.uuid4()  # 異なるプロジェクトID

        service.project_file_repository.get = AsyncMock(return_value=mock_project_file)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.select_sheet(project_id, file_id, sheet_id, user_id)

        assert "該当ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_select_sheet_sheet_not_found(self, db_session: AsyncSession):
        """[test_sheet_operations-005] シート選択時にシートが見つからない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_project_file = MagicMock()
        mock_project_file.project_id = project_id

        service.project_file_repository.get = AsyncMock(return_value=mock_project_file)
        service.file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.select_sheet(project_id, file_id, sheet_id, user_id)

        assert "シートが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_sheet_file_not_found(self, db_session: AsyncSession):
        """[test_sheet_operations-006] シート削除時にファイルが見つからない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        service.project_file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_sheet(project_id, file_id, sheet_id, user_id)

        assert "ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_sheet_sheet_not_found(self, db_session: AsyncSession):
        """[test_sheet_operations-007] シート削除時にシートが見つからない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_project_file = MagicMock()
        mock_project_file.project_id = project_id

        service.project_file_repository.get = AsyncMock(return_value=mock_project_file)
        service.file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_sheet(project_id, file_id, sheet_id, user_id)

        assert "シートが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_sheet_file_not_found(self, db_session: AsyncSession):
        """[test_sheet_operations-008] シート更新時にファイルが見つからない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        service.project_file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.refresh_sheet(project_id, file_id, sheet_id, user_id)

        assert "ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_sheet_not_selected(self, db_session: AsyncSession):
        """[test_sheet_operations-009] 選択されていないシートの更新時のエラー。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_project_file = MagicMock()
        mock_project_file.project_id = project_id

        mock_driver_tree_file = MagicMock()
        mock_driver_tree_file.project_file_id = file_id
        mock_driver_tree_file.axis_config = {}  # 空 = 未選択

        service.project_file_repository.get = AsyncMock(return_value=mock_project_file)
        service.file_repository.get = AsyncMock(return_value=mock_driver_tree_file)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.refresh_sheet(project_id, file_id, sheet_id, user_id)

        assert "シートが選択されていません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_sheet_detail_file_not_found(self, db_session: AsyncSession):
        """[test_sheet_operations-010] シート詳細取得時にファイルが見つからない場合。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        service.project_file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_sheet_detail(project_id, file_id, sheet_id, user_id)

        assert "ファイルが見つかりません" in str(exc_info.value)

    def test_build_axis_config(self, db_session: AsyncSession):
        """[test_sheet_operations-011] axis_config構築の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        df_metadata = pd.DataFrame({"年度": ["2023", "2024"], "部門": ["営業", "開発"]})
        df_data = pd.DataFrame({"売上": [1000, 800], "費用": [500, 400]})

        # Act
        result = service._build_axis_config(df_metadata, df_data)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 3  # 年度、部門、科目

    def test_infer_data_type_number(self, db_session: AsyncSession):
        """[test_sheet_operations-012] 数値型推定の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        series = pd.Series([100, 200, 300])

        # Act
        result = service._infer_data_type(series)

        # Assert
        assert result == "number"

    def test_infer_data_type_string(self, db_session: AsyncSession):
        """[test_sheet_operations-013] 文字列型推定の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        series = pd.Series(["営業", "開発", "管理"])

        # Act
        result = service._infer_data_type(series)

        # Assert
        assert result == "string"

    def test_infer_role_transition(self, db_session: AsyncSession):
        """[test_sheet_operations-014] 推移役割推定の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)

        # Act
        result = service._infer_role("FY2023", "string")

        # Assert
        assert result == "推移"

    def test_infer_role_category(self, db_session: AsyncSession):
        """[test_sheet_operations-015] カテゴリ役割推定の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)

        # Act
        result = service._infer_role("部門", "string")

        # Assert
        assert result == "カテゴリ"
