"""ロール一覧APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/role - ロール一覧取得
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/role - ロール一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_roles_success(client: AsyncClient):
    """[test_role-001] ロール一覧取得の成功ケース（認証不要）。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "systemRoles" in data
    assert "projectRoles" in data


@pytest.mark.asyncio
async def test_get_roles_contains_system_roles(client: AsyncClient):
    """[test_role-002] システムロールが含まれていること。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    system_roles = data["systemRoles"]
    assert len(system_roles) > 0
    # 各ロールに必要なフィールドがあること
    for role in system_roles:
        assert "value" in role
        assert "label" in role
        assert "description" in role


@pytest.mark.asyncio
async def test_get_roles_contains_project_roles(client: AsyncClient):
    """[test_role-003] プロジェクトロールが含まれていること。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    project_roles = data["projectRoles"]
    assert len(project_roles) > 0
    # 各ロールに必要なフィールドがあること
    for role in project_roles:
        assert "value" in role
        assert "label" in role
        assert "description" in role


@pytest.mark.asyncio
async def test_get_roles_system_admin_exists(client: AsyncClient):
    """[test_role-004] system_adminロールが存在すること。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    system_roles = data["systemRoles"]
    admin_role = next((role for role in system_roles if role["value"] == "system_admin"), None)
    assert admin_role is not None


@pytest.mark.asyncio
async def test_get_roles_project_manager_exists(client: AsyncClient):
    """[test_role-005] project_managerロールが存在すること。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    project_roles = data["projectRoles"]
    manager_role = next((role for role in project_roles if role["value"] == "project_manager"), None)
    assert manager_role is not None
