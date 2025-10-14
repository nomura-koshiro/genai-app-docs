"""Local filesystem storage backend."""

from pathlib import Path

import aiofiles

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str | Path):
        """
        Initialize local storage backend.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, file_path: Path, content: bytes) -> str:
        """Upload a file to local storage."""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        return str(file_path)

    async def download(self, file_id: str) -> bytes:
        """Download a file from local storage."""
        file_path = self.base_path / file_id

        if not await self.exists(file_id):
            raise FileNotFoundError(f"File not found: {file_id}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, file_id: str) -> None:
        """Delete a file from local storage."""
        file_path = self.base_path / file_id

        if not await self.exists(file_id):
            raise FileNotFoundError(f"File not found: {file_id}")

        file_path.unlink()

    async def exists(self, file_id: str) -> bool:
        """Check if a file exists in local storage."""
        file_path = self.base_path / file_id
        return file_path.exists() and file_path.is_file()

    async def list_files(self) -> list[dict[str, str]]:
        """List all files in local storage."""
        files = []
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.base_path)
                files.append(
                    {
                        "file_id": str(relative_path),
                        "filename": file_path.name,
                        "size": str(file_path.stat().st_size),
                    }
                )
        return files
