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
@pytest.mark.parametrize(
    "user_role,expected_status,check_response",
    [
        ("owner", 201, True),
        ("non_member", 403, False),
        ("viewer", 403, False),
    ],
    ids=["owner_success", "non_member_forbidden", "viewer_forbidden"],
)
async def test_upload_file_access_control(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    project_with_members,
    test_data_seeder,
    mock_storage_path,
    user_role,
    expected_status,
    check_response,
):
    """[test_project_files-001,002,003] ファイルアップロードアクセス制御（owner・非メンバー・viewer）。"""
    # Arrange
    file_content = b"Test file content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

    if user_role == "owner":
        project, owner = project_with_owner
        override_auth(owner)
    elif user_role == "non_member":
        project, _ = project_with_owner
        other_user = await test_data_seeder.create_user(display_name="Other User")
        await test_data_seeder.db.commit()
        override_auth(other_user)
    else:  # viewer
        data = project_with_members
        project = data["project"]
        override_auth(data["viewer"])

    # Act
    with mock_storage_path:
        response = await client.post(
            f"/api/v1/project/{project.id}/file",
            files=files,
        )

    # Assert
    assert response.status_code == expected_status
    if check_response:
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["fileSize"] == len(file_content)
        assert "id" in data


# ================================================================================
# GET /api/v1/project/{project_id}/file - ファイル一覧取得
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_count,query_params,expected_file_count",
    [
        (2, {}, 2),
        (5, {"skip": 0, "limit": 2}, 2),
    ],
    ids=["no_pagination", "with_pagination"],
)
async def test_list_files(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_path,
    file_count,
    query_params,
    expected_file_count,
):
    """[test_project_files-004,005] ファイル一覧取得（基本・ページネーション）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with mock_storage_path:
        for i in range(file_count):
            file_content = f"File content {i}".encode()
            files = {"file": (f"test{i}.txt", BytesIO(file_content), "text/plain")}
            await client.post(
                f"/api/v1/project/{project.id}/file",
                files=files,
            )

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/file", params=query_params)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert "total" in data
    assert "projectId" in data
    assert len(data["files"]) == expected_file_count
    assert data["total"] == file_count


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
@pytest.mark.parametrize(
    "uploader_role,deleter_role,expected_status",
    [
        ("owner", "owner", 200),
        ("member", "owner", 200),
        ("owner", "viewer", 403),
    ],
    ids=["uploader_success", "manager_success", "no_permission"],
)
async def test_delete_file_permissions(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    project_with_members,
    mock_storage_path,
    uploader_role,
    deleter_role,
    expected_status,
):
    """[test_project_files-008,009,010] ファイル削除権限（アップロード者・マネージャー・権限なし）。"""
    # Arrange
    if uploader_role == "owner" and deleter_role in ["owner", "viewer"]:
        # owner/viewerテストにはproject_with_membersを使用
        data = project_with_members
        project = data["project"]
        uploader = data["owner"]
        deleter = data["owner"] if deleter_role == "owner" else data["viewer"]
    else:  # member -> owner
        data = project_with_members
        project = data["project"]
        uploader = data["member"]
        deleter = data["owner"]

    # ファイルをアップロード
    override_auth(uploader)

    with mock_storage_path:
        file_content = b"Delete test"
        files = {"file": ("delete.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/file",
            files=files,
        )
        file_id = upload_response.json()["id"]

        # Act - 削除者で削除
        override_auth(deleter)
        response = await client.delete(f"/api/v1/project/{project.id}/file/{file_id}")

    # Assert
    assert response.status_code == expected_status
    if expected_status == 200:
        result = response.json()
        assert result["fileId"] == file_id
