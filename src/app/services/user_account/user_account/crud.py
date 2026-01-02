"""ユーザーアカウントCRUDサービス。

このモジュールは、ユーザーアカウントのCRUD操作を提供します。
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import cache_result, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import UserAccount
from app.services.user_account.user_account.base import UserAccountServiceBase

logger = get_logger(__name__)


class UserAccountCrudService(UserAccountServiceBase):
    """ユーザーアカウントのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ユーザーアカウントCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @cache_result(ttl=3600, key_prefix="user")
    @measure_performance
    async def get_user(self, user_id: uuid.UUID) -> UserAccount | None:
        """ユーザーIDでユーザー情報を取得します。

        Args:
            user_id: 取得対象のユーザーUUID

        Returns:
            UserAccount | None: 該当するユーザーモデルインスタンス、存在しない場合はNone
        """
        logger.debug("ユーザーIDでユーザーを取得中", user_id=str(user_id), action="get_user")

        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            return None

        logger.debug("ユーザーを正常に取得しました", user_id=str(user.id), email=user.email)
        return user

    @measure_performance
    async def get_user_by_email(self, email: str) -> UserAccount:
        """メールアドレスでユーザー情報を取得します。

        Args:
            email: 検索対象のメールアドレス

        Returns:
            UserAccount: 該当するユーザーモデルインスタンス

        Raises:
            NotFoundError: 指定されたメールアドレスのユーザーが存在しない場合
        """
        logger.debug(
            "メールアドレスでユーザーを取得中",
            email=email,
            action="get_user_by_email",
        )

        user = await self.repository.get_by_email(email)
        if not user:
            logger.warning("ユーザーが見つかりません", email=email)
            raise NotFoundError("ユーザーが見つかりません", details={"email": email})

        logger.debug("ユーザーを正常に取得しました", user_id=str(user.id), email=user.email)
        return user

    @measure_performance
    async def get_user_by_azure_oid(self, azure_oid: str) -> UserAccount:
        """Azure OIDでユーザー情報を取得します。

        Args:
            azure_oid: Azure AD Object ID

        Returns:
            UserAccount: 該当するユーザーモデルインスタンス

        Raises:
            NotFoundError: 指定されたAzure OIDのユーザーが存在しない場合
        """
        logger.debug(
            "Azure OIDでユーザーを取得中",
            azure_oid=azure_oid,
            action="get_user_by_azure_oid",
        )

        user = await self.repository.get_by_azure_oid(azure_oid)
        if not user:
            logger.warning("ユーザーが見つかりません", azure_oid=azure_oid)
            raise NotFoundError("ユーザーが見つかりません", details={"azure_oid": azure_oid})

        logger.debug("ユーザーを正常に取得しました", user_id=str(user.id), email=user.email)
        return user

    @measure_performance
    async def list_active_users(self, skip: int = 0, limit: int = 100) -> list[UserAccount]:
        """アクティブなユーザーの一覧を取得します。

        Args:
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            list[UserAccount]: アクティブユーザーモデルインスタンスのリスト
        """
        logger.debug("アクティブユーザー一覧を取得中", skip=skip, limit=limit, action="list_active_users")

        users = await self.repository.get_active_users(skip=skip, limit=limit)

        logger.debug(
            "アクティブユーザー一覧を正常に取得しました",
            count=len(users),
            skip=skip,
            limit=limit,
        )

        return users

    @measure_performance
    async def list_users(self, skip: int = 0, limit: int = 100) -> list[UserAccount]:
        """すべてのユーザーの一覧を取得します（アクティブ・非アクティブ両方）。

        Args:
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            list[UserAccount]: ユーザーモデルインスタンスのリスト
        """
        logger.debug("ユーザー一覧を取得中", skip=skip, limit=limit, action="list_users")

        users = await self.repository.get_multi(skip=skip, limit=limit)

        logger.debug(
            "ユーザー一覧を正常に取得しました",
            count=len(users),
            skip=skip,
            limit=limit,
        )

        return users

    @measure_performance
    async def count_users(self, is_active: bool | None = None) -> int:
        """ユーザー総数を取得します。

        Args:
            is_active: アクティブフラグフィルタ
                - True: アクティブユーザーのみ
                - False: 非アクティブユーザーのみ
                - None: 全ユーザー

        Returns:
            int: 条件に一致するユーザー総数
        """
        logger.debug(
            "ユーザー総数を取得中",
            is_active=is_active,
            action="count_users",
        )

        if is_active is not None:
            total = await self.repository.count(is_active=is_active)
        else:
            total = await self.repository.count()

        logger.debug(
            "ユーザー総数を正常に取得しました",
            total=total,
            is_active=is_active,
        )

        return total

    @measure_performance
    @transactional
    async def update_user(
        self,
        user_id: uuid.UUID,
        update_data: dict[str, Any],
        current_user_roles: list[str],
    ) -> UserAccount:
        """ユーザー情報を更新します。

        roles および is_active フィールドの更新には SystemAdmin ロールが必要です。

        Args:
            user_id: 更新対象ユーザーID
            update_data: 更新データ
            current_user_roles: 実行ユーザーのロール（権限チェック用）

        Returns:
            UserAccount: 更新されたユーザーモデルインスタンス

        Raises:
            ValidationError: 権限不足（roles/is_active 更新時に SystemAdmin がない場合）
            NotFoundError: ユーザーが存在しない
        """
        logger.info(
            "ユーザー情報を更新中",
            user_id=str(user_id),
            update_fields=list(update_data.keys()),
            current_user_roles=current_user_roles,
            action="update_user",
        )

        # 権限チェック: roles または is_active の更新は管理者のみ
        if "roles" in update_data or "is_active" in update_data:
            if "system_admin" not in current_user_roles:
                logger.warning(
                    "権限不足: rolesまたはis_activeの更新には管理者権限が必要です",
                    user_id=str(user_id),
                    current_user_roles=current_user_roles,
                    attempted_update=update_data,
                )
                raise ValidationError(
                    "rolesまたはis_activeの更新には管理者権限が必要です",
                    details={"required_role": "SystemAdmin"},
                )

        # ユーザー取得
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

        # 更新実行
        updated_user = await self.repository.update(user, **update_data)

        logger.info(
            "ユーザー情報を更新しました",
            user_id=str(updated_user.id),
            updated_fields=list(update_data.keys()),
        )

        return updated_user

    @measure_performance
    @transactional
    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """ユーザーを削除します。

        Args:
            user_id: 削除対象ユーザーID

        Returns:
            bool: 削除成功の場合True

        Raises:
            NotFoundError: ユーザーが存在しない
        """
        logger.info(
            "ユーザーを削除中",
            user_id=str(user_id),
            action="delete_user",
        )

        # ユーザー取得
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

        # 削除実行
        await self.repository.delete(user_id)

        logger.info(
            "ユーザーを削除しました",
            user_id=str(user_id),
        )

        return True

    @measure_performance
    @transactional
    async def activate_user(self, user_id: uuid.UUID) -> UserAccount:
        """ユーザーを有効化します。

        Args:
            user_id: 有効化対象ユーザーID

        Returns:
            UserAccount: 有効化されたユーザーモデルインスタンス

        Raises:
            NotFoundError: ユーザーが存在しない
        """
        logger.info(
            "ユーザーを有効化中",
            user_id=str(user_id),
            action="activate_user",
        )

        # ユーザー取得
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

        # 有効化実行
        updated_user = await self.repository.update(user, is_active=True)

        logger.info(
            "ユーザーを有効化しました",
            user_id=str(updated_user.id),
            email=updated_user.email,
        )

        return updated_user

    @measure_performance
    @transactional
    async def deactivate_user(self, user_id: uuid.UUID) -> UserAccount:
        """ユーザーを無効化します。

        Args:
            user_id: 無効化対象ユーザーID

        Returns:
            UserAccount: 無効化されたユーザーモデルインスタンス

        Raises:
            NotFoundError: ユーザーが存在しない
        """
        logger.info(
            "ユーザーを無効化中",
            user_id=str(user_id),
            action="deactivate_user",
        )

        # ユーザー取得
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

        # 無効化実行
        updated_user = await self.repository.update(user, is_active=False)

        logger.info(
            "ユーザーを無効化しました",
            user_id=str(updated_user.id),
            email=updated_user.email,
        )

        return updated_user

    @measure_performance
    @transactional
    async def update_user_role(self, user_id: uuid.UUID, roles: list[str]) -> UserAccount:
        """ユーザーのロールを更新します。

        Args:
            user_id: ロール更新対象ユーザーID
            roles: 新しいロールリスト

        Returns:
            UserAccount: ロールが更新されたユーザーモデルインスタンス

        Raises:
            NotFoundError: ユーザーが存在しない
        """
        logger.info(
            "ユーザーロールを更新中",
            user_id=str(user_id),
            new_roles=roles,
            action="update_user_role",
        )

        # ユーザー取得
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError("ユーザーが見つかりません", details={"user_id": str(user_id)})

        # ロール更新実行
        updated_user = await self.repository.update(user, roles=roles)

        logger.info(
            "ユーザーロールを更新しました",
            user_id=str(updated_user.id),
            email=updated_user.email,
            new_roles=updated_user.roles,
        )

        return updated_user
