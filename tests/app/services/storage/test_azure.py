"""Azure Blob Storageサービスのテスト。

AzureStorageServiceの機能を検証するテストです。
モックを使用してAzure SDKとの統合をテストします。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError

from app.core.exceptions import NotFoundError, ValidationError
from app.services.storage.azure import AzureStorageService
from app.services.storage.base import StorageService


class TestAzureStorageServiceInit:
    """AzureStorageService初期化のテスト。"""

    def test_init_creates_blob_service_client(self):
        """[test_azure-001] 初期化時にBlobServiceClientが作成されることを確認。"""
        # Arrange
        connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net"

        # Act & Assert
        with patch("app.services.storage.azure.BlobServiceClient") as mock_client:
            mock_client.from_connection_string.return_value = MagicMock()
            service = AzureStorageService(connection_string)

            mock_client.from_connection_string.assert_called_once_with(connection_string)
            assert service.client is not None

    def test_inherits_from_storage_service(self):
        """[test_azure-002] StorageServiceを継承していることを確認。"""
        # Arrange
        connection_string = "test_connection_string"

        # Act
        with patch("app.services.storage.azure.BlobServiceClient"):
            service = AzureStorageService(connection_string)

            # Assert
            assert isinstance(service, StorageService)


class TestAzureStorageServiceGetContainerClient:
    """AzureStorageService._get_container_clientメソッドのテスト。"""

    def test_get_container_client_returns_client(self):
        """[test_azure-003] コンテナクライアントが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = service._get_container_client(container)

            # Assert
            mock_client_instance.get_container_client.assert_called_once_with(container)
            assert result == mock_container_client


class TestAzureStorageServiceUpload:
    """AzureStorageService.uploadメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_upload_success(self):
        """[test_azure-004] ファイルアップロードが成功することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"
        data = b"Hello, World!"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_container_client.create_container = AsyncMock()
            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_blob_client_instance.upload_blob = AsyncMock()

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.upload(container, path, data)

            # Assert
            assert result is True
            mock_container_client.create_container.assert_called_once_with(exist_ok=True)
            mock_blob_client_instance.upload_blob.assert_called_once_with(data, overwrite=True)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation,setup_mock,error_message",
        [
            (
                "upload",
                lambda mock_container: setattr(mock_container, "create_container", AsyncMock(side_effect=Exception("Upload failed"))),
                "Failed to upload file",
            ),
            (
                "download",
                lambda mock_container: None,  # download用のセットアップは別途必要
                "Failed to download file",
            ),
            (
                "delete",
                lambda mock_container: None,  # delete用のセットアップは別途必要
                "Failed to delete file",
            ),
        ],
        ids=["upload_error", "download_error", "delete_error"],
    )
    async def test_file_operation_raises_validation_error(self, operation, setup_mock, error_message):
        """[test_azure-005] ファイル操作失敗時にValidationErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"
        data = b"Test data"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            if operation == "upload":
                mock_container_client.create_container = AsyncMock(side_effect=Exception("Upload failed"))
            elif operation == "download":
                mock_blob_client_instance.exists = AsyncMock(return_value=True)
                mock_blob_client_instance.download_blob = AsyncMock(side_effect=Exception("Download failed"))
                mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            elif operation == "delete":
                mock_blob_client_instance.exists = AsyncMock(return_value=True)
                mock_blob_client_instance.delete_blob = AsyncMock(side_effect=Exception("Delete failed"))
                mock_container_client.get_blob_client.return_value = mock_blob_client_instance

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                if operation == "upload":
                    await service.upload(container, path, data)
                elif operation == "download":
                    await service.download(container, path)
                elif operation == "delete":
                    await service.delete(container, path)

            assert error_message in str(exc_info.value.message)


class TestAzureStorageServiceDownload:
    """AzureStorageService.downloadメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_download_success(self):
        """[test_azure-006] ファイルダウンロードが成功することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"
        expected_data = b"Test content"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()
            mock_downloader = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.download_blob = AsyncMock(return_value=mock_downloader)
            mock_downloader.readall = AsyncMock(return_value=expected_data)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.download(container, path)

            # Assert
            assert result == expected_data

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "container,path,exists_behavior,expected_error",
        [
            ("test-container", "nonexistent-file.txt", ("return", False), "File not found"),
            ("nonexistent-container", "test-file.txt", ("raise", ResourceNotFoundError("Container not found")), "Container not found"),
        ],
        ids=["blob_not_exists", "container_not_exists"],
    )
    async def test_download_not_found_error(self, container, path, exists_behavior, expected_error):
        """[test_azure-007] Blobまたはコンテナが存在しない場合NotFoundErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            behavior_type, behavior_value = exists_behavior
            if behavior_type == "return":
                mock_blob_client_instance.exists = AsyncMock(return_value=behavior_value)
            else:  # raise
                mock_blob_client_instance.exists = AsyncMock(side_effect=behavior_value)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.download(container, path)

            assert expected_error in str(exc_info.value.message)


