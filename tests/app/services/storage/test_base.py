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

    def test_storage_service_has_upload_method(self):
        """[test_base-003] uploadメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "upload")
        assert callable(getattr(StorageService, "upload", None))

    def test_storage_service_has_download_method(self):
        """[test_base-004] downloadメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "download")
        assert callable(getattr(StorageService, "download", None))

    def test_storage_service_has_delete_method(self):
        """[test_base-005] deleteメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "delete")
        assert callable(getattr(StorageService, "delete", None))

    def test_storage_service_has_exists_method(self):
        """[test_base-006] existsメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "exists")
        assert callable(getattr(StorageService, "exists", None))

    def test_storage_service_has_list_blobs_method(self):
        """[test_base-007] list_blobsメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "list_blobs")
        assert callable(getattr(StorageService, "list_blobs", None))

    def test_storage_service_has_get_file_path_method(self):
        """[test_base-008] get_file_pathメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "get_file_path")
        assert callable(getattr(StorageService, "get_file_path", None))

    def test_storage_service_has_download_to_temp_file_method(self):
        """[test_base-009] download_to_temp_fileメソッドが定義されていることを確認。"""
        # Arrange & Act & Assert
        assert hasattr(StorageService, "download_to_temp_file")
        assert callable(getattr(StorageService, "download_to_temp_file", None))


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
