"""ProjectMemberServiceのテスト。"""

import pytest

from app.core.exceptions import AuthorizationError, ValidationError
from app.models import Project, ProjectMember, ProjectRole, UserAccount
from app.repositories import ProjectMemberRepository
from app.schemas import ProjectMemberCreate
from app.services import ProjectMemberService


@pytest.fixture
async def test_users(db_session):
    """[test_project_member-001] テスト用ユーザーを作成。"""
    users = []
    for i in range(5):
        user = UserAccount(
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
    """[test_project_member-002] OWNER付きテスト用プロジェクトを作成。"""
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
    """[test_project_member-003] メンバー追加成功のテスト（ADMINがMEMBERを追加）。"""
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
    """[test_project_member-004] 重複メンバー追加のテスト（ValidationError）。"""
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


@pytest.mark.parametrize(
    "requester_role,target_role,expected_error",
    [
        (ProjectRole.VIEWER, ProjectRole.MEMBER, "権限がありません"),
        (ProjectRole.PROJECT_MODERATOR, ProjectRole.PROJECT_MANAGER, "PROJECT_MANAGER"),
    ],
    ids=["viewer_cannot_add_member", "moderator_cannot_add_manager"],
)
@pytest.mark.asyncio
async def test_add_member_permission_denied(db_session, test_project_with_owner, test_users, requester_role, target_role, expected_error):
    """[test_project_member-005] 権限不足でのメンバー追加テスト（AuthorizationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # test_users[1]を指定されたロールとして追加
    requester_member = ProjectMember(
        project_id=project.id,
        user_id=test_users[1].id,
        role=requester_role,
        added_by=test_users[0].id,
    )
    db_session.add(requester_member)
    await db_session.commit()

    member_data = ProjectMemberCreate(
        user_id=test_users[2].id,
        role=target_role,
    )

    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        await service.add_member(project.id, member_data, test_users[1].id)

    assert expected_error in str(exc_info.value.message)


@pytest.mark.parametrize(
    "initial_role,new_role,should_succeed,expected_error",
    [
        (ProjectRole.MEMBER, ProjectRole.PROJECT_MANAGER, True, None),
        (ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, False, "最低1人のPROJECT_MANAGER"),
    ],
    ids=["member_to_manager_success", "last_manager_downgrade_fails"],
)
@pytest.mark.asyncio
async def test_update_member_role(db_session, test_project_with_owner, test_users, initial_role, new_role, should_succeed, expected_error):
    """[test_project_member-007] メンバーロール更新のテスト。"""
    # Arrange
    service = ProjectMemberService(db_session)
    repository = ProjectMemberRepository(db_session)
    project = test_project_with_owner

    if initial_role == ProjectRole.PROJECT_MANAGER:
        # 現在のPROJECT_MANAGERを取得
        member = await repository.get_by_project_and_user(project.id, test_users[0].id)
        assert member is not None
    else:
        # test_users[1]を指定されたロールとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=test_users[1].id,
            role=initial_role,
            added_by=test_users[0].id,
        )
        db_session.add(member)
        await db_session.commit()

    member_id = member.id

    # Act & Assert
    if should_succeed:
        updated = await service.update_member_role(
            member_id=member_id,
            new_role=new_role,
            requester_id=test_users[0].id,
        )
        await db_session.commit()
        assert updated.role == new_role
    else:
        with pytest.raises(ValidationError) as exc_info:
            await service.update_member_role(
                member_id=member_id,
                new_role=new_role,
                requester_id=test_users[0].id,
            )
        assert expected_error in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_remove_member_success(db_session, test_project_with_owner, test_users):
    """[test_project_member-009] メンバー削除成功のテスト。"""
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
    repository = ProjectMemberRepository(db_session)
    deleted_member = await repository.get(member_id)
    assert deleted_member is None


@pytest.mark.asyncio
async def test_remove_self(db_session, test_project_with_owner, test_users):
    """[test_project_member-010] 自分自身の削除テスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    repository = ProjectMemberRepository(db_session)
    project = test_project_with_owner

    # 現在のOWNERはtest_users[0]
    owner_member = await repository.get_by_project_and_user(project.id, test_users[0].id)
    assert owner_member is not None

    # Act & Assert - 自分自身を削除しようとするとエラー
    with pytest.raises(ValidationError) as exc_info:
        await service.remove_member(
            member_id=owner_member.id,
            requester_id=test_users[0].id,
        )

    assert "自分自身" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_remove_last_owner(db_session, test_project_with_owner, test_users):
    """[test_project_member-011] 最後のOWNER削除テスト（ValidationError）。"""
    # Arrange
    service = ProjectMemberService(db_session)
    repository = ProjectMemberRepository(db_session)
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
    first_owner = await repository.get_by_project_and_user(project.id, test_users[0].id)
    assert first_owner is not None
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
    """[test_project_member-012] プロジェクト退出成功のテスト。"""
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
    repository = ProjectMemberRepository(db_session)
    left_member = await repository.get_by_project_and_user(project.id, test_users[1].id)
    assert left_member is None


@pytest.mark.asyncio
async def test_leave_project_last_owner(db_session, test_project_with_owner, test_users):
    """[test_project_member-013] 最後のPROJECT_MANAGERの退出テスト（ValidationError）。"""
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
    """[test_project_member-014] ユーザーロール取得のテスト。"""
    # Arrange
    service = ProjectMemberService(db_session)
    project = test_project_with_owner

    # Act
    role = await service.get_user_role(
        project_id=project.id,
        user_id=test_users[0].id,
    )

    # Assert
    assert role is not None
    assert role == ProjectRole.PROJECT_MANAGER
