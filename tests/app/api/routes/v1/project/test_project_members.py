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

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import ProjectMember

# ================================================================================
# GET /api/v1/project/{project_id}/member - メンバー一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_project_members_success(client: AsyncClient, override_auth, project_with_members):
    """[test_project_members-001] メンバー一覧取得の成功ケース。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    # Act
    response = await client.get(f"/api/v1/project/{data['project'].id}/member")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "members" in result
    assert "total" in result
    assert result["total"] == 4  # owner + moderator + member + viewer
    for member in result["members"]:
        assert "id" in member
        assert "userId" in member
        assert "role" in member


@pytest.mark.asyncio
async def test_get_project_members_with_pagination(client: AsyncClient, override_auth, project_with_members):
    """[test_project_members-002] ページネーション付きメンバー一覧取得。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    # Act
    response = await client.get(f"/api/v1/project/{data['project'].id}/member?skip=0&limit=2")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert len(result["members"]) == 2
    assert result["total"] == 4


@pytest.mark.asyncio
async def test_get_project_members_unauthorized(client: AsyncClient, project_with_owner):
    """[test_project_members-003] 認証なしでのメンバー一覧取得失敗。"""
    # Arrange
    project, _ = project_with_owner

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/member")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/member/me - 自分のロール取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_my_role_success(client: AsyncClient, override_auth, project_with_owner):
    """[test_project_members-004] 自分のロール取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_my_role_not_member(client: AsyncClient, override_auth, project_with_owner, test_data_seeder):
    """[test_project_members-005] メンバーでないユーザーのロール取得（404エラー）。"""
    # Arrange
    project, _ = project_with_owner
    other_user = await test_data_seeder.create_user()
    await test_data_seeder.db.commit()

    override_auth(other_user)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/member/me")

    # Assert
    assert response.status_code == 404


# ================================================================================
# POST /api/v1/project/{project_id}/member - メンバー追加
# ================================================================================


@pytest.mark.asyncio
async def test_add_member_success(client: AsyncClient, override_auth, project_with_owner, test_data_seeder):
    """[test_project_members-006] メンバー追加の成功ケース。"""
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
    """[test_project_members-007] 既存メンバーの追加（422エラー）。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    payload = {"user_id": str(data["member"].id), "role": "member"}

    # Act
    response = await client.post(f"/api/v1/project/{data['project'].id}/member", json=payload)

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_member_unauthorized(client: AsyncClient, project_with_owner, test_data_seeder):
    """[test_project_members-008] 認証なしでのメンバー追加失敗。"""
    # Arrange
    project, _ = project_with_owner
    new_user = await test_data_seeder.create_user()
    await test_data_seeder.db.commit()

    payload = {"user_id": str(new_user.id), "role": "member"}

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/member", json=payload)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_member_no_permission(client: AsyncClient, override_auth, project_with_members, test_data_seeder):
    """[test_project_members-009] 権限のないユーザーによるメンバー追加（403エラー）。"""
    # Arrange
    data = project_with_members
    new_user = await test_data_seeder.create_user()
    await test_data_seeder.db.commit()

    # 一般メンバーでメンバー追加を試みる
    override_auth(data["member"])
    payload = {"user_id": str(new_user.id), "role": "member"}

    # Act
    response = await client.post(f"/api/v1/project/{data['project'].id}/member", json=payload)

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/project/{project_id}/member/bulk - メンバー複数人追加
# ================================================================================


@pytest.mark.asyncio
async def test_add_members_bulk_success(client: AsyncClient, override_auth, project_with_owner, test_data_seeder):
    """[test_project_members-010] メンバー複数人追加の成功ケース。"""
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
    """[test_project_members-011] メンバー複数人追加の部分成功（一部重複）。"""
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
    """[test_project_members-012] 空リストでのメンバー複数人追加（422エラー）。"""
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
async def test_update_member_role_success(client: AsyncClient, override_auth, project_with_members, db_session):
    """[test_project_members-013] メンバーロール更新の成功ケース。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    # memberのmember_idを取得
    result = await db_session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == data["project"].id,
            ProjectMember.user_id == data["member"].id,
        )
    )
    member_record = result.scalar_one()

    # Act
    response = await client.patch(
        f"/api/v1/project/{data['project'].id}/member/{member_record.id}",
        json={"role": "project_moderator"},
    )

    # Assert
    assert response.status_code == 200
    result_data = response.json()
    assert result_data["role"] == "project_moderator"


@pytest.mark.asyncio
async def test_update_member_role_not_found(client: AsyncClient, override_auth, project_with_owner):
    """[test_project_members-014] 存在しないメンバーのロール更新（404エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/member/{nonexistent_id}",
        json={"role": "member"},
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_last_manager_role(client: AsyncClient, override_auth, project_with_owner, db_session):
    """[test_project_members-015] 最後のPROJECT_MANAGERのロール変更（422エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ownerのmember_idを取得
    result = await db_session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == owner.id,
        )
    )
    owner_member = result.scalar_one()

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/member/{owner_member.id}",
        json={"role": "member"},
    )

    # Assert
    assert response.status_code == 422


# ================================================================================
# DELETE /api/v1/project/{project_id}/member/{member_id} - メンバー削除
# ================================================================================


@pytest.mark.asyncio
async def test_remove_member_success(client: AsyncClient, override_auth, project_with_members, db_session):
    """[test_project_members-016] メンバー削除の成功ケース。"""
    # Arrange
    data = project_with_members
    override_auth(data["owner"])

    # viewerのmember_idを取得
    result = await db_session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == data["project"].id,
            ProjectMember.user_id == data["viewer"].id,
        )
    )
    viewer_member = result.scalar_one()

    # Act
    response = await client.delete(f"/api/v1/project/{data['project'].id}/member/{viewer_member.id}")

    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_member_not_found(client: AsyncClient, override_auth, project_with_owner):
    """[test_project_members-017] 存在しないメンバーの削除（404エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/member/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_self_not_allowed(client: AsyncClient, override_auth, project_with_owner, db_session):
    """[test_project_members-018] 自分自身の削除（422エラー、退出を使用すべき）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    result = await db_session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == owner.id,
        )
    )
    owner_member = result.scalar_one()

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/member/{owner_member.id}")

    # Assert
    assert response.status_code == 422


# ================================================================================
# DELETE /api/v1/project/{project_id}/member/me - プロジェクト退出
# ================================================================================


@pytest.mark.asyncio
async def test_leave_project_success(client: AsyncClient, override_auth, project_with_members):
    """[test_project_members-019] プロジェクト退出の成功ケース。"""
    # Arrange
    data = project_with_members
    override_auth(data["member"])

    # Act
    response = await client.delete(f"/api/v1/project/{data['project'].id}/member/me")

    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_leave_project_last_manager(client: AsyncClient, override_auth, project_with_owner):
    """[test_project_members-020] 最後のPROJECT_MANAGERのプロジェクト退出（422エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/member/me")

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_leave_project_not_member(client: AsyncClient, override_auth, project_with_owner, test_data_seeder):
    """[test_project_members-021] メンバーでないユーザーのプロジェクト退出（404エラー）。"""
    # Arrange
    project, _ = project_with_owner
    other_user = await test_data_seeder.create_user()
    await test_data_seeder.db.commit()

    override_auth(other_user)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/member/me")

    # Assert
    assert response.status_code == 404
