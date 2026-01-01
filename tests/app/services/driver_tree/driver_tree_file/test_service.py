"""ドライバーツリーファイルサービスのテスト。

このテストファイルは、DriverTreeFileServiceクラスのテストを行います。

対応クラス:
    - DriverTreeFileService: ファイル管理サービス
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.driver_tree.driver_tree_file.service import DriverTreeFileService

# ================================================================================
# DriverTreeFileService 初期化テスト
# ================================================================================


class TestDriverTreeFileServiceInit:
    """DriverTreeFileServiceの初期化テスト。"""

    @pytest.mark.asyncio
    async def test_init_with_default_storage(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-001] デフォルトストレージでの初期化。"""
        # Arrange & Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert service.db == db_session
        assert service.storage is not None
        assert service.container == "driver_tree"

    @pytest.mark.asyncio
    async def test_init_with_custom_storage(self, db_session: AsyncSession):
        """[test_service-002] カスタムストレージでの初期化。"""
        # Arrange
        custom_storage = AsyncMock()

        # Act
        service = DriverTreeFileService(db_session, storage=custom_storage)

        # Assert
        assert service.storage == custom_storage

    @pytest.mark.asyncio
    async def test_init_repositories(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-003] リポジトリが正しく初期化される。"""
        # Arrange & Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert service.file_repository is not None
        assert service.data_frame_repository is not None
        assert service.project_file_repository is not None


# ================================================================================
# Mixin 統合テスト
# ================================================================================


class TestDriverTreeFileServiceMixins:
    """DriverTreeFileServiceのMixin統合テスト。"""

    @pytest.mark.asyncio
    async def test_has_file_operations_methods(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-004] FileOperationsMixinのメソッドが使用可能。"""
        # Arrange
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert hasattr(service, "upload_file")
        assert hasattr(service, "delete_file")
        assert hasattr(service, "list_uploaded_files")
        assert callable(service.upload_file)
        assert callable(service.delete_file)
        assert callable(service.list_uploaded_files)

    @pytest.mark.asyncio
    async def test_has_sheet_operations_methods(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-005] SheetOperationsMixinのメソッドが使用可能。"""
        # Arrange
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert hasattr(service, "select_sheet")
        assert hasattr(service, "delete_sheet")
        assert hasattr(service, "list_selected_sheets")
        assert hasattr(service, "refresh_sheet")
        assert hasattr(service, "get_sheet_detail")
        assert callable(service.select_sheet)
        assert callable(service.delete_sheet)
        assert callable(service.list_selected_sheets)

    @pytest.mark.asyncio
    async def test_has_column_config_methods(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-006] ColumnConfigMixinのメソッドが使用可能。"""
        # Arrange
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert hasattr(service, "update_column_config")
        assert callable(service.update_column_config)


# ================================================================================
# コンテナ名テスト
# ================================================================================


class TestDriverTreeFileServiceContainer:
    """DriverTreeFileServiceのコンテナ名テスト。"""

    @pytest.mark.asyncio
    async def test_container_name(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-007] コンテナ名が正しい。"""
        # Arrange & Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert service.container == "driver_tree"

    @pytest.mark.asyncio
    async def test_container_is_class_attribute(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-008] コンテナ名がクラス属性である。"""
        # Assert
        assert hasattr(DriverTreeFileService, "container")
        assert DriverTreeFileService.container == "driver_tree"
