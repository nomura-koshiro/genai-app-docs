"""Project シーダー。"""

import uuid
from typing import Any

from app.models import Project, ProjectRole, UserAccount

from .project_member import ProjectMemberSeederMixin
from .user_account import UserAccountSeederMixin


class ProjectSeederMixin(UserAccountSeederMixin, ProjectMemberSeederMixin):
    """Project作成用Mixin。"""

    async def create_project(
        self,
        *,
        name: str = "Test Project",
        code: str | None = None,
        description: str = "Test project description",
        created_by: uuid.UUID | None = None,
        is_active: bool = True,
    ) -> Project:
        """テスト用プロジェクトを作成。"""
        unique_id = uuid.uuid4().hex[:6]
        project = Project(
            name=name,
            code=code or f"TEST-{unique_id}",
            description=description,
            created_by=created_by,
            is_active=is_active,
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        self._created_data.projects.append(project)
        return project

    async def create_project_with_owner(
        self,
        *,
        owner: UserAccount | None = None,
        name: str = "Test Project",
        code: str | None = None,
    ) -> tuple[Project, UserAccount]:
        """オーナー付きプロジェクトを作成。"""
        if owner is None:
            owner = await self.create_user(display_name="Project Owner")

        project = await self.create_project(
            name=name,
            code=code,
            created_by=owner.id,
        )

        await self.create_member(
            project=project,
            user=owner,
            role=ProjectRole.PROJECT_MANAGER,
            added_by=owner.id,
        )

        return project, owner

    async def seed_basic_dataset(self) -> dict[str, Any]:
        """基本的なテストデータセットをシード。"""
        admin = await self.create_admin_user()
        owner = await self.create_user(display_name="Project Owner")

        project = await self.create_project(
            name="Basic Test Project",
            created_by=owner.id,
        )

        await self.create_member(
            project=project,
            user=owner,
            role=ProjectRole.PROJECT_MANAGER,
        )

        members = []
        for i, role in enumerate([ProjectRole.PROJECT_MODERATOR, ProjectRole.MEMBER, ProjectRole.VIEWER]):
            member_user = await self.create_user(display_name=f"Member {i + 1}")
            await self.create_member(
                project=project,
                user=member_user,
                role=role,
                added_by=owner.id,
            )
            members.append(member_user)

        await self.db.commit()

        return {
            "admin": admin,
            "owner": owner,
            "members": members,
            "project": project,
        }

    async def seed_multiple_projects_dataset(self) -> dict[str, Any]:
        """複数プロジェクトを持つデータセットをシード。"""
        user = await self.create_user(display_name="Multi-Project User")

        projects = []
        for i in range(3):
            project, _ = await self.create_project_with_owner(
                name=f"Project {i + 1}",
            )
            await self.create_member(
                project=project,
                user=user,
                role=ProjectRole.MEMBER,
            )
            projects.append(project)

        await self.db.commit()

        return {
            "user": user,
            "projects": projects,
        }
