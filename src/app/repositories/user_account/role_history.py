"""ロール変更履歴のデータアクセスリポジトリ。

このモジュールは、RoleHistoryモデルに対するデータベース操作を提供します。
ロール変更の履歴を記録・取得するためのメソッドを含みます。

主な機能:
    - ロール変更履歴の記録
    - ユーザー別の履歴取得
    - プロジェクト別の履歴取得
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_account.role_history import RoleHistory
from app.repositories.base import BaseRepository


class RoleHistoryRepository(BaseRepository[RoleHistory, uuid.UUID]):
    """ロール変更履歴のリポジトリクラス。

    このリポジトリは、ロール変更履歴の記録と取得を行います。

    主なメソッド:
        - create_history(): 履歴を記録
        - get_by_user_id(): ユーザー別の履歴取得
        - get_by_project_id(): プロジェクト別の履歴取得
    """

    def __init__(self, db: AsyncSession):
        """ロール履歴リポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
        """
        super().__init__(RoleHistory, db)

    async def create_history(
        self,
        user_id: uuid.UUID,
        action: str,
        role_type: str,
        old_roles: list[str],
        new_roles: list[str],
        changed_by_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> RoleHistory:
        """ロール変更履歴を作成します。

        Args:
            user_id: 変更対象ユーザーID
            action: 変更アクション（grant/revoke/update）
            role_type: ロール種別（system/project）
            old_roles: 変更前のロール一覧
            new_roles: 変更後のロール一覧
            changed_by_id: 変更実行者のユーザーID
            project_id: プロジェクトID（プロジェクトロールの場合）
            reason: 変更理由

        Returns:
            RoleHistory: 作成された履歴レコード
        """
        history = RoleHistory(
            user_id=user_id,
            changed_by_id=changed_by_id,
            action=action,
            role_type=role_type,
            project_id=project_id,
            old_roles=old_roles,
            new_roles=new_roles,
            reason=reason,
            changed_at=datetime.now(UTC),
        )
        self.db.add(history)
        await self.db.flush()
        return history

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RoleHistory]:
        """ユーザーIDで履歴を取得します。

        Args:
            user_id: 対象ユーザーID
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[RoleHistory]: 履歴リスト（新しい順）
        """
        stmt = (
            select(RoleHistory)
            .where(RoleHistory.user_id == user_id)
            .options(selectinload(RoleHistory.changed_by))
            .options(selectinload(RoleHistory.project))
            .order_by(desc(RoleHistory.changed_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_project_id(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RoleHistory]:
        """プロジェクトIDで履歴を取得します。

        Args:
            project_id: 対象プロジェクトID
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[RoleHistory]: 履歴リスト（新しい順）
        """
        stmt = (
            select(RoleHistory)
            .where(RoleHistory.project_id == project_id)
            .options(selectinload(RoleHistory.user))
            .options(selectinload(RoleHistory.changed_by))
            .order_by(desc(RoleHistory.changed_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user_id(self, user_id: uuid.UUID) -> int:
        """ユーザーIDで履歴の件数をカウントします。

        Args:
            user_id: 対象ユーザーID

        Returns:
            int: 履歴件数
        """
        stmt = select(func.count()).select_from(RoleHistory).where(RoleHistory.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_by_project_id(self, project_id: uuid.UUID) -> int:
        """プロジェクトIDで履歴の件数をカウントします。

        Args:
            project_id: 対象プロジェクトID

        Returns:
            int: 履歴件数
        """
        stmt = select(func.count()).select_from(RoleHistory).where(RoleHistory.project_id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
