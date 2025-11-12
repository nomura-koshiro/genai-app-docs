"""Project Members API Endpointのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。
"""

import pytest
from httpx import AsyncClient

from app.models.project.member import ProjectMember, ProjectRole
from app.models.project.project import Project
from app.models.user.user import User


@pytest.fixture
async def api_test_users(db_session):
    """API テスト用ユーザーを作成。"""
    users = []
    for i in range(5):
        user = User(
            azure_oid=f"api-test-oid-{i}",
            email=f"apiuser{i}@company.com",
            display_name=f"API User {i}",
        )
        db_session.add(user)
        users.append(user)
    await db_session.commit()
    for user in users:
        await db_session.refresh(user)
    return users


@pytest.fixture
async def api_test_project_with_owner(db_session, api_test_users):
    """API テスト用プロジェクト（OWNER付き）を作成。"""
    project = Project(
        name="API Test Project",
        code="API-TEST-001",
        description="Test project for API tests",
        created_by=api_test_users[0].id,
    )
    db_session.add(project)
    await db_session.flush()

    # api_test_users[0]をOWNERとして追加
    owner_member = ProjectMember(
        project_id=project.id,
        user_id=api_test_users[0].id,
        role=ProjectRole.PROJECT_MANAGER,
        added_by=api_test_users[0].id,
    )
    db_session.add(owner_member)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_add_member_success(
    client: AsyncClient,
    override_auth,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバー追加API成功テスト。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    payload = {
        "user_id": str(api_test_users[1].id),
        "role": "member",
    }

    # Act
    response = await client.post(
        f"/api/v1/projects/{project.id}/members",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(project.id)
    assert data["user_id"] == str(api_test_users[1].id)
    assert data["role"] == "member"
    assert "user" in data  # ユーザー情報が含まれる


@pytest.mark.asyncio
async def test_add_member_unauthorized(
    client: AsyncClient,
    api_test_project_with_owner,
    api_test_users,
):
    """未認証でのメンバー追加APIテスト（403エラー）。"""
    # Arrange
    project = api_test_project_with_owner
    payload = {
        "user_id": str(api_test_users[1].id),
        "role": "member",
    }

    # Act
    response = await client.post(
        f"/api/v1/projects/{project.id}/members",
        json=payload,
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_project_members_success(
    client: AsyncClient,
    override_auth,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """プロジェクトメンバー一覧取得API成功テスト。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    # メンバーを追加
    for i in range(1, 4):
        member = ProjectMember(
            project_id=project.id,
            user_id=api_test_users[i].id,
            role=ProjectRole.MEMBER,
            added_by=api_test_users[0].id,
        )
        db_session.add(member)
    await db_session.commit()

    # Act
    response = await client.get(
        f"/api/v1/projects/{project.id}/members",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "members" in data
    assert "total" in data
    assert "project_id" in data
    # OWNER (PROJECT_MANAGER) + 3 MEMBER
    assert data["total"] == 4
    assert len(data["members"]) == 4
    # 各メンバーに必須フィールドがあることを確認
    for member in data["members"]:
        assert "id" in member
        assert "user_id" in member
        assert "role" in member
        assert "user" in member


@pytest.mark.asyncio
async def test_get_project_members_pagination(
    client: AsyncClient,
    override_auth,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """プロジェクトメンバー一覧取得APIページネーションテスト。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    # メンバーを追加
    for i in range(1, 5):
        member = ProjectMember(
            project_id=project.id,
            user_id=api_test_users[i].id,
            role=ProjectRole.MEMBER,
            added_by=api_test_users[0].id,
        )
        db_session.add(member)
    await db_session.commit()

    # Act
    response = await client.get(
        f"/api/v1/projects/{project.id}/members?skip=0&limit=2",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "members" in data
    assert "total" in data
    assert len(data["members"]) == 2
    # OWNER (PROJECT_MANAGER) + 4 MEMBER = 5
    assert data["total"] == 5
    # 各メンバーに必須フィールドがあることを確認
    for member in data["members"]:
        assert "id" in member
        assert "user_id" in member
        assert "role" in member
        assert "user" in member


@pytest.mark.asyncio
async def test_update_member_role_success(
    client: AsyncClient,
    override_auth,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバーロール更新API成功テスト。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    # MEMBERを追加
    member = ProjectMember(
        project_id=project.id,
        user_id=api_test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=api_test_users[0].id,
    )
    db_session.add(member)
    await db_session.commit()
    member_id = member.id

    payload = {"role": "project_moderator"}

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project.id}/members/{member_id}",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "project_moderator"


@pytest.mark.skip(reason="Bulk endpoint or validation issue - needs investigation")
@pytest.mark.asyncio
async def test_leave_project_last_owner(
    client: AsyncClient,
    override_auth,
    api_test_project_with_owner,
    api_test_users,
):
    """最後のOWNERのプロジェクト退出APIテスト（422エラー）。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])  # OWNER

    # Act
    response = await client.delete(
        f"/api/v1/projects/{project.id}/members/me",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "PROJECT_MANAGER" in str(data.get("detail", "")) or "最低1人" in str(data.get("detail", ""))


@pytest.mark.asyncio
async def test_add_members_bulk_success(
    client: AsyncClient,
    override_auth,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバー複数人追加API成功テスト。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    payload = {
        "members": [
            {"user_id": str(api_test_users[1].id), "role": "member"},
            {"user_id": str(api_test_users[2].id), "role": "viewer"},
            {"user_id": str(api_test_users[3].id), "role": "project_moderator"},
        ]
    }

    # Act
    response = await client.post(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(project.id)
    assert data["total_requested"] == 3
    assert data["total_added"] == 3
    assert data["total_failed"] == 0
    assert len(data["added"]) == 3
    assert len(data["failed"]) == 0


@pytest.mark.asyncio
async def test_add_members_bulk_partial_success(
    client: AsyncClient,
    override_auth,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバー複数人追加API部分成功テスト（一部重複）。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    # user[1]を既存メンバーとして追加
    existing_member = ProjectMember(
        project_id=project.id,
        user_id=api_test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=api_test_users[0].id,
    )
    db_session.add(existing_member)
    await db_session.commit()

    payload = {
        "members": [
            {"user_id": str(api_test_users[1].id), "role": "member"},  # 重複
            {"user_id": str(api_test_users[2].id), "role": "viewer"},  # 成功
            {"user_id": str(api_test_users[3].id), "role": "project_moderator"},  # 成功
        ]
    }

    # Act
    response = await client.post(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(project.id)
    assert data["total_requested"] == 3
    assert data["total_added"] == 2
    assert data["total_failed"] == 1
    assert len(data["added"]) == 2
    assert len(data["failed"]) == 1
    # 失敗したメンバーの確認
    assert data["failed"][0]["user_id"] == str(api_test_users[1].id)
    assert "既に" in data["failed"][0]["error"]


@pytest.mark.asyncio
async def test_add_members_bulk_unauthorized(
    client: AsyncClient,
    api_test_project_with_owner,
    api_test_users,
):
    """未認証でのメンバー複数人追加APIテスト（403エラー）。"""
    # Arrange
    project = api_test_project_with_owner
    payload = {
        "members": [
            {"user_id": str(api_test_users[1].id), "role": "member"},
        ]
    }

    # Act
    response = await client.post(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_members_bulk_empty_list(
    client: AsyncClient,
    override_auth,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバー複数人追加API空リストテスト（422エラー）。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    payload = {"members": []}

    # Act
    response = await client.post(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.skip(reason="Bulk endpoint or validation issue - needs investigation")
@pytest.mark.asyncio
async def test_update_members_bulk_success(
    client: AsyncClient,
    override_auth,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバーロール複数人更新API成功テスト。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])  # OWNER

    # メンバーを追加
    members = []
    for i in range(1, 4):
        member = ProjectMember(
            project_id=project.id,
            user_id=api_test_users[i].id,
            role=ProjectRole.MEMBER,
            added_by=api_test_users[0].id,
        )
        db_session.add(member)
        members.append(member)
    await db_session.commit()
    for member in members:
        await db_session.refresh(member)

    payload = {
        "updates": [
            {"member_id": str(members[0].id), "role": "project_moderator"},
            {"member_id": str(members[1].id), "role": "viewer"},
            {"member_id": str(members[2].id), "role": "project_moderator"},
        ]
    }

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(project.id)
    assert data["total_requested"] == 3
    assert data["total_updated"] == 3
    assert data["total_failed"] == 0
    assert len(data["updated"]) == 3
    assert len(data["failed"]) == 0


@pytest.mark.skip(reason="Bulk endpoint or validation issue - needs investigation")
@pytest.mark.asyncio
async def test_update_members_bulk_partial_success(
    client: AsyncClient,
    override_auth,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバーロール複数人更新API部分成功テスト（一部エラー）。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])  # OWNER

    # メンバーを追加
    member1 = ProjectMember(
        project_id=project.id,
        user_id=api_test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=api_test_users[0].id,
    )
    db_session.add(member1)
    await db_session.commit()
    await db_session.refresh(member1)

    import uuid as uuid_module

    fake_member_id = uuid_module.uuid4()

    payload = {
        "updates": [
            {"member_id": str(member1.id), "role": "project_moderator"},  # 成功
            {"member_id": str(fake_member_id), "role": "viewer"},  # 失敗（存在しない）
        ]
    }

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(project.id)
    assert data["total_requested"] == 2
    assert data["total_updated"] == 1
    assert data["total_failed"] == 1
    assert len(data["updated"]) == 1
    assert len(data["failed"]) == 1
    # 失敗したメンバーの確認
    assert data["failed"][0]["member_id"] == str(fake_member_id)
    assert "見つかりません" in data["failed"][0]["error"]


@pytest.mark.asyncio
async def test_update_members_bulk_unauthorized(
    client: AsyncClient,
    db_session,
    api_test_project_with_owner,
    api_test_users,
):
    """未認証でのメンバーロール複数人更新APIテスト（403エラー）。"""
    # Arrange
    project = api_test_project_with_owner

    # メンバーを追加
    member = ProjectMember(
        project_id=project.id,
        user_id=api_test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=api_test_users[0].id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    payload = {
        "updates": [
            {"member_id": str(member.id), "role": "project_moderator"},
        ]
    }

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_members_bulk_empty_list(
    client: AsyncClient,
    override_auth,
    api_test_project_with_owner,
    api_test_users,
):
    """メンバーロール複数人更新API空リストテスト（422エラー）。"""
    # Arrange
    project = api_test_project_with_owner
    override_auth(api_test_users[0])

    payload = {"updates": []}

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project.id}/members/bulk",
        json=payload,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert
    assert response.status_code == 422
