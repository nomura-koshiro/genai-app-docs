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

    @pytest.mark.parametrize(
        "operation,error_type",
        [
            ("select_sheet", "file_not_found"),
            ("delete_sheet", "file_not_found"),
            ("refresh_sheet", "file_not_found"),
            ("get_sheet_detail", "file_not_found"),
        ],
        ids=["select_file_not_found", "delete_file_not_found", "refresh_file_not_found", "get_detail_file_not_found"],
    )
    @pytest.mark.asyncio
    async def test_operations_file_not_found(self, db_session: AsyncSession, operation: str, error_type: str):
        """[test_sheet_operations-003] 各操作でのファイルNotFoundErrorケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        sheet_id = uuid.uuid4()
        user_id = uuid.uuid4()

        service.project_file_repository.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            operation_method = getattr(service, operation)
            await operation_method(project_id, file_id, sheet_id, user_id)

        assert "ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.parametrize(
        "error_type",
        ["select_sheet_not_found", "delete_sheet_not_found"],
        ids=["select_sheet_not_found", "delete_sheet_not_found"],
    )
    @pytest.mark.asyncio
    async def test_operations_sheet_not_found(self, db_session: AsyncSession, error_type: str):
        """[test_sheet_operations-004] シート選択・削除時のシートNotFoundErrorケース。"""
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
            if error_type == "select_sheet_not_found":
                await service.select_sheet(project_id, file_id, sheet_id, user_id)
            else:  # delete_sheet_not_found
                await service.delete_sheet(project_id, file_id, sheet_id, user_id)

        assert "シートが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_select_sheet_project_mismatch(self, db_session: AsyncSession):
        """[test_sheet_operations-005] シート選択時にプロジェクトIDが一致しない場合。"""
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
    async def test_refresh_sheet_not_selected(self, db_session: AsyncSession):
        """[test_sheet_operations-006] 選択されていないシートの更新時のエラー。"""
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

    def test_build_axis_config(self, db_session: AsyncSession):
        """[test_sheet_operations-007] axis_config構築の成功ケース。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        df_metadata = pd.DataFrame({"年度": ["2023", "2024"], "部門": ["営業", "開発"]})
        df_data = pd.DataFrame({"売上": [1000, 800], "費用": [500, 400]})

        # Act
        result = service._build_axis_config(df_metadata, df_data)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 3  # 年度、部門、科目

    @pytest.mark.parametrize(
        "series_data,expected_type",
        [
            ([100, 200, 300], "number"),
            (["営業", "開発", "管理"], "string"),
        ],
        ids=["number", "string"],
    )
    def test_infer_data_type(self, db_session: AsyncSession, series_data: list, expected_type: str):
        """[test_sheet_operations-008] データ型推定のテスト。"""
        # Arrange
        service = self._create_mixin_instance(db_session)
        series = pd.Series(series_data)

        # Act
        result = service._infer_data_type(series)

        # Assert
        assert result == expected_type

    @pytest.mark.parametrize(
        "column_name,data_type,expected_role",
        [
            ("FY2023", "string", "推移"),
            ("部門", "string", "カテゴリ"),
        ],
        ids=["transition", "category"],
    )
    def test_infer_role(self, db_session: AsyncSession, column_name: str, data_type: str, expected_role: str):
        """[test_sheet_operations-009] 役割推定のテスト。"""
        # Arrange
        service = self._create_mixin_instance(db_session)

        # Act
        result = service._infer_role(column_name, data_type)

        # Assert
        assert result == expected_role
