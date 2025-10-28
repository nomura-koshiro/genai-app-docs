"""ファイルAPIのテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_file_upload_endpoint(client: AsyncClient):
    """ファイルアップロードエンドポイントのテスト。"""
    # Arrange
    files = {"file": ("test.txt", b"Test file content", "text/plain")}

    # Act
    response = await client.post("/api/v1/files/upload", files=files)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "file_id" in data
    assert "size" in data
    assert data["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_file_upload_no_file(client: AsyncClient):
    """ファイルなしでのアップロード失敗のテスト。"""
    # Act
    response = await client.post("/api/v1/files/upload")

    # Assert
    assert response.status_code == 422  # Validation error
