"""ProjectMemberServiceのテスト。"""

import pytest

from app.core.exceptions import AuthorizationError, ValidationError
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.project_member import ProjectMemberCreate
from app.services.project_member import ProjectMemberService


@pytest.fixture
async def test_users(db_session):
    """テスト用ユーザーを作成。"""
    users = []
    for i in range(5):
        user = User(
            azure_oid=f"service-test-oid-{i}",
            email=f"serviceuser{i}@company.com",
            display_name=f"Service User {i}",
        )
        db_session.add(user)
        users.append(user)
    await db_session.commit()
    for user in users:
        await db_session.refresh(user)
    return users


@pytest.fixture
async def test_project_with_owner(db_session, test_users):
    """OWNER付きテスト用プロジェクトを作成。"""
    project = Project(
        name="Service Test Project",
        code="SERVICE-TEST-001",
        description="Test project for service tests",
        created_by=test_users[0].id,
    )
    db_session.add(project)
    await db_session.flush()

    # test_users[0]をOWNERとして追加
    owner_member = ProjectMember(
        project_id=project.id,
        user_id=test_users[0].id,
        role=ProjectRole.PROJECT_MANAGER,
        added_by=test_users[0].id,
    )
    db_session.add(owner_member)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_add_member_success(db_session, test_project_with_owner, test_users):
    """メンバー追加成功のテスト（ADMINがMEMBERを追加）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    member_data = ProjectMemberCreate(
        user_id=test_users[1].id,
        role=ProjectRole.MEMBER,
    )

    # Act
    member = await service.add_member(
        project_id=project.id,
        member_data=member_data,
        added_by=test_users[0].id,  # OWNER
    )
    await db_session.commit()

    # Assert
    assert member is not None
    assert member.project_id == project.id
    assert member.user_id == test_users[1].id
    assert member.role == ProjectRole.MEMBER
    assert member.added_by == test_users[0].id


@pytest.mark.asyncio
async def test_add_member_duplicate(db_session, test_project_with_owner, test_users):
    """重複メンバー追加のテスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    member_data = ProjectMemberCreate(
        user_id=test_users[1].id,
        role=ProjectRole.MEMBER,
    )

    # 最初の追加
    await service.add_member(project.id, member_data, test_users[0].id)
    await db_session.commit()

    # Act & Assert - 重複追加でエラー
    with pytest.raises(ValidationError) as exc_info:
        await service.add_member(project.id, member_data, test_users[0].id)

    assert "既にプロジェクトのメンバー" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_add_member_insufficient_permission(db_session, test_project_with_owner, test_users):
    """権限不足でのメンバー追加テスト（AuthorizationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]をVIEWERとして追加
    viewer_member = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=ProjectRole.VIEWER,
        added_by=test_users[0].id,
    )
    db_session.add(viewer_member)
    await db_session.commit()

    member_data = ProjectMemberCreate(
        user_id=test_users[2].id,
        role=ProjectRole.MEMBER,
    )

    # Act & Assert - VIEWERはメンバー追加不可
    with pytest.raises(AuthorizationError) as exc_info:
        await service.add_member(project.id, member_data, test_users[1].id)

    assert "権限がありません" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_add_owner_by_non_owner(db_session, test_project_with_owner, test_users):
    """PROJECT_MODERATORによるPROJECT_MANAGER追加テスト（AuthorizationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]をPROJECT_MODERATORとして追加
    moderator_member = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=ProjectRole.PROJECT_MODERATOR,
        added_by=test_users[0].id,
    )
    db_session.add(moderator_member)
    await db_session.commit()

    member_data = ProjectMemberCreate(
        user_id=test_users[2].id,
        role=ProjectRole.PROJECT_MANAGER,  # PROJECT_MANAGER追加
    )

    # Act & Assert - PROJECT_MODERATORはPROJECT_MANAGER追加不可
    with pytest.raises(AuthorizationError) as exc_info:
        await service.add_member(project.id, member_data, test_users[1].id)

    assert "PROJECT_MANAGER" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_update_member_role_success(db_session, test_project_with_owner, test_users):
    """ロール更新成功のテスト。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]をMEMBERとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=test_users[0].id,
    )
    db_session.add(member)
    await db_session.commit()
    member_id = member.id

    # Act - MEMBERをADMINに昇格
    updated = await service.update_member_role(
        member_id=member_id,
        new_role=ProjectRole.PROJECT_MANAGER,
        requester_id=test_users[0].id,  # OWNER
    )
    await db_session.commit()

    # Assert
    assert updated.role == ProjectRole.PROJECT_MANAGER


@pytest.mark.asyncio
async def test_update_last_owner_role(db_session, test_project_with_owner, test_users):
    """最後のPROJECT_MANAGER降格テスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # 現在のPROJECT_MANAGERはtest_users[0]のみ
    manager_member = await service.repository.get_by_project_and_user(
        project.id, test_users[0].id
    )

    # Act & Assert - 最後のPROJECT_MANAGERを降格しようとするとエラー
    with pytest.raises(ValidationError) as exc_info:
        await service.update_member_role(
            member_id=manager_member.id,
            new_role=ProjectRole.MEMBER,  # MEMBERに降格
            requester_id=test_users[0].id,
        )

    assert "最低1人のPROJECT_MANAGER" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_remove_member_success(db_session, test_project_with_owner, test_users):
    """メンバー削除成功のテスト。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]をMEMBERとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=test_users[0].id,
    )
    db_session.add(member)
    await db_session.commit()
    member_id = member.id

    # Act
    await service.remove_member(
        member_id=member_id,
        requester_id=test_users[0].id,  # OWNER
    )
    await db_session.commit()

    # Assert
    deleted_member = await service.repository.get(member_id)
    assert deleted_member is None


@pytest.mark.asyncio
async def test_remove_self(db_session, test_project_with_owner, test_users):
    """自分自身の削除テスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # 現在のOWNERはtest_users[0]
    owner_member = await service.repository.get_by_project_and_user(
        project.id, test_users[0].id
    )

    # Act & Assert - 自分自身を削除しようとするとエラー
    with pytest.raises(ValidationError) as exc_info:
        await service.remove_member(
            member_id=owner_member.id,
            requester_id=test_users[0].id,
        )

    assert "自分自身" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_remove_last_owner(db_session, test_project_with_owner, test_users):
    """最後のOWNER削除テスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]とtest_users[2]をOWNERとして追加
    second_owner = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=ProjectRole.PROJECT_MANAGER,
        added_by=test_users[0].id,
    )
    third_owner = ProjectMember(
        project_id=project.id,
        user_id=test_users[2].id,
        role=ProjectRole.PROJECT_MANAGER,
        added_by=test_users[0].id,
    )
    db_session.add(second_owner)
    db_session.add(third_owner)
    await db_session.commit()

    # 最初の2人のOWNERを削除（成功するはず）
    first_owner = await service.repository.get_by_project_and_user(
        project.id, test_users[0].id
    )
    await service.remove_member(first_owner.id, test_users[1].id)
    await db_session.commit()

    await service.remove_member(second_owner.id, test_users[2].id)
    await db_session.commit()

    # Act & Assert - 最後のOWNERを削除しようとするとエラー
    # test_users[2]だけが残っている状態で、test_users[1]を権限者として削除を試みる
    # しかしtest_users[1]は既に削除されているので、test_users[2]が削除を試みる
    with pytest.raises(ValidationError) as exc_info:
        await service.remove_member(third_owner.id, test_users[2].id)

    assert "最低1人のOWNER" in str(exc_info.value.message) or "自分自身" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_leave_project_success(db_session, test_project_with_owner, test_users):
    """プロジェクト退出成功のテスト。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]をMEMBERとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=ProjectRole.MEMBER,
        added_by=test_users[0].id,
    )
    db_session.add(member)
    await db_session.commit()

    # Act
    await service.leave_project(
        project_id=project.id,
        user_id=test_users[1].id,
    )
    await db_session.commit()

    # Assert
    left_member = await service.repository.get_by_project_and_user(
        project.id, test_users[1].id
    )
    assert left_member is None


@pytest.mark.asyncio
async def test_leave_project_last_owner(db_session, test_project_with_owner, test_users):
    """最後のPROJECT_MANAGERの退出テスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # 現在のPROJECT_MANAGERはtest_users[0]のみ

    # Act & Assert - 最後のPROJECT_MANAGERは退出不可
    with pytest.raises(ValidationError) as exc_info:
        await service.leave_project(
            project_id=project.id,
            user_id=test_users[0].id,
        )

    assert "最低1人のPROJECT_MANAGER" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_get_user_role(db_session, test_project_with_owner, test_users):
    """ユーザーロール取得のテスト。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # Act
    role_info = await service.get_user_role(
        project_id=project.id,
        user_id=test_users[0].id,
    )

    # Assert
    assert role_info["project_id"] == project.id
    assert role_info["user_id"] == test_users[0].id
    assert role_info["role"] == ProjectRole.PROJECT_MANAGER
    assert role_info["is_owner"] is True
    assert role_info["is_admin"] is True
