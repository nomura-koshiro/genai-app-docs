"""プロジェクトファイルAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。

対応エンドポイント:
    - GET /api/v1/project/{project_id}/file - ファイル一覧取得
    - GET /api/v1/project/{project_id}/file/{file_id} - ファイル情報取得
    - GET /api/v1/project/{project_id}/file/{file_id}/download - ファイルダウンロード
    - POST /api/v1/project/{project_id}/file - ファイルアップロード
    - DELETE /api/v1/project/{project_id}/file/{file_id} - ファイル削除
"""

import uuid
from io import BytesIO
from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.fixture
def mock_storage_path(tmp_path):
    """ストレージパスをtmp_pathにパッチするfixture。

    Usage:
        with mock_storage_path:
            # ファイル操作を実行
    """
    return patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path))


# ================================================================================
# POST /api/v1/project/{project_id}/file - ファイルアップロード
# ================================================================================


@pytest.mark.asyncio
async def test_upload_file_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_path,
):
    """[test_project_files-001] ファイルアップロードの成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    file_content = b"Test file content for upload"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

    # Act
    with mock_storage_path:
        response = await client.post(
            f"/api/v1/project/{project.id}/file",
            files=files,
        )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["originalFilename"] == "test.pdf"
    assert data["fileSize"] == len(file_content)
    assert "id" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_upload_file_not_member(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    test_data_seeder,
):
    """[test_project_files-002] 非メンバーによるファイルアップロード失敗。"""
    # Arrange
    project, _ = project_with_owner
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()

    override_auth(other_user)
    file_content = b"Test file"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/file",
        files=files,
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_file_viewer_not_allowed(
    client: AsyncClient,
    override_auth,
    project_with_members,
    mock_storage_path,
):
    """[test_project_files-003] VIEWERロールによるファイルアップロード失敗。"""
    # Arrange
    data = project_with_members
    override_auth(data["viewer"])
    file_content = b"Test file"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    # Act
    with mock_storage_path:
        response = await client.post(
            f"/api/v1/project/{data['project'].id}/file",
            files=files,
        )

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/file - ファイル一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_files_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_path,
):
    """[test_project_files-004] ファイル一覧取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with mock_storage_path:
        for i in range(2):
            file_content = f"File content {i}".encode()
            files = {"file": (f"test{i}.txt", BytesIO(file_content), "text/plain")}
            await client.post(
                f"/api/v1/project/{project.id}/file",
                files=files,
            )

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/file")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert "total" in data
    assert "projectId" in data
    assert len(data["files"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_files_with_pagination(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_path,
):
    """[test_project_files-005] ページネーション付きファイル一覧取得。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # 5つのファイルをアップロード
    with mock_storage_path:
        for i in range(5):
            file_content = f"File {i}".encode()
            files = {"file": (f"page{i}.txt", BytesIO(file_content), "text/plain")}
            await client.post(
                f"/api/v1/project/{project.id}/file",
                files=files,
            )

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/file?skip=0&limit=2")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 2
    assert data["total"] == 5


# ================================================================================
# GET /api/v1/project/{project_id}/file/{file_id} - ファイル情報取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_file_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_path,
):
    """[test_project_files-006] ファイル情報取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with mock_storage_path:
        file_content = b"Get file test content"
        files = {"file": ("gettest.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/file",
            files=files,
        )
        file_id = upload_response.json()["id"]

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/file/{file_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["filename"] == "gettest.txt"


# ================================================================================
# GET /api/v1/project/{project_id}/file/{file_id}/download - ファイルダウンロード
# ================================================================================


@pytest.mark.asyncio
async def test_download_file_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_service,
    tmp_path,
):
    """[test_project_files-007] ファイルダウンロードの成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    file_content = b"Download test content"

    # 一時ファイルを作成してモックストレージに設定
    temp_file = tmp_path / "download_test.txt"
    temp_file.write_bytes(file_content)
    mock_storage_service.download_to_temp_file.return_value = str(temp_file)

    # ファイルをアップロード
    files = {"file": ("download.txt", BytesIO(file_content), "text/plain")}
    upload_response = await client.post(
        f"/api/v1/project/{project.id}/file",
        files=files,
    )
    file_id = upload_response.json()["id"]

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/file/{file_id}/download")

    # Assert
    assert response.status_code == 200
    assert response.content == file_content


# ================================================================================
# DELETE /api/v1/project/{project_id}/file/{file_id} - ファイル削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_file_by_uploader(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_path,
):
    """[test_project_files-008] アップロード者によるファイル削除の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    with mock_storage_path:
        file_content = b"Delete test"
        files = {"file": ("delete.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/file",
            files=files,
        )
        file_id = upload_response.json()["id"]

        # Act
        response = await client.delete(f"/api/v1/project/{project.id}/file/{file_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["fileId"] == file_id


@pytest.mark.asyncio
async def test_delete_file_by_manager(
    client: AsyncClient,
    override_auth,
    project_with_members,
    mock_storage_path,
):
    """[test_project_files-009] PROJECT_MANAGERによる他者のファイル削除の成功ケース。"""
    # Arrange
    data = project_with_members

    # memberでファイルをアップロード
    override_auth(data["member"])

    with mock_storage_path:
        file_content = b"Manager delete test"
        files = {"file": ("managerdel.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post(
            f"/api/v1/project/{data['project'].id}/file",
            files=files,
        )
        file_id = upload_response.json()["id"]

        # Act - PROJECT_MANAGERで削除
        override_auth(data["owner"])
        response = await client.delete(f"/api/v1/project/{data['project'].id}/file/{file_id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["fileId"] == file_id


@pytest.mark.asyncio
async def test_delete_file_no_permission(
    client: AsyncClient,
    override_auth,
    project_with_members,
    mock_storage_path,
):
    """[test_project_files-010] 権限のないユーザーによるファイル削除失敗。"""
    # Arrange
    data = project_with_members

    # PROJECT_MANAGERでファイルをアップロード
    override_auth(data["owner"])

    with mock_storage_path:
        file_content = b"Permission test"
        files = {"file": ("perm.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post(
            f"/api/v1/project/{data['project'].id}/file",
            files=files,
        )
        file_id = upload_response.json()["id"]

        # Act - VIEWERで削除を試みる
        override_auth(data["viewer"])
        response = await client.delete(f"/api/v1/project/{data['project'].id}/file/{file_id}")

    # Assert
    assert response.status_code == 403
