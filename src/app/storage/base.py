"""Base storage interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(self, file_path: Path, content: bytes) -> str:
        """
        Upload a file.

        Args:
            file_path: Path where the file should be stored
            content: File content as bytes

        Returns:
            File identifier
        """
        pass

    @abstractmethod
    async def download(self, file_id: str) -> bytes:
        """
        Download a file.

        Args:
            file_id: File identifier

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> None:
        """
        Delete a file.

        Args:
            file_id: File identifier
        """
        pass

    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_id: File identifier

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_files(self) -> list[dict[str, str]]:
        """
        List all files.

        Returns:
            List of file information dictionaries
        """
        pass
