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

    @pytest.mark.parametrize(
        "mixin_type,methods",
        [
            ("file_operations", ["upload_file", "delete_file", "list_uploaded_files"]),
            ("sheet_operations", ["select_sheet", "delete_sheet", "list_selected_sheets", "refresh_sheet", "get_sheet_detail"]),
            ("column_config", ["update_column_config"]),
        ],
        ids=["file_operations", "sheet_operations", "column_config"],
    )
    @pytest.mark.asyncio
    async def test_has_mixin_methods(
        self, db_session: AsyncSession, mock_storage_service, mixin_type: str, methods: list
    ):
        """[test_service-004] 各Mixinのメソッドが使用可能。"""
        # Arrange
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        for method in methods:
            assert hasattr(service, method)
            assert callable(getattr(service, method))


# ================================================================================
# コンテナ名テスト
# ================================================================================


class TestDriverTreeFileServiceContainer:
    """DriverTreeFileServiceのコンテナ名テスト。"""

    @pytest.mark.asyncio
    async def test_container_name_and_attribute(self, db_session: AsyncSession, mock_storage_service):
        """[test_service-005] コンテナ名が正しくクラス属性として定義されている。"""
        # Arrange & Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = DriverTreeFileService(db_session)

        # Assert
        assert service.container == "driver_tree"
        assert hasattr(DriverTreeFileService, "container")
        assert DriverTreeFileService.container == "driver_tree"
