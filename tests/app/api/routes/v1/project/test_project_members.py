"""プロジェクトメンバーAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。

対応エンドポイント:
    - GET /api/v1/project/{project_id}/member - メンバー一覧取得
    - GET /api/v1/project/{project_id}/member/me - 自分のロール取得
    - POST /api/v1/project/{project_id}/member - メンバー追加
    - POST /api/v1/project/{project_id}/member/bulk - メンバー複数人追加
    - PATCH /api/v1/project/{project_id}/member/{member_id} - ロール更新
    - DELETE /api/v1/project/{project_id}/member/{member_id} - メンバー削除
    - DELETE /api/v1/project/{project_id}/member/me - プロジェクト退出
"""


import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import ProjectMember

# ================================================================================
# GET /api/v1/project/{project_id}/member - メンバー一覧取得
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_params,expected_member_count,expected_total",
    [
        ({}, 4, 4),
        ({"skip": 0, "limit": 2}, 2, 4),
    ],
    ids=["no_pagination", "with_pagination"],
)
async def test_get_project_members(
    client: AsyncClient,
    override_auth,
    project_with_members,
    query_params,
    expected_member_count,
    expected_total,
):
    """[test_project_members-001,002] メンバー一覧取得（基本・ページネーション）。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    # Act
    response = await client.get(f"/api/v1/project/{data['project'].id}/member", params=query_params)

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "members" in result
    assert "total" in result
    assert len(result["members"]) == expected_member_count
    assert result["total"] == expected_total
    for member in result["members"]:
        assert "id" in member
        assert "userId" in member
        assert "role" in member


# ================================================================================
# GET /api/v1/project/{project_id}/member/me - 自分のロール取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_my_role_success(client: AsyncClient, override_auth, project_with_owner):
    """[test_project_members-003] 自分のロール取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/member/me")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["projectId"] == str(project.id)
    assert data["userId"] == str(owner.id)
    assert data["role"] == "project_manager"


# ================================================================================
# POST /api/v1/project/{project_id}/member - メンバー追加
# ================================================================================


@pytest.mark.asyncio
async def test_add_member_success(client: AsyncClient, override_auth, project_with_owner, test_data_seeder):
    """[test_project_members-004] メンバー追加の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    new_user = await test_data_seeder.create_user(display_name="New Member")
    await test_data_seeder.db.commit()

    override_auth(owner)
    payload = {"user_id": str(new_user.id), "role": "member"}

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/member", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["projectId"] == str(project.id)
    assert data["userId"] == str(new_user.id)
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_add_member_duplicate(client: AsyncClient, override_auth, project_with_members):
    """[test_project_members-005] 既存メンバーの追加（422エラー）。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    payload = {"user_id": str(data["member"].id), "role": "member"}

    # Act
    response = await client.post(f"/api/v1/project/{data['project'].id}/member", json=payload)

    # Assert
    assert response.status_code == 422


# ================================================================================
# POST /api/v1/project/{project_id}/member/bulk - メンバー複数人追加
# ================================================================================


@pytest.mark.asyncio
async def test_add_members_bulk_success(client: AsyncClient, override_auth, project_with_owner, test_data_seeder):
    """[test_project_members-006] メンバー複数人追加の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    users = [await test_data_seeder.create_user(display_name=f"Bulk User {i}") for i in range(3)]
    await test_data_seeder.db.commit()

    override_auth(owner)
    payload = {
        "members": [
            {"user_id": str(users[0].id), "role": "member"},
            {"user_id": str(users[1].id), "role": "viewer"},
            {"user_id": str(users[2].id), "role": "project_moderator"},
        ]
    }

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/member/bulk", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["totalRequested"] == 3
    assert data["totalAdded"] == 3
    assert data["totalFailed"] == 0


@pytest.mark.asyncio
async def test_add_members_bulk_partial_success(client: AsyncClient, override_auth, project_with_members, test_data_seeder):
    """[test_project_members-007] メンバー複数人追加の部分成功（一部重複）。"""
    # Arrange
    data = project_with_members
    new_user = await test_data_seeder.create_user()
    await test_data_seeder.db.commit()

    override_auth(data["owner"])
    payload = {
        "members": [
            {"user_id": str(data["member"].id), "role": "member"},  # 重複
            {"user_id": str(new_user.id), "role": "viewer"},  # 成功
        ]
    }

    # Act
    response = await client.post(f"/api/v1/project/{data['project'].id}/member/bulk", json=payload)

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert result["totalRequested"] == 2
    assert result["totalAdded"] == 1
    assert result["totalFailed"] == 1


@pytest.mark.asyncio
async def test_add_members_bulk_empty_list(client: AsyncClient, override_auth, project_with_owner):
    """[test_project_members-008] 空リストでのメンバー複数人追加（422エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/member/bulk", json={"members": []})

    # Assert
    assert response.status_code == 422


