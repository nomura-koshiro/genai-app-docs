"""ロール一覧APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/role - ロール一覧取得（認証必須）
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/role - ロール一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_roles_success(client: AsyncClient):
    """[test_role-001] ロール一覧取得の成功ケース（認証済み）。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "systemRoles" in data
    assert "projectRoles" in data


@pytest.mark.parametrize(
    "role_type",
    ["systemRoles", "projectRoles"],
    ids=["system", "project"],
)
@pytest.mark.asyncio
async def test_get_roles_contains_role_type(client: AsyncClient, role_type: str):
    """[test_role-002,003] ロールタイプが含まれており、必要なフィールドがあること。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    roles = data[role_type]
    assert len(roles) > 0
    # 各ロールに必要なフィールドがあること
    for role in roles:
        assert "value" in role
        assert "label" in role
        assert "description" in role


@pytest.mark.parametrize(
    "role_type,role_value",
    [
        ("systemRoles", "system_admin"),
        ("projectRoles", "project_manager"),
    ],
    ids=["system_admin", "project_manager"],
)
@pytest.mark.asyncio
async def test_get_roles_specific_role_exists(
    client: AsyncClient, role_type: str, role_value: str
):
    """[test_role-004,005] 特定のロールが存在すること。"""
    # Act
    response = await client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 200
    data = response.json()
    roles = data[role_type]
    specific_role = next((role for role in roles if role["value"] == role_value), None)
    assert specific_role is not None


@pytest.mark.asyncio
async def test_get_roles_unauthenticated_returns_401(unauthenticated_client: AsyncClient):
    """[test_role-006] 未認証でのアクセスは401エラー。"""
    # Act
    response = await unauthenticated_client.get("/api/v1/admin/role")

    # Assert
    assert response.status_code == 401
