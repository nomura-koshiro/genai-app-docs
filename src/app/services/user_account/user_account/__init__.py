"""ユーザーアカウントサービス。

このモジュールは、ユーザーアカウント管理のビジネスロジックを提供します。

主な機能:
    - Azure OIDによるユーザー取得・作成
    - ユーザー情報の取得・更新
    - 最終ログイン情報の更新
    - アクティブユーザーの一覧取得

サブモジュール:
    - base.py: 共通ベースクラス
    - auth.py: 認証関連操作
    - crud.py: CRUD操作
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserAccount
from app.services.user_account.user_account.auth import UserAccountAuthService
from app.services.user_account.user_account.crud import UserAccountCrudService


class UserAccountService:
    """ユーザーアカウント管理のビジネスロジックを提供するサービスクラス。

    認証、CRUD操作を提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """ユーザーアカウントサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._auth_service = UserAccountAuthService(db)
        self._crud_service = UserAccountCrudService(db)

    # ================================================================================
    # 認証関連
    # ================================================================================

    async def get_or_create_by_azure_oid(
        self,
        azure_oid: str,
        email: str,
        display_name: str | None = None,
        roles: list[str] | None = None,
    ) -> UserAccount:
        """Azure OIDでユーザーを取得、または新規作成します。"""
        return await self._auth_service.get_or_create_by_azure_oid(azure_oid, email, display_name, roles)

    async def update_last_login(self, user_id: uuid.UUID, client_ip: str | None = None) -> UserAccount:
        """ユーザーの最終ログイン情報を更新します。"""
        return await self._auth_service.update_last_login(user_id, client_ip)

    # ================================================================================
    # CRUD操作
    # ================================================================================

    async def get_user(self, user_id: uuid.UUID) -> UserAccount | None:
        """ユーザーIDでユーザー情報を取得します。"""
        return await self._crud_service.get_user(user_id)

    async def get_user_by_email(self, email: str) -> UserAccount:
        """メールアドレスでユーザー情報を取得します。"""
        return await self._crud_service.get_user_by_email(email)

    async def get_user_by_azure_oid(self, azure_oid: str) -> UserAccount:
        """Azure OIDでユーザー情報を取得します。"""
        return await self._crud_service.get_user_by_azure_oid(azure_oid)

    async def list_active_users(self, skip: int = 0, limit: int = 100) -> list[UserAccount]:
        """アクティブなユーザーの一覧を取得します。"""
        return await self._crud_service.list_active_users(skip, limit)

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[UserAccount]:
        """すべてのユーザーの一覧を取得します。"""
        return await self._crud_service.list_users(skip, limit)

    async def count_users(self, is_active: bool | None = None) -> int:
        """ユーザー総数を取得します。"""
        return await self._crud_service.count_users(is_active)

    async def update_user(
        self,
        user_id: uuid.UUID,
        update_data: dict[str, Any],
        current_user_roles: list[str],
    ) -> UserAccount:
        """ユーザー情報を更新します。"""
        return await self._crud_service.update_user(user_id, update_data, current_user_roles)

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """ユーザーを削除します。"""
        return await self._crud_service.delete_user(user_id)

    async def activate_user(self, user_id: uuid.UUID) -> UserAccount:
        """ユーザーを有効化します。"""
        return await self._crud_service.activate_user(user_id)

    async def deactivate_user(self, user_id: uuid.UUID) -> UserAccount:
        """ユーザーを無効化します。"""
        return await self._crud_service.deactivate_user(user_id)

    async def update_user_role(self, user_id: uuid.UUID, roles: list[str]) -> UserAccount:
        """ユーザーのロールを更新します。"""
        return await self._crud_service.update_user_role(user_id, roles)


__all__ = ["UserAccountService"]
