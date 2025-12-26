"""ProjectMember シーダー。"""

import uuid

from app.models import Project, ProjectMember, ProjectRole, UserAccount

from .base import BaseSeeder


class ProjectMemberSeederMixin(BaseSeeder):
    """ProjectMember作成用Mixin。"""

    async def create_member(
        self,
        *,
        project: Project,
        user: UserAccount,
        role: ProjectRole = ProjectRole.MEMBER,
        added_by: uuid.UUID | None = None,
    ) -> ProjectMember:
        """プロジェクトメンバーを追加。"""
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=role,
            added_by=added_by or user.id,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        self._created_data.members.append(member)
        return member
