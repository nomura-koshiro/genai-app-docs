"""ストレージサービス基底クラスのテスト。

StorageService抽象基底クラスのインターフェース定義を検証するテストです。
"""

from abc import ABC

import pytest

from app.services.storage.base import StorageService


class TestStorageServiceInterface:
    """StorageServiceインターフェースのテスト。"""

    def test_storage_service_is_abstract_class(self):
        """[test_base-001] StorageServiceが抽象基底クラスであることを確認。"""
        # Arrange & Act & Assert
        assert issubclass(StorageService, ABC)

    def test_storage_service_cannot_be_instantiated(self):
        """[test_base-002] StorageServiceが直接インスタンス化できないことを確認。"""
        # Arrange & Act & Assert
        with pytest.raises(TypeError):
            StorageService()  # type: ignore[abstract]

    @pytest.mark.parametrize(
        "method_name",
        [
            "upload",
            "download",
            "delete",
            "exists",
            "list_blobs",
            "get_file_path",
            "download_to_temp_file",
        ],
        ids=["upload", "download", "delete", "exists", "list_blobs", "get_file_path", "download_to_temp_file"],
    )
    def test_storage_service_has_required_methods(self, method_name):
        """[test_base-003] 必須メソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, method_name)
        assert callable(getattr(StorageService, method_name, None))


class TestConcreteImplementation:
    """具象クラス実装のテスト。"""

    def test_concrete_class_must_implement_all_methods(self):
        """[test_base-010] 具象クラスが全ての抽象メソッドを実装する必要があることを確認。"""

        # Arrange
        class IncompleteStorageService(StorageService):
            """不完全な実装（一部のメソッドのみ実装）。"""

            async def upload(self, container: str, path: str, data: bytes) -> bool:
                return True

        # Act & Assert
        with pytest.raises(TypeError):
            IncompleteStorageService()  # type: ignore[abstract]

    def test_complete_implementation_can_be_instantiated(self):
        """[test_base-011] 全てのメソッドを実装した具象クラスがインスタンス化できることを確認。"""

        # Arrange
        class CompleteStorageService(StorageService):
            """完全な実装。"""

            async def upload(self, container: str, path: str, data: bytes) -> bool:
                return True

            async def download(self, container: str, path: str) -> bytes:
                return b""

            async def delete(self, container: str, path: str) -> bool:
                return True

            async def exists(self, container: str, path: str) -> bool:
                return True

            async def list_blobs(self, container: str, prefix: str = "") -> list[str]:
                return []

            def get_file_path(self, container: str, path: str) -> str:
                return ""

            async def download_to_temp_file(self, container: str, path: str) -> str:
                return ""

        # Act
        service = CompleteStorageService()

        # Assert
        assert isinstance(service, StorageService)