# ================================================================================
# PATCH /api/v1/project/{project_id}/member/{member_id} - ロール更新
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_project_type,target_user_key,new_role,expected_status",
    [
        ("with_members", "member", "project_moderator", 200),
        ("with_owner", "owner", "member", 422),
    ],
    ids=["success", "last_manager_error"],
)
async def test_update_member_role(
    client: AsyncClient,
    override_auth,
    project_with_members,
    project_with_owner,
    db_session,
    use_project_type,
    target_user_key,
    new_role,
    expected_status,
):
    """[test_project_members-009,010] メンバーロール更新（成功・最後のマネージャーエラー）。"""
    # Arrange
    if use_project_type == "with_members":
        data = project_with_members
        project = data["project"]
        target_user = data[target_user_key]
        override_auth(data["owner"])
    else:  # with_owner
        project, owner = project_with_owner
        target_user = owner
        override_auth(owner)

    # member_idを取得
    result = await db_session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == target_user.id,
        )
    )
    member_record = result.scalar_one()

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/member/{member_record.id}",
        json={"role": new_role},
    )

    # Assert
    assert response.status_code == expected_status
    if expected_status == 200:
        result_data = response.json()
        assert result_data["role"] == new_role


# ================================================================================
# DELETE /api/v1/project/{project_id}/member/{member_id} - メンバー削除
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_project_type,target_user_key,expected_status",
    [
        ("with_members", "viewer", 204),
        ("with_owner", "owner", 422),
    ],
    ids=["success", "self_deletion_error"],
)
async def test_remove_member(
    client: AsyncClient,
    override_auth,
    project_with_members,
    project_with_owner,
    db_session,
    use_project_type,
    target_user_key,
    expected_status,
):
    """[test_project_members-011,012] メンバー削除（成功・自分自身削除エラー）。"""
    # Arrange
    if use_project_type == "with_members":
        data = project_with_members
        project = data["project"]
        target_user = data[target_user_key]
        override_auth(data["owner"])
    else:  # with_owner
        project, owner = project_with_owner
        target_user = owner
        override_auth(owner)

    # member_idを取得
    result = await db_session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == target_user.id,
        )
    )
    member_record = result.scalar_one()

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/member/{member_record.id}")

    # Assert
    assert response.status_code == expected_status


# ================================================================================
# DELETE /api/v1/project/{project_id}/member/me - プロジェクト退出
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_project_type,auth_user_key,expected_status",
    [
        ("with_members", "member", 204),
        ("with_owner", "owner", 422),
    ],
    ids=["success", "last_manager_error"],
)
async def test_leave_project(
    client: AsyncClient,
    override_auth,
    project_with_members,
    project_with_owner,
    use_project_type,
    auth_user_key,
    expected_status,
):
    """[test_project_members-013,014] プロジェクト退出（成功・最後のマネージャーエラー）。"""
    # Arrange
    if use_project_type == "with_members":
        data = project_with_members
        project = data["project"]
        override_auth(data[auth_user_key])
    else:  # with_owner
        project, owner = project_with_owner
        override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/member/me")

    # Assert
    assert response.status_code == expected_status
