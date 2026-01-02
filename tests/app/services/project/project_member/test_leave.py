"""ProjectMemberLeaveServiceのテスト。"""

import uuid

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Project, ProjectMember, ProjectRole, UserAccount
from app.repositories import ProjectMemberRepository
from app.services.project.project_member.leave import ProjectMemberLeaveService


class TestProjectMemberLeaveService:
    """ProjectMemberLeaveServiceのテストクラス。"""

    @pytest.mark.parametrize(
        "leaving_role",
        [
            ProjectRole.MEMBER,
            ProjectRole.VIEWER,
            ProjectRole.PROJECT_MODERATOR,
        ],
        ids=["member_leave", "viewer_leave", "moderator_leave"],
    )
    @pytest.mark.asyncio
    async def test_leave_project_success_by_role(self, db_session, leaving_role):
        """[test_leave-001] 異なるロールでのプロジェクト退出成功テスト。"""
        # Arrange
        owner = UserAccount(
            azure_oid="leave-owner-oid",
            email="leaveowner@company.com",
            display_name="Leave Owner",
        )
        leaving_user = UserAccount(
            azure_oid="leave-user-oid",
            email="leaveuser@company.com",
            display_name="Leave User",
        )
        project = Project(
            name="Leave Project",
            code="LEAVE-TEST",
        )
        db_session.add(owner)
        db_session.add(leaving_user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(owner)
        await db_session.refresh(leaving_user)
        await db_session.refresh(project)

        # ownerをPROJECT_MANAGERとして追加
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        # leaving_userを指定されたロールとして追加
        leaving_member = ProjectMember(
            project_id=project.id,
            user_id=leaving_user.id,
            role=leaving_role,
        )
        db_session.add(owner_member)
        db_session.add(leaving_member)
        await db_session.commit()

        service = ProjectMemberLeaveService(db_session)

        # Act
        await service.leave_project(project.id, leaving_user.id)
        await db_session.commit()

        # Assert
        repository = ProjectMemberRepository(db_session)
        left_member = await repository.get_by_project_and_user(project.id, leaving_user.id)
        assert left_member is None

    @pytest.mark.asyncio
    async def test_leave_project_not_member(self, db_session):
        """[test_leave-004] 非メンバーによるプロジェクト退出失敗テスト。"""
        # Arrange
        owner = UserAccount(
            azure_oid="leave-owner4-oid",
            email="leaveowner4@company.com",
            display_name="Leave Owner 4",
        )
        non_member_user = UserAccount(
            azure_oid="leave-nonmember-oid",
            email="leavenonmember@company.com",
            display_name="Leave Non Member",
        )
        project = Project(
            name="Leave Non Member Project",
            code="LEAVE-004",
        )
        db_session.add(owner)
        db_session.add(non_member_user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(owner)
        await db_session.refresh(non_member_user)
        await db_session.refresh(project)

        # ownerのみをPROJECT_MANAGERとして追加（non_member_userは追加しない）
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        db_session.add(owner_member)
        await db_session.commit()

        service = ProjectMemberLeaveService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.leave_project(project.id, non_member_user.id)

        assert "プロジェクトのメンバーではありません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_leave_project_last_manager_forbidden(self, db_session):
        """[test_leave-005] 最後のPROJECT_MANAGERの退出失敗テスト。"""
        # Arrange
        owner = UserAccount(
            azure_oid="leave-lastowner-oid",
            email="leavelastowner@company.com",
            display_name="Leave Last Owner",
        )
        project = Project(
            name="Leave Last Owner Project",
            code="LEAVE-005",
        )
        db_session.add(owner)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(owner)
        await db_session.refresh(project)

        # ownerを唯一のPROJECT_MANAGERとして追加
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        db_session.add(owner_member)
        await db_session.commit()

        service = ProjectMemberLeaveService(db_session)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.leave_project(project.id, owner.id)

        assert "最低1人のPROJECT_MANAGER" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_leave_project_manager_with_multiple_managers(self, db_session):
        """[test_leave-006] 複数のPROJECT_MANAGERがいる場合の退出成功テスト。"""
        # Arrange
        owner1 = UserAccount(
            azure_oid="leave-owner1-multi-oid",
            email="leaveowner1multi@company.com",
            display_name="Leave Owner 1 Multi",
        )
        owner2 = UserAccount(
            azure_oid="leave-owner2-multi-oid",
            email="leaveowner2multi@company.com",
            display_name="Leave Owner 2 Multi",
        )
        project = Project(
            name="Leave Multi Owner Project",
            code="LEAVE-006",
        )
        db_session.add(owner1)
        db_session.add(owner2)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(owner1)
        await db_session.refresh(owner2)
        await db_session.refresh(project)

        # 両方をPROJECT_MANAGERとして追加
        owner1_member = ProjectMember(
            project_id=project.id,
            user_id=owner1.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        owner2_member = ProjectMember(
            project_id=project.id,
            user_id=owner2.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        db_session.add(owner1_member)
        db_session.add(owner2_member)
        await db_session.commit()

        service = ProjectMemberLeaveService(db_session)

        # Act - owner1が退出
        await service.leave_project(project.id, owner1.id)
        await db_session.commit()

        # Assert
        repository = ProjectMemberRepository(db_session)
        left_owner1 = await repository.get_by_project_and_user(project.id, owner1.id)
        remaining_owner2 = await repository.get_by_project_and_user(project.id, owner2.id)
        assert left_owner1 is None
        assert remaining_owner2 is not None
        assert remaining_owner2.role == ProjectRole.PROJECT_MANAGER

    @pytest.mark.asyncio
    async def test_leave_project_non_existent_project(self, db_session):
        """[test_leave-007] 存在しないプロジェクトからの退出失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="leave-noproject-oid",
            email="leavenoproject@company.com",
            display_name="Leave No Project",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        non_existent_project_id = uuid.uuid4()

        service = ProjectMemberLeaveService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.leave_project(non_existent_project_id, user.id)

        assert "プロジェクトのメンバーではありません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_leave_project_twice(self, db_session):
        """[test_leave-008] 同じユーザーが2回退出を試みた場合の失敗テスト。"""
        # Arrange
        owner = UserAccount(
            azure_oid="leave-owner-twice-oid",
            email="leaveownertwice@company.com",
            display_name="Leave Owner Twice",
        )
        member_user = UserAccount(
            azure_oid="leave-member-twice-oid",
            email="leavemembertwice@company.com",
            display_name="Leave Member Twice",
        )
        project = Project(
            name="Leave Twice Project",
            code="LEAVE-008",
        )
        db_session.add(owner)
        db_session.add(member_user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(owner)
        await db_session.refresh(member_user)
        await db_session.refresh(project)

        # ownerをPROJECT_MANAGERとして追加
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        # member_userをMEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=member_user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(owner_member)
        db_session.add(member)
        await db_session.commit()

        service = ProjectMemberLeaveService(db_session)

        # Act - 1回目の退出（成功）
        await service.leave_project(project.id, member_user.id)
        await db_session.commit()

        # Act & Assert - 2回目の退出（失敗）
        with pytest.raises(NotFoundError) as exc_info:
            await service.leave_project(project.id, member_user.id)

        assert "プロジェクトのメンバーではありません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_leave_project_preserves_other_members(self, db_session):
        """[test_leave-009] 退出後も他のメンバーが保持されることのテスト。"""
        # Arrange
        owner = UserAccount(
            azure_oid="leave-owner-preserve-oid",
            email="leaveownerpreserve@company.com",
            display_name="Leave Owner Preserve",
        )
        member1 = UserAccount(
            azure_oid="leave-member1-preserve-oid",
            email="leavemember1preserve@company.com",
            display_name="Leave Member 1 Preserve",
        )
        member2 = UserAccount(
            azure_oid="leave-member2-preserve-oid",
            email="leavemember2preserve@company.com",
            display_name="Leave Member 2 Preserve",
        )
        project = Project(
            name="Leave Preserve Project",
            code="LEAVE-009",
        )
        db_session.add(owner)
        db_session.add(member1)
        db_session.add(member2)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(owner)
        await db_session.refresh(member1)
        await db_session.refresh(member2)
        await db_session.refresh(project)

        # メンバーを追加
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        member1_entry = ProjectMember(
            project_id=project.id,
            user_id=member1.id,
            role=ProjectRole.MEMBER,
        )
        member2_entry = ProjectMember(
            project_id=project.id,
            user_id=member2.id,
            role=ProjectRole.VIEWER,
        )
        db_session.add(owner_member)
        db_session.add(member1_entry)
        db_session.add(member2_entry)
        await db_session.commit()

        service = ProjectMemberLeaveService(db_session)

        # Act - member1が退出
        await service.leave_project(project.id, member1.id)
        await db_session.commit()

        # Assert
        repository = ProjectMemberRepository(db_session)
        left_member1 = await repository.get_by_project_and_user(project.id, member1.id)
        remaining_owner = await repository.get_by_project_and_user(project.id, owner.id)
        remaining_member2 = await repository.get_by_project_and_user(project.id, member2.id)

        assert left_member1 is None
        assert remaining_owner is not None
        assert remaining_owner.role == ProjectRole.PROJECT_MANAGER
        assert remaining_member2 is not None
        assert remaining_member2.role == ProjectRole.VIEWER
