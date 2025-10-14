"""Azure Blob Storage backend."""

from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from app.storage.base import StorageBackend


class AzureBlobStorageBackend(StorageBackend):
    """Azure Blob Storage implementation."""

    def __init__(self, connection_string: str | None = None, container_name: str = "uploads"):
        """
        Initialize Azure Blob Storage backend.

        Args:
            connection_string: Azure Storage connection string (optional if using DefaultAzureCredential)
            container_name: Container name for file storage
        """
        self.container_name = container_name

        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        else:
            # Use DefaultAzureCredential for managed identity
            credential = DefaultAzureCredential()
            account_url = "https://<account_name>.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url, credential=credential)

    async def _ensure_container_exists(self):
        """Ensure the container exists."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            await container_client.create_container()
        except Exception:
            # Container already exists or other error
            pass

    async def upload(self, file_path: Path, content: bytes) -> str:
        """Upload a file to Azure Blob Storage."""
        await self._ensure_container_exists()

        blob_name = str(file_path)
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )

        await blob_client.upload_blob(content, overwrite=True)
        return blob_name

    async def download(self, file_id: str) -> bytes:
        """Download a file from Azure Blob Storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=file_id
        )

        if not await self.exists(file_id):
            raise FileNotFoundError(f"File not found: {file_id}")

        stream = await blob_client.download_blob()
        return await stream.readall()

    async def delete(self, file_id: str) -> None:
        """Delete a file from Azure Blob Storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=file_id
        )

        if not await self.exists(file_id):
            raise FileNotFoundError(f"File not found: {file_id}")

        await blob_client.delete_blob()

    async def exists(self, file_id: str) -> bool:
        """Check if a file exists in Azure Blob Storage."""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=file_id
            )
            await blob_client.get_blob_properties()
            return True
        except Exception:
            return False

    async def list_files(self) -> list[dict[str, str]]:
        """List all files in Azure Blob Storage."""
        container_client = self.blob_service_client.get_container_client(self.container_name)

        files = []
        async for blob in container_client.list_blobs():
            files.append(
                {
                    "file_id": blob.name,
                    "filename": Path(blob.name).name,
                    "size": str(blob.size),
                }
            )
        return files
