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
    async def test_upload_raises_validation_error_on_failure(self):
        """[test_azure-005] アップロード失敗時にValidationErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"
        data = b"Test data"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()

            mock_container_client.create_container = AsyncMock(side_effect=Exception("Upload failed"))

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                await service.upload(container, path, data)

            assert "Failed to upload file" in str(exc_info.value.message)


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
    async def test_download_not_found_error_when_blob_not_exists(self):
        """[test_azure-007] Blobが存在しない場合NotFoundErrorが発生することを確認。"""
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
                await service.download(container, path)

            assert "File not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_download_not_found_error_when_container_not_exists(self):
        """[test_azure-008] コンテナが存在しない場合NotFoundErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "nonexistent-container"
        path = "test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(side_effect=ResourceNotFoundError("Container not found"))

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(NotFoundError) as exc_info:
                await service.download(container, path)

            assert "Container not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_download_raises_validation_error_on_failure(self):
        """[test_azure-009] ダウンロード失敗時にValidationErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.download_blob = AsyncMock(side_effect=Exception("Download failed"))

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                await service.download(container, path)

            assert "Failed to download file" in str(exc_info.value.message)


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

    @pytest.mark.asyncio
    async def test_delete_raises_validation_error_on_failure(self):
        """[test_azure-012] 削除失敗時にValidationErrorが発生することを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)
            mock_blob_client_instance.delete_blob = AsyncMock(side_effect=Exception("Delete failed"))

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                await service.delete(container, path)

            assert "Failed to delete file" in str(exc_info.value.message)


class TestAzureStorageServiceExists:
    """AzureStorageService.existsメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_blob(self):
        """[test_azure-013] 存在するBlobでTrueが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(return_value=True)

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.exists(container, path)

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_nonexistent_blob(self):
        """[test_azure-014] 存在しないBlobでFalseが返されることを確認。"""
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

            # Act
            result = await service.exists(container, path)

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_false_on_exception(self):
        """[test_azure-015] 例外発生時にFalseが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"
        path = "test-file.txt"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()
            mock_blob_client_instance = MagicMock()

            mock_blob_client_instance.exists = AsyncMock(side_effect=Exception("Error"))

            mock_container_client.get_blob_client.return_value = mock_blob_client_instance
            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.exists(container, path)

            # Assert
            assert result is False


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
    async def test_list_blobs_returns_empty_for_nonexistent_container(self):
        """[test_azure-018] 存在しないコンテナで空リストが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "nonexistent-container"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()

            mock_container_client.get_container_properties = AsyncMock(side_effect=ResourceNotFoundError("Container not found"))

            mock_client_instance.get_container_client.return_value = mock_container_client
            mock_blob_client.from_connection_string.return_value = mock_client_instance

            service = AzureStorageService(connection_string)

            # Act
            result = await service.list_blobs(container)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_list_blobs_returns_empty_on_exception(self):
        """[test_azure-019] 例外発生時に空リストが返されることを確認。"""
        # Arrange
        connection_string = "test_connection_string"
        container = "test-container"

        with patch("app.services.storage.azure.BlobServiceClient") as mock_blob_client:
            mock_client_instance = MagicMock()
            mock_container_client = MagicMock()

            mock_container_client.get_container_properties = AsyncMock(side_effect=Exception("Error"))

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
