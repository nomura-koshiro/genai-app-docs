"""UserAccount シーダー。"""

import uuid

from app.models import UserAccount

from .base import BaseSeeder


class UserAccountSeederMixin(BaseSeeder):
    """UserAccount作成用Mixin。"""

    async def create_user(
        self,
        *,
        email: str | None = None,
        display_name: str = "Test User",
        roles: list[str] | None = None,
        is_active: bool = True,
    ) -> UserAccount:
        """テスト用ユーザーを作成。"""
        unique_id = uuid.uuid4().hex[:8]
        user = UserAccount(
            azure_oid=f"test-oid-{unique_id}",
            email=email or f"test-{unique_id}@example.com",
            display_name=display_name,
            roles=roles or ["User"],
            is_active=is_active,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        self._created_data.users.append(user)
        return user

    async def create_admin_user(
        self,
        *,
        email: str | None = None,
        display_name: str = "Admin User",
    ) -> UserAccount:
        """テスト用管理者ユーザーを作成。"""
        return await self.create_user(
            email=email,
            display_name=display_name,
            roles=["SystemAdmin"],
        )
