"""RoleHistoryService のテスト。

このモジュールは、ロール変更履歴サービスの機能をテストします。

テストケース:
    - システムロール変更履歴の記録
    - プロジェクトロール変更履歴の記録
    - ユーザー別履歴の取得
    - プロジェクト別履歴の取得
    - アクション決定ロジック
"""

import pytest

from app.models import Project, UserAccount
from app.services.user_account.role_history import RoleHistoryService


class TestRecordSystemRoleChange:
    """システムロール変更履歴記録のテスト。"""

    @pytest.mark.asyncio
    async def test_record_system_role_grant(self, db_session):
        """[test_role_history-001] システムロール付与の履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-001",
            email="role-history-user-001@example.com",
            display_name="Role History User 001",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-001",
            email="role-history-admin-001@example.com",
            display_name="Role History Admin 001",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_system_role_change(
            user_id=user.id,
            old_roles=[],
            new_roles=["User"],
            changed_by_id=admin.id,
            reason="Initial role assignment",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.id is not None
        assert history.user_id == user.id
        assert history.changed_by_id == admin.id
        assert history.action == "grant"
        assert history.role_type == "system"
        assert history.old_roles == []
        assert history.new_roles == ["User"]
        assert history.reason == "Initial role assignment"
        assert history.project_id is None

    @pytest.mark.asyncio
    async def test_record_system_role_revoke(self, db_session):
        """[test_role_history-002] システムロール削除の履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-002",
            email="role-history-user-002@example.com",
            display_name="Role History User 002",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-002",
            email="role-history-admin-002@example.com",
            display_name="Role History Admin 002",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_system_role_change(
            user_id=user.id,
            old_roles=["User", "ProjectManager"],
            new_roles=[],
            changed_by_id=admin.id,
            reason="Revoke all roles",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.action == "revoke"
        assert history.role_type == "system"
        assert history.old_roles == ["User", "ProjectManager"]
        assert history.new_roles == []

    @pytest.mark.asyncio
    async def test_record_system_role_update(self, db_session):
        """[test_role_history-003] システムロール更新の履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-003",
            email="role-history-user-003@example.com",
            display_name="Role History User 003",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-003",
            email="role-history-admin-003@example.com",
            display_name="Role History Admin 003",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_system_role_change(
            user_id=user.id,
            old_roles=["User"],
            new_roles=["User", "SystemAdmin"],
            changed_by_id=admin.id,
            reason="Promote to admin",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.action == "update"
        assert history.role_type == "system"
        assert history.old_roles == ["User"]
        assert history.new_roles == ["User", "SystemAdmin"]

    @pytest.mark.asyncio
    async def test_record_system_role_change_without_changed_by(self, db_session):
        """[test_role_history-004] 変更者なしでのシステムロール変更履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-004",
            email="role-history-user-004@example.com",
            display_name="Role History User 004",
            roles=["User"],
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_system_role_change(
            user_id=user.id,
            old_roles=[],
            new_roles=["User"],
            changed_by_id=None,
            reason="System auto-assignment",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.changed_by_id is None
        assert history.reason == "System auto-assignment"


class TestRecordProjectRoleChange:
    """プロジェクトロール変更履歴記録のテスト。"""

    @pytest.mark.asyncio
    async def test_record_project_role_grant(self, db_session):
        """[test_role_history-005] プロジェクトロール付与の履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-005",
            email="role-history-user-005@example.com",
            display_name="Role History User 005",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-005",
            email="role-history-admin-005@example.com",
            display_name="Role History Admin 005",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)

        project = Project(
            name="Test Project 005",
            code="TP-005",
            description="Test project for role history",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_project_role_change(
            user_id=user.id,
            project_id=project.id,
            old_roles=[],
            new_roles=["Member"],
            changed_by_id=admin.id,
            reason="Add to project",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.id is not None
        assert history.user_id == user.id
        assert history.project_id == project.id
        assert history.changed_by_id == admin.id
        assert history.action == "grant"
        assert history.role_type == "project"
        assert history.old_roles == []
        assert history.new_roles == ["Member"]
        assert history.reason == "Add to project"

    @pytest.mark.asyncio
    async def test_record_project_role_revoke(self, db_session):
        """[test_role_history-006] プロジェクトロール削除の履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-006",
            email="role-history-user-006@example.com",
            display_name="Role History User 006",
            roles=["User"],
        )
        db_session.add(user)

        project = Project(
            name="Test Project 006",
            code="TP-006",
            description="Test project for role history",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_project_role_change(
            user_id=user.id,
            project_id=project.id,
            old_roles=["Member"],
            new_roles=[],
            changed_by_id=None,
            reason="Remove from project",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.action == "revoke"
        assert history.role_type == "project"
        assert history.project_id == project.id

    @pytest.mark.asyncio
    async def test_record_project_role_update(self, db_session):
        """[test_role_history-007] プロジェクトロール更新の履歴記録テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-007",
            email="role-history-user-007@example.com",
            display_name="Role History User 007",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-007",
            email="role-history-admin-007@example.com",
            display_name="Role History Admin 007",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)

        project = Project(
            name="Test Project 007",
            code="TP-007",
            description="Test project for role history",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)

        # Act
        history = await service.record_project_role_change(
            user_id=user.id,
            project_id=project.id,
            old_roles=["Member"],
            new_roles=["ProjectManager"],
            changed_by_id=admin.id,
            reason="Promote to project manager",
        )
        await db_session.commit()

        # Assert
        assert history is not None
        assert history.action == "update"
        assert history.role_type == "project"
        assert history.old_roles == ["Member"]
        assert history.new_roles == ["ProjectManager"]


class TestGetUserRoleHistory:
    """ユーザー別履歴取得のテスト。"""

    @pytest.mark.asyncio
    async def test_get_user_role_history(self, db_session):
        """[test_role_history-008] ユーザー別履歴取得テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-008",
            email="role-history-user-008@example.com",
            display_name="Role History User 008",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-008",
            email="role-history-admin-008@example.com",
            display_name="Role History Admin 008",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        # Create multiple history records
        service = RoleHistoryService(db_session)
        await service.record_system_role_change(
            user_id=user.id,
            old_roles=[],
            new_roles=["User"],
            changed_by_id=admin.id,
        )
        await service.record_system_role_change(
            user_id=user.id,
            old_roles=["User"],
            new_roles=["User", "SystemAdmin"],
            changed_by_id=admin.id,
        )
        await db_session.commit()

        # Act
        result = await service.get_user_role_history(user.id)

        # Assert
        assert result is not None
        assert result.total == 2
        assert len(result.histories) == 2
        assert result.skip == 0
        assert result.limit == 100

    @pytest.mark.asyncio
    async def test_get_user_role_history_with_pagination(self, db_session):
        """[test_role_history-009] ユーザー別履歴取得のページネーションテスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-009",
            email="role-history-user-009@example.com",
            display_name="Role History User 009",
            roles=["User"],
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = RoleHistoryService(db_session)

        # Create 5 history records
        for i in range(5):
            await service.record_system_role_change(
                user_id=user.id,
                old_roles=["Role" + str(i)],
                new_roles=["Role" + str(i + 1)],
            )
        await db_session.commit()

        # Act
        result = await service.get_user_role_history(user.id, skip=2, limit=2)

        # Assert
        assert result is not None
        assert result.total == 5
        assert len(result.histories) == 2
        assert result.skip == 2
        assert result.limit == 2

    @pytest.mark.asyncio
    async def test_get_user_role_history_empty(self, db_session):
        """[test_role_history-010] 履歴がないユーザーの履歴取得テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-010",
            email="role-history-user-010@example.com",
            display_name="Role History User 010",
            roles=["User"],
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = RoleHistoryService(db_session)

        # Act
        result = await service.get_user_role_history(user.id)

        # Assert
        assert result is not None
        assert result.total == 0
        assert len(result.histories) == 0


class TestGetProjectRoleHistory:
    """プロジェクト別履歴取得のテスト。"""

    @pytest.mark.asyncio
    async def test_get_project_role_history(self, db_session):
        """[test_role_history-011] プロジェクト別履歴取得テスト。"""
        # Arrange
        user1 = UserAccount(
            azure_oid="role-history-user-011-1",
            email="role-history-user-011-1@example.com",
            display_name="Role History User 011-1",
            roles=["User"],
        )
        user2 = UserAccount(
            azure_oid="role-history-user-011-2",
            email="role-history-user-011-2@example.com",
            display_name="Role History User 011-2",
            roles=["User"],
        )
        db_session.add(user1)
        db_session.add(user2)

        project = Project(
            name="Test Project 011",
            code="TP-011",
            description="Test project for role history",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)

        # Add role history for two users
        await service.record_project_role_change(
            user_id=user1.id,
            project_id=project.id,
            old_roles=[],
            new_roles=["Member"],
        )
        await service.record_project_role_change(
            user_id=user2.id,
            project_id=project.id,
            old_roles=[],
            new_roles=["Viewer"],
        )
        await db_session.commit()

        # Act
        result = await service.get_project_role_history(project.id)

        # Assert
        assert result is not None
        assert result.total == 2
        assert len(result.histories) == 2

    @pytest.mark.asyncio
    async def test_get_project_role_history_with_pagination(self, db_session):
        """[test_role_history-012] プロジェクト別履歴取得のページネーションテスト。"""
        # Arrange
        project = Project(
            name="Test Project 012",
            code="TP-012",
            description="Test project for role history",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)

        # Create 5 users and history records
        for i in range(5):
            user = UserAccount(
                azure_oid=f"role-history-user-012-{i}",
                email=f"role-history-user-012-{i}@example.com",
                display_name=f"Role History User 012-{i}",
                roles=["User"],
            )
            db_session.add(user)
            await db_session.flush()

            await service.record_project_role_change(
                user_id=user.id,
                project_id=project.id,
                old_roles=[],
                new_roles=["Member"],
            )
        await db_session.commit()

        # Act
        result = await service.get_project_role_history(project.id, skip=1, limit=2)

        # Assert
        assert result is not None
        assert result.total == 5
        assert len(result.histories) == 2
        assert result.skip == 1
        assert result.limit == 2

    @pytest.mark.asyncio
    async def test_get_project_role_history_empty(self, db_session):
        """[test_role_history-013] 履歴がないプロジェクトの履歴取得テスト。"""
        # Arrange
        project = Project(
            name="Test Project 013",
            code="TP-013",
            description="Test project for role history",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)

        # Act
        result = await service.get_project_role_history(project.id)

        # Assert
        assert result is not None
        assert result.total == 0
        assert len(result.histories) == 0


class TestDetermineAction:
    """アクション決定ロジックのテスト。"""

    @pytest.mark.asyncio
    async def test_determine_action_grant(self, db_session):
        """[test_role_history-014] grant アクションの決定テスト。"""
        # Arrange
        service = RoleHistoryService(db_session)

        # Act
        action = service._determine_action(old_roles=[], new_roles=["User"])

        # Assert
        assert action == "grant"

    @pytest.mark.asyncio
    async def test_determine_action_revoke(self, db_session):
        """[test_role_history-015] revoke アクションの決定テスト。"""
        # Arrange
        service = RoleHistoryService(db_session)

        # Act
        action = service._determine_action(old_roles=["User"], new_roles=[])

        # Assert
        assert action == "revoke"

    @pytest.mark.asyncio
    async def test_determine_action_update(self, db_session):
        """[test_role_history-016] update アクションの決定テスト。"""
        # Arrange
        service = RoleHistoryService(db_session)

        # Act
        action = service._determine_action(old_roles=["User"], new_roles=["Admin"])

        # Assert
        assert action == "update"

    @pytest.mark.asyncio
    async def test_determine_action_update_add_role(self, db_session):
        """[test_role_history-017] ロール追加時の update アクション決定テスト。"""
        # Arrange
        service = RoleHistoryService(db_session)

        # Act
        action = service._determine_action(old_roles=["User"], new_roles=["User", "Admin"])

        # Assert
        assert action == "update"

    @pytest.mark.asyncio
    async def test_determine_action_update_remove_role(self, db_session):
        """[test_role_history-018] ロール削除時の update アクション決定テスト。"""
        # Arrange
        service = RoleHistoryService(db_session)

        # Act
        action = service._determine_action(old_roles=["User", "Admin"], new_roles=["User"])

        # Assert
        assert action == "update"


class TestToResponse:
    """レスポンス変換のテスト。"""

    @pytest.mark.asyncio
    async def test_to_response_with_changed_by(self, db_session):
        """[test_role_history-019] 変更者ありのレスポンス変換テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-019",
            email="role-history-user-019@example.com",
            display_name="Role History User 019",
            roles=["User"],
        )
        db_session.add(user)

        admin = UserAccount(
            azure_oid="role-history-admin-019",
            email="role-history-admin-019@example.com",
            display_name="Admin User 019",
            roles=["SystemAdmin"],
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(admin)

        service = RoleHistoryService(db_session)
        _ = await service.record_system_role_change(
            user_id=user.id,
            old_roles=[],
            new_roles=["User"],
            changed_by_id=admin.id,
            reason="Test reason",
        )
        await db_session.commit()

        # Refresh to load relationships
        result = await service.get_user_role_history(user.id)

        # Assert
        assert len(result.histories) == 1
        response = result.histories[0]
        assert response.user_id == user.id
        assert response.changed_by_id == admin.id
        assert response.changed_by_name == "Admin User 019"
        assert response.action.value == "grant"
        assert response.role_type.value == "system"
        assert response.reason == "Test reason"

    @pytest.mark.asyncio
    async def test_to_response_without_changed_by(self, db_session):
        """[test_role_history-020] 変更者なしのレスポンス変換テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-020",
            email="role-history-user-020@example.com",
            display_name="Role History User 020",
            roles=["User"],
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = RoleHistoryService(db_session)
        _ = await service.record_system_role_change(
            user_id=user.id,
            old_roles=[],
            new_roles=["User"],
            changed_by_id=None,
        )
        await db_session.commit()

        # Refresh to load relationships
        result = await service.get_user_role_history(user.id)

        # Assert
        assert len(result.histories) == 1
        response = result.histories[0]
        assert response.changed_by_id is None
        assert response.changed_by_name is None

    @pytest.mark.asyncio
    async def test_to_response_with_project(self, db_session):
        """[test_role_history-021] プロジェクトありのレスポンス変換テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="role-history-user-021",
            email="role-history-user-021@example.com",
            display_name="Role History User 021",
            roles=["User"],
        )
        db_session.add(user)

        project = Project(
            name="Test Project 021",
            code="TP-021",
            description="Test project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        service = RoleHistoryService(db_session)
        await service.record_project_role_change(
            user_id=user.id,
            project_id=project.id,
            old_roles=[],
            new_roles=["Member"],
        )
        await db_session.commit()

        # Refresh to load relationships
        result = await service.get_project_role_history(project.id)

        # Assert
        assert len(result.histories) == 1
        response = result.histories[0]
        assert response.project_id == project.id
        assert response.project_name == "Test Project 021"
        assert response.role_type.value == "project"