class TestAzureStorageServiceDelete:
    """AzureStorageService.deleteメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """[test_azure-010] ファイル削除が成功することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.delete_blob = AsyncMock()

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.delete(container, path)

            # Assert
            assert result is True
            mock_blob_client_instance.delete_blob.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_error(self):
        """[test_azure-011] 存在しないファイル削除でNotFoundErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "nonexistent-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=False)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.delete(container, path)

            assert "File not found" in str(exc_info.value.message)


class TestAzureStorageServiceExists:
    """AzureStorageService.existsメソッドのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "path,exists_return,expected",
        [
            ("test-file.txt", True, True),
            ("nonexistent-file.txt", False, False),
            ("error-file.txt", Exception("Error"), False),
        ],
        ids=["existing_blob", "nonexistent_blob", "exception"],
    )
    async def test_exists(self, path, exists_return, expected):
        """[test_azure-013] existsメソッドの各種ケースをテスト。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            if isinstance(exists_return, Exception):
                mock_blob_client_instance.exists = AsyncMock(side_effect=exists_return)
            else:
                mock_blob_client_instance.exists = AsyncMock(return_value=exists_return)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.exists(container, path)

            # Assert
            assert result is expected


class TestAzureStorageServiceListBlobs:
    """AzureStorageService.list_blobsメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_list_blobs_returns_blob_names(self):
        """[test_azure-016] Blob名一覧が返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        expected_blobs = ["file1.txt", "file2.txt", "file3.txt"]

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()

            # Blobオブジェクトをモック
            mock_blobs = [MagicMock(name=name) for name in expected_blobs]
            for mock_blob, name in zip(mock_blobs, expected_blobs, strict=False):
                mock_blob.name = name

            # 非同期イテレータをモック
            async def mock_list_blobs(*args, **kwargs):
                for blob in mock_blobs:
                    yield blob

            mock_container_client.list_blobs = mock_list_blobs
            mock_container_client.get_container_properties = AsyncMock()

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.list_blobs(container)

            # Assert
            assert result == expected_blobs

    @pytest.mark.asyncio
    async def test_list_blobs_with_prefix(self):
        """[test_azure-017] プレフィックスフィルタが機能することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        prefix = "data/"
        expected_blobs = ["data/file1.txt", "data/file2.txt"]

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()

            mock_blobs = [MagicMock(name=name) for name in expected_blobs]
            for mock_blob, name in zip(mock_blobs, expected_blobs, strict=False):
                mock_blob.name = name

            async def mock_list_blobs(*args, **kwargs):
                for blob in mock_blobs:
                    yield blob

            mock_container_client.list_blobs = mock_list_blobs
            mock_container_client.get_container_properties = AsyncMock()

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.list_blobs(container, prefix=prefix)

            # Assert
            assert result == expected_blobs

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "container,exception",
        [
            ("nonexistent-container", ResourceNotFoundError("Container not found")),
            ("test-container", Exception("Error")),
        ],
        ids=["nonexistent_container", "exception"],
    )
    async def test_list_blobs_returns_empty_on_error(self, container, exception):
        """[test_azure-018] エラー時に空リストが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()

            mock_container_client.get_container_properties = AsyncMock(side_effect=exception)

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.list_blobs(container)

            # Assert
            assert result == []


class TestAzureStorageServiceGetFilePath:
    """AzureStorageService.get_file_pathメソッドのテスト。"""

    def test_get_file_path_returns_blob_url(self):
        """[test_azure-020] Blob URLが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"
        expected_url = "https://account.blob.core.windows.net/test-container/test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.url = expected_url

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = service.get_file_path(container, path)

            # Assert
            assert result == expected_url


class TestAzureStorageServiceDownloadToTempFile:
    """AzureStorageService.download_to_temp_fileメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_download_to_temp_file_success(self):
        """[test_azure-021] 一時ファイルへのダウンロードが成功することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.xlsx"
        expected_data = b"Test content"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()
            mock_downloader = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.download_blob = AsyncMock(return_value=mock_downloader)
            mock_downloader.readall = AsyncMock(return_value=expected_data)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.download_to_temp_file(container, path)

            # Assert
            assert result.endswith(".xlsx")
            assert Path(result).exists()
            assert Path(result).read_bytes() == expected_data

            # Cleanup
            Path(result).unlink()

    @pytest.mark.asyncio
    async def test_download_to_temp_file_not_found_error(self):
        """[test_azure-022] 存在しないファイルでNotFoundErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "nonexistent-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=False)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.download_to_temp_file(container, path)

            assert "File not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_download_to_temp_file_preserves_extension(self):
        """[test_azure-023] 拡張子が保持されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "data/subdir/test-file.csv"
        expected_data = b"col1,col2\n1,2"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()
            mock_downloader = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.download_blob = AsyncMock(return_value=mock_downloader)
            mock_downloader.readall = AsyncMock(return_value=expected_data)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.download_to_temp_file(container, path)

            # Assert
            assert result.endswith(".csv")

            # Cleanup
            Path(result).unlink()

    @pytest.mark.asyncio
    async def test_download_to_temp_file_raises_validation_error_on_write_failure(self):
        """[test_azure-024] 書き込み失敗時にValidationErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"
        expected_data = b"Test content"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()
            mock_downloader = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.download_blob = AsyncMock(return_value=mock_downloader)
            mock_downloader.readall = AsyncMock(return_value=expected_data)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with patch("aiofiles.open", side_effect=OSError("Write error")):
                with pytest.raises(ValidationError) as exc_info:
                    await service.download_to_temp_file(container, path)

                assert "Failed to write to temporary file" in str(exc_info.value.message)
