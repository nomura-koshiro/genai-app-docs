"""ローカルストレージサービスのテスト。

LocalStorageServiceの機能を検証するテストです。
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorageService


class TestLocalStorageServiceInit:
    """LocalStorageService初期化のテスト。"""

    def test_init_creates_base_directory(self):
        """[test_local-001] 初期化時にベースディレクトリが作成されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "new_uploads"

            # Act
            service = LocalStorageService(str(base_path))

            # Assert
            assert base_path.exists()
            assert service.base_path == base_path

    def test_init_with_default_path(self):
        """[test_local-002] デフォルトパスで初期化されることを確認。"""
        # Arrange & Act
        with patch.object(Path, "mkdir"):
            service = LocalStorageService()

        # Assert
        assert service.base_path == Path("./uploads")

    def test_init_with_custom_path(self):
        """[test_local-003] カスタムパスで初期化されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_uploads"

            # Act
            service = LocalStorageService(str(custom_path))

            # Assert
            assert service.base_path == custom_path

    def test_inherits_from_storage_service(self):
        """[test_local-004] StorageServiceを継承していることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Act
            service = LocalStorageService(temp_dir)

            # Assert
            assert isinstance(service, StorageService)


class TestLocalStorageServiceGetFilePath:
    """LocalStorageService.get_file_pathメソッドのテスト。"""

    def test_get_file_path_returns_correct_path(self):
        """[test_local-005] 正しいファイルパスが返されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"

            # Act
            result = service.get_file_path(container, path)

            # Assert
            expected = str(Path(temp_dir) / container / path)
            assert result == expected

    def test_get_file_path_creates_container_directory(self):
        """[test_local-006] コンテナディレクトリが作成されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "new-container"
            path = "file.txt"

            # Act
            service.get_file_path(container, path)

            # Assert
            container_path = Path(temp_dir) / container
            assert container_path.exists()


class TestLocalStorageServiceUpload:
    """LocalStorageService.uploadメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_upload_success(self):
        """[test_local-007] ファイルアップロードが成功することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"
            data = b"Hello, World!"

            # Act
            result = await service.upload(container, path, data)

            # Assert
            assert result is True
            file_path = Path(temp_dir) / container / path
            assert file_path.exists()
            assert file_path.read_bytes() == data

    @pytest.mark.asyncio
    async def test_upload_creates_parent_directories(self):
        """[test_local-008] 親ディレクトリが自動作成されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "subdir1/subdir2/test-file.txt"
            data = b"Nested file"

            # Act
            result = await service.upload(container, path, data)

            # Assert
            assert result is True
            file_path = Path(temp_dir) / container / path
            assert file_path.exists()

    @pytest.mark.asyncio
    async def test_upload_overwrites_existing_file(self):
        """[test_local-009] 既存ファイルが上書きされることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"
            initial_data = b"Initial content"
            new_data = b"New content"

            # 初回アップロード
            await service.upload(container, path, initial_data)

            # Act
            result = await service.upload(container, path, new_data)

            # Assert
            assert result is True
            file_path = Path(temp_dir) / container / path
            assert file_path.read_bytes() == new_data

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation,patch_target,error,error_message",
        [
            ("upload", "aiofiles.open", PermissionError("Access denied"), "Failed to upload file"),
            ("download", "aiofiles.open", OSError("Read error"), "Failed to download file"),
            ("delete", "aiofiles.os.remove", PermissionError("Access denied"), "Failed to delete file"),
        ],
        ids=["upload_error", "download_error", "delete_error"],
    )
    async def test_file_operation_raises_validation_error(self, operation, patch_target, error, error_message):
        """[test_local-010] ファイル操作失敗時にValidationErrorが発生することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"
            data = b"Test data"

            # ファイルを作成（download/delete用）
            if operation in ["download", "delete"]:
                await service.upload(container, path, data)

            # Act & Assert
            if operation == "download":
                with patch("aiofiles.os.path.exists", new_callable=AsyncMock, return_value=True):
                    with patch(patch_target, side_effect=error):
                        with pytest.raises(ValidationError) as exc_info:
                            await service.download(container, path)
                        assert error_message in str(exc_info.value.message)
            elif operation == "delete":
                with patch("aiofiles.os.path.exists", new_callable=AsyncMock, return_value=True):
                    with patch(patch_target, new_callable=AsyncMock, side_effect=error):
                        with pytest.raises(ValidationError) as exc_info:
                            await service.delete(container, path)
                        assert error_message in str(exc_info.value.message)
            else:  # upload
                with patch(patch_target, side_effect=error):
                    with pytest.raises(ValidationError) as exc_info:
                        await service.upload(container, path, data)
                    assert error_message in str(exc_info.value.message)


class TestLocalStorageServiceDownload:
    """LocalStorageService.downloadメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_download_success(self):
        """[test_local-011] ファイルダウンロードが成功することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"
            data = b"Test content"

            # ファイルを作成
            await service.upload(container, path, data)

            # Act
            result = await service.download(container, path)

            # Assert
            assert result == data

    @pytest.mark.asyncio
    async def test_download_not_found_error(self):
        """[test_local-012] 存在しないファイルでNotFoundErrorが発生することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "nonexistent-file.txt"

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.download(container, path)

            assert "File not found" in str(exc_info.value.message)


