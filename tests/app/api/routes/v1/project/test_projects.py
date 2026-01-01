"""プロジェクトAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。

対応エンドポイント:
    - POST /api/v1/project - プロジェクト作成
    - GET /api/v1/project - プロジェクト一覧取得
    - GET /api/v1/project/{project_id} - プロジェクト詳細取得
    - GET /api/v1/project/code/{code} - プロジェクトコード検索
    - PATCH /api/v1/project/{project_id} - プロジェクト更新
    - DELETE /api/v1/project/{project_id} - プロジェクト削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# POST /api/v1/project - プロジェクト作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, override_auth, regular_user):
    """[test_projects-001] プロジェクト作成の成功ケース。"""
    # Arrange
    override_auth(regular_user)
    project_data = {
        "name": "Test Project",
        "code": f"TEST-{uuid.uuid4().hex[:6]}",
        "description": "Test description",
    }

    # Act
    response = await client.post("/api/v1/project", json=project_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == project_data["name"]
    assert data["code"] == project_data["code"]
    assert data["isActive"] is True
    assert data["createdBy"] == str(regular_user.id)


@pytest.mark.asyncio
async def test_create_project_duplicate_code(client: AsyncClient, override_auth, regular_user):
    """[test_projects-002] 重複コードでのプロジェクト作成失敗。"""
    # Arrange
    override_auth(regular_user)
    unique_code = f"DUP-{uuid.uuid4().hex[:6]}"

    # 最初のプロジェクトを作成
    first_project = {"name": "First Project", "code": unique_code}
    await client.post("/api/v1/project", json=first_project)

    # Act - 同じコードで2回目の作成を試みる
    duplicate_project = {"name": "Duplicate Project", "code": unique_code}
    response = await client.post("/api/v1/project", json=duplicate_project)

    # Assert
    assert response.status_code == 422


# ================================================================================
# GET /api/v1/project - プロジェクト一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_projects_success(client: AsyncClient, override_auth, regular_user):
    """[test_projects-003] プロジェクト一覧取得の成功ケース。"""
    # Arrange
    override_auth(regular_user)

    # プロジェクトを作成（作成者は自動的にメンバーになる）
    for i in range(2):
        await client.post(
            "/api/v1/project",
            json={"name": f"List Project {i}", "code": f"LIST{i}-{uuid.uuid4().hex[:6]}"},
        )

    # Act
    response = await client.get("/api/v1/project")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert len(data["projects"]) >= 2


@pytest.mark.asyncio
async def test_list_projects_with_pagination(client: AsyncClient, override_auth, regular_user):
    """[test_projects-004] ページネーション付きプロジェクト一覧取得。"""
    # Arrange
    override_auth(regular_user)

    for i in range(5):
        await client.post(
            "/api/v1/project",
            json={"name": f"Page Project {i}", "code": f"PAGE{i}-{uuid.uuid4().hex[:6]}"},
        )

    # Act
    response = await client.get("/api/v1/project?skip=0&limit=3")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 3


@pytest.mark.asyncio
async def test_list_projects_with_active_filter(client: AsyncClient, override_auth, regular_user):
    """[test_projects-005] アクティブフィルタ付きプロジェクト一覧取得。"""
    # Arrange
    override_auth(regular_user)
    await client.post(
        "/api/v1/project",
        json={"name": "Active Project", "code": f"ACTIVE-{uuid.uuid4().hex[:6]}"},
    )

    # Act
    response = await client.get("/api/v1/project?is_active=true")

    # Assert
    assert response.status_code == 200
    data = response.json()
    for project in data["projects"]:
        assert project["isActive"] is True


# ================================================================================
# GET /api/v1/project/{project_id} - プロジェクト詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_project_success(client: AsyncClient, override_auth, project_with_owner):
    """[test_projects-006] プロジェクト詳細取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(project.id)
    assert data["name"] == project.name


# ================================================================================
# GET /api/v1/project/code/{code} - プロジェクトコード検索
# ================================================================================


@pytest.mark.asyncio
async def test_get_project_by_code_success(client: AsyncClient, override_auth, project_with_owner):
    """[test_projects-007] コードによるプロジェクト検索の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/code/{project.code}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == project.code


# ================================================================================
# PATCH /api/v1/project/{project_id} - プロジェクト更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_project_success(client: AsyncClient, override_auth, project_with_owner):
    """[test_projects-008] プロジェクト更新の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    update_data = {"name": "Updated Name", "description": "Updated description"}

    # Act
    response = await client.patch(f"/api/v1/project/{project.id}", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


# ================================================================================
# DELETE /api/v1/project/{project_id} - プロジェクト削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_project_success(client: AsyncClient, override_auth, regular_user):
    """[test_projects-009] プロジェクト削除の成功ケース。"""
    # Arrange
    override_auth(regular_user)

    # プロジェクト作成
    create_response = await client.post(
        "/api/v1/project",
        json={"name": "Delete Project", "code": f"DEL-{uuid.uuid4().hex[:6]}"},
    )
    project_id = create_response.json()["id"]

    # Act
    response = await client.delete(f"/api/v1/project/{project_id}")

    # Assert
    assert response.status_code == 204

    # 削除確認
    get_response = await client.get(f"/api/v1/project/{project_id}")
    assert get_response.status_code == 404
