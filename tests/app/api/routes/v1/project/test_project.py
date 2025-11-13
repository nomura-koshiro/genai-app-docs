"""プロジェクトAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models import UserAccount


@pytest.fixture
async def mock_current_user(db_session):
    """モック認証ユーザー（DB保存済み）。"""
    user = User(
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email="test@example.com",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_project_endpoint_success(client: AsyncClient, override_auth, mock_current_user):
    """プロジェクト作成エンドポイントの成功ケース。"""
    # Arrange
    override_auth(mock_current_user)

    project_data = {
        "name": "Test Project",
        "code": f"TEST-{uuid.uuid4().hex[:6]}",
        "description": "Test description",
    }

    # Act
    response = await client.post("/api/v1/projects", json=project_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == project_data["name"]
    assert data["code"] == project_data["code"]
    assert data["description"] == project_data["description"]


@pytest.mark.asyncio
async def test_create_project_duplicate_code(client: AsyncClient, override_auth, mock_current_user):
    """重複コードでのプロジェクト作成失敗のテスト。"""
    # Arrange
    override_auth(mock_current_user)

    unique_code = f"DUP-{uuid.uuid4().hex[:6]}"
    project_data = {
        "name": "First Project",
        "code": unique_code,
        "description": "First project",
    }

    # 最初のプロジェクトを作成
    await client.post("/api/v1/projects", json=project_data)

    # Act - 同じコードで2回目の作成を試みる
    duplicate_project = {
        "name": "Duplicate Project",
        "code": unique_code,
        "description": "Duplicate project",
    }
    response = await client.post("/api/v1/projects", json=duplicate_project)

    # Assert
    assert response.status_code == 422  # Validation error for duplicate code


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """認証なしでのアクセステスト。"""
    # Act - 認証なしでプロジェクト作成を試みる
    project_data = {
        "name": "Unauthorized Project",
        "code": f"UNAUTH-{uuid.uuid4().hex[:6]}",
        "description": "Unauthorized project",
    }
    response = await client.post("/api/v1/projects", json=project_data)

    # Assert - 認証エラー
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_projects_endpoint(client: AsyncClient, override_auth, mock_current_user):
    """プロジェクト一覧取得エンドポイントのテスト。"""
    # Arrange
    override_auth(mock_current_user)

    # プロジェクトを作成
    project1 = {
        "name": "List Project 1",
        "code": f"LIST1-{uuid.uuid4().hex[:6]}",
        "description": "List project 1",
    }
    project2 = {
        "name": "List Project 2",
        "code": f"LIST2-{uuid.uuid4().hex[:6]}",
        "description": "List project 2",
    }

    await client.post("/api/v1/projects", json=project1)
    await client.post("/api/v1/projects", json=project2)

    # Act
    response = await client.get("/api/v1/projects")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_projects_with_pagination(client: AsyncClient, override_auth, mock_current_user):
    """ページネーション付きプロジェクト一覧取得のテスト。"""
    # Arrange
    override_auth(mock_current_user)

    # プロジェクトを複数作成
    for i in range(5):
        project_data = {
            "name": f"Pagination Project {i}",
            "code": f"PAGE{i}-{uuid.uuid4().hex[:6]}",
            "description": f"Pagination project {i}",
        }
        await client.post("/api/v1/projects", json=project_data)

    # Act - ページネーション付きで取得
    response = await client.get("/api/v1/projects?skip=0&limit=3")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 少なくとも3件は取得できる
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, override_auth, mock_current_user):
    """存在しないプロジェクトの取得テスト。"""
    # Arrange
    override_auth(mock_current_user)

    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/projects/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project_endpoint(client: AsyncClient, override_auth, mock_current_user):
    """プロジェクト更新エンドポイントのテスト。"""
    # Arrange
    override_auth(mock_current_user)

    # プロジェクトを作成
    project_data = {
        "name": "Original Name",
        "code": f"UPD-{uuid.uuid4().hex[:6]}",
        "description": "Original description",
    }
    create_response = await client.post("/api/v1/projects", json=project_data)
    created_project = create_response.json()
    project_id = created_project["id"]

    # Act - 更新
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
    }
    response = await client.patch(f"/api/v1/projects/{project_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