class TestLocalStorageServiceDelete:
    """LocalStorageService.deleteメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """[test_local-014] ファイル削除が成功することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"
            data = b"Test content"

            # ファイルを作成
            await service.upload(container, path, data)
            file_path = Path(temp_dir) / container / path
            assert file_path.exists()

            # Act
            result = await service.delete(container, path)

            # Assert
            assert result is True
            assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_not_found_error(self):
        """[test_local-015] 存在しないファイル削除でNotFoundErrorが発生することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "nonexistent-file.txt"

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.delete(container, path)

            assert "File not found" in str(exc_info.value.message)


class TestLocalStorageServiceExists:
    """LocalStorageService.existsメソッドのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "path,should_create,expected",
        [
            ("test-file.txt", True, True),
            ("nonexistent-file.txt", False, False),
        ],
        ids=["existing_file", "nonexistent_file"],
    )
    async def test_exists(self, path, should_create, expected):
        """[test_local-017] existsメソッドの各種ケースをテスト。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            data = b"Test content"

            # ファイルを作成（必要な場合のみ）
            if should_create:
                await service.upload(container, path, data)

            # Act
            result = await service.exists(container, path)

            # Assert
            assert result is expected


class TestLocalStorageServiceListBlobs:
    """LocalStorageService.list_blobsメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_list_blobs_returns_all_files(self):
        """[test_local-019] 全ファイル一覧が返されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            files = ["file1.txt", "file2.txt", "file3.txt"]

            for f in files:
                await service.upload(container, f, b"content")

            # Act
            result = await service.list_blobs(container)

            # Assert
            assert len(result) == 3
            for f in files:
                assert f in result

    @pytest.mark.asyncio
    async def test_list_blobs_with_prefix(self):
        """[test_local-020] プレフィックスフィルタが機能することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"

            # 異なるプレフィックスのファイルを作成
            await service.upload(container, "data/file1.txt", b"content")
            await service.upload(container, "data/file2.txt", b"content")
            await service.upload(container, "other/file3.txt", b"content")

            # Act
            result = await service.list_blobs(container, prefix="data/")

            # Assert
            assert len(result) == 2
            assert all("data/" in f for f in result)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "container,create_container",
        [
            ("empty-container", True),
            ("nonexistent-container", False),
        ],
        ids=["empty_container", "nonexistent_container"],
    )
    async def test_list_blobs_returns_empty(self, container, create_container):
        """[test_local-021] 空コンテナまたは存在しないコンテナで空リストが返されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)

            # コンテナディレクトリを作成（必要な場合のみ）
            if create_container:
                (Path(temp_dir) / container).mkdir(parents=True, exist_ok=True)

            # Act
            result = await service.list_blobs(container)

            # Assert
            assert result == []


class TestLocalStorageServiceDownloadToTempFile:
    """LocalStorageService.download_to_temp_fileメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_download_to_temp_file_returns_file_path(self):
        """[test_local-023] ファイルパスが返されることを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "test-file.txt"
            data = b"Test content"

            # ファイルを作成
            await service.upload(container, path, data)

            # Act
            result = await service.download_to_temp_file(container, path)

            # Assert
            expected_path = str(Path(temp_dir) / container / path)
            assert result == expected_path
            assert Path(result).exists()

    @pytest.mark.asyncio
    async def test_download_to_temp_file_not_found_error(self):
        """[test_local-024] 存在しないファイルでNotFoundErrorが発生することを確認。"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalStorageService(temp_dir)
            container = "test-container"
            path = "nonexistent-file.txt"

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.download_to_temp_file(container, path)

            assert "File not found" in str(exc_info.value.message)
