"""プロジェクトファイルAPIエンドポイントのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。
"""

import uuid
from io import BytesIO
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models import Project, ProjectMember, ProjectRole, UserAccount


@pytest.mark.asyncio
async def test_upload_file_success(client: AsyncClient, override_auth, db_session, tmp_path, mock_azure_user):
    """ファイルアップロードAPIの成功テスト。"""
    # Arrange
    user = UserAccount(
        azure_oid=mock_azure_user["oid"],
        email=mock_azure_user["email"],
        display_name=mock_azure_user["name"],
    )
    project = Project(
        name="API Upload Project",
        code="APIUPLOAD-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # メンバーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member)
    await db_session.commit()

    # 認証をモック
    override_auth(user)

    # Act
    file_content = b"Test file content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        response = await client.post(
            f"/api/v1/projects/{project.id}/files",
            files=files,
            headers={"Authorization": "Bearer mock-token"},
        )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["original_filename"] == "test.pdf"
    assert data["file_size"] == len(file_content)
    assert data["message"] == "File uploaded successfully"


@pytest.mark.asyncio
async def test_upload_file_unauthorized(client: AsyncClient):
    """認証なしでのファイルアップロード失敗テスト。"""
    # Arrange
    project_id = uuid.uuid4()
    file_content = b"Test file"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    # Act
    response = await client.post(f"/api/v1/projects/{project_id}/files", files=files)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_file_not_member(client: AsyncClient, override_auth, db_session, mock_azure_user):
    """非メンバーのファイルアップロード失敗テスト。"""
    # Arrange
    user = UserAccount(
        azure_oid=mock_azure_user["oid"],
        email=mock_azure_user["email"],
        display_name=mock_azure_user["name"],
    )
    project = Project(
        name="Non Member Upload Project",
        code="NONMEMBERUP-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)
    # メンバーとして追加しない

    # 認証をモック
    override_auth(user)

    # Act
    file_content = b"Test file"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    response = await client.post(
        f"/api/v1/projects/{project.id}/files",
        files=files,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_files(client: AsyncClient, override_auth, db_session, tmp_path, mock_azure_user):
    """ファイル一覧取得APIのテスト。"""
    # Arrange
    user = UserAccount(
        azure_oid=mock_azure_user["oid"],
        email=mock_azure_user["email"],
        display_name=mock_azure_user["name"],
    )
    project = Project(
        name="List Files Project",
        code="LISTFILES-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # メンバーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member)
    await db_session.commit()

    # 認証をモック
    override_auth(user)

    # ファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        for i in range(2):
            file_content = f"File {i}".encode()
            files = {"file": (f"test{i}.txt", BytesIO(file_content), "text/plain")}
            await client.post(
                f"/api/v1/projects/{project.id}/files",
                files=files,
                headers={"Authorization": "Bearer mock-token"},
            )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project.id}/files",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 2
    assert data["total"] == 2
    assert data["project_id"] == str(project.id)


@pytest.mark.asyncio
async def test_list_files_with_pagination(client: AsyncClient, override_auth, db_session, tmp_path, mock_azure_user):
    """ファイル一覧取得APIのページネーションテスト。"""
    # Arrange
    user = UserAccount(
        azure_oid=mock_azure_user["oid"],
        email=mock_azure_user["email"],
        display_name=mock_azure_user["name"],
    )
    project = Project(
        name="Page Files Project",
        code="PAGEFILES-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # メンバーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member)
    await db_session.commit()

    # 認証をモック
    override_auth(user)

    # 5つのファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        for i in range(5):
            file_content = f"File {i}".encode()
            files = {"file": (f"page{i}.txt", BytesIO(file_content), "text/plain")}
            await client.post(
                f"/api/v1/projects/{project.id}/files",
                files=files,
                headers={"Authorization": "Bearer mock-token"},
            )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project.id}/files?skip=0&limit=2",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_get_file_not_found(client: AsyncClient, override_auth, db_session, mock_azure_user):
    """存在しないファイル取得APIのテスト。"""
    # Arrange
    user = UserAccount(
        azure_oid=mock_azure_user["oid"],
        email=mock_azure_user["email"],
        display_name=mock_azure_user["name"],
    )
    project = Project(
        name="Not Found File Project",
        code="NOTFOUNDFILE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # メンバーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.VIEWER,
    )
    db_session.add(member)
    await db_session.commit()

    # 認証をモック
    override_auth(user)

    # Act
    non_existent_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/projects/{project.id}/files/{non_existent_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_file_by_admin(client: AsyncClient, override_auth, db_session, tmp_path, mock_azure_user):
    """ADMINによる他人のファイル削除APIのテスト。"""
    # Arrange
    uploader = UserAccount(
        azure_oid="uploader-api-oid",
        email="uploaderapi@company.com",
        display_name="Uploader API",
    )
    admin = UserAccount(
        azure_oid=mock_azure_user["oid"],
        email=mock_azure_user["email"],
        display_name=mock_azure_user["name"],
    )
    project = Project(
        name="Admin Delete File Project",
        code="ADMINDELFILE-001",
    )
    db_session.add(uploader)
    db_session.add(admin)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(uploader)
    await db_session.refresh(admin)
    await db_session.refresh(project)

    # uploaderをMEMBER、adminをADMINとして追加
    uploader_member = ProjectMember(
        project_id=project.id,
        user_id=uploader.id,
        role=ProjectRole.MEMBER,
    )
    admin_member = ProjectMember(
        project_id=project.id,
        user_id=admin.id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(uploader_member)
    db_session.add(admin_member)
    await db_session.commit()

    # uploaderでログインしてファイルをアップロード
    override_auth(uploader)

    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        file_content = b"Admin delete test"
        files = {"file": ("admindel.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post(
            f"/api/v1/projects/{project.id}/files",
            files=files,
            headers={"Authorization": "Bearer mock-token"},
        )
        file_id = upload_response.json()["id"]

    # Act - adminで削除
    override_auth(admin)

    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        response = await client.delete(
            f"/api/v1/projects/{project.id}/files/{file_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

    # Assert
    assert response.status_code == 200
