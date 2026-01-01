"""ロール履歴サービス。

このモジュールは、ロール変更履歴の管理機能を提供します。

主な機能:
    - ロール変更履歴の記録
    - ユーザー別履歴の取得
    - プロジェクト別履歴の取得
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.models.user_account.role_history import RoleHistory
from app.repositories.user_account.role_history import RoleHistoryRepository
from app.schemas.user_account.role_history import (
    RoleChangeActionEnum,
    RoleHistoryListResponse,
    RoleHistoryResponse,
    RoleTypeEnum,
)

logger = get_logger(__name__)


class RoleHistoryService:
    """ロール変更履歴サービスクラス。

    ロール変更履歴の記録と取得を行います。
    """

    def __init__(self, db: AsyncSession):
        """ロール履歴サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = RoleHistoryRepository(db)

    @measure_performance
    async def record_system_role_change(
        self,
        user_id: uuid.UUID,
        old_roles: list[str],
        new_roles: list[str],
        changed_by_id: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> RoleHistory:
        """システムロールの変更履歴を記録します。

        Args:
            user_id: 変更対象ユーザーID
            old_roles: 変更前のロール
            new_roles: 変更後のロール
            changed_by_id: 変更実行者ID
            reason: 変更理由

        Returns:
            RoleHistory: 作成された履歴レコード
        """
        logger.info(
            "システムロール変更を記録中",
            user_id=str(user_id),
            old_roles=old_roles,
            new_roles=new_roles,
            changed_by_id=str(changed_by_id) if changed_by_id else None,
        )

        action = self._determine_action(old_roles, new_roles)

        history = await self.repository.create_history(
            user_id=user_id,
            action=action,
            role_type="system",
            old_roles=old_roles,
            new_roles=new_roles,
            changed_by_id=changed_by_id,
            reason=reason,
        )

        logger.info(
            "システムロール変更を記録しました",
            history_id=str(history.id),
            action=action,
        )

        return history

    @measure_performance
    async def record_project_role_change(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        old_roles: list[str],
        new_roles: list[str],
        changed_by_id: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> RoleHistory:
        """プロジェクトロールの変更履歴を記録します。

        Args:
            user_id: 変更対象ユーザーID
            project_id: 対象プロジェクトID
            old_roles: 変更前のロール
            new_roles: 変更後のロール
            changed_by_id: 変更実行者ID
            reason: 変更理由

        Returns:
            RoleHistory: 作成された履歴レコード
        """
        logger.info(
            "プロジェクトロール変更を記録中",
            user_id=str(user_id),
            project_id=str(project_id),
            old_roles=old_roles,
            new_roles=new_roles,
        )

        action = self._determine_action(old_roles, new_roles)

        history = await self.repository.create_history(
            user_id=user_id,
            action=action,
            role_type="project",
            project_id=project_id,
            old_roles=old_roles,
            new_roles=new_roles,
            changed_by_id=changed_by_id,
            reason=reason,
        )

        logger.info(
            "プロジェクトロール変更を記録しました",
            history_id=str(history.id),
            action=action,
        )

        return history

    @measure_performance
    async def get_user_role_history(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> RoleHistoryListResponse:
        """ユーザーのロール変更履歴を取得します。

        Args:
            user_id: 対象ユーザーID
            skip: スキップ数
            limit: 取得件数

        Returns:
            RoleHistoryListResponse: 履歴一覧レスポンス
        """
        logger.debug(
            "ユーザーロール履歴を取得中",
            user_id=str(user_id),
            skip=skip,
            limit=limit,
        )

        histories = await self.repository.get_by_user_id(user_id, skip=skip, limit=limit)
        total = await self.repository.count_by_user_id(user_id)

        history_responses = [self._to_response(h) for h in histories]

        return RoleHistoryListResponse(
            histories=history_responses,
            total=total,
            skip=skip,
            limit=limit,
        )

    @measure_performance
    async def get_project_role_history(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> RoleHistoryListResponse:
        """プロジェクトのロール変更履歴を取得します。

        Args:
            project_id: 対象プロジェクトID
            skip: スキップ数
            limit: 取得件数

        Returns:
            RoleHistoryListResponse: 履歴一覧レスポンス
        """
        logger.debug(
            "プロジェクトロール履歴を取得中",
            project_id=str(project_id),
            skip=skip,
            limit=limit,
        )

        histories = await self.repository.get_by_project_id(project_id, skip=skip, limit=limit)
        total = await self.repository.count_by_project_id(project_id)

        history_responses = [self._to_response(h) for h in histories]

        return RoleHistoryListResponse(
            histories=history_responses,
            total=total,
            skip=skip,
            limit=limit,
        )

    def _determine_action(self, old_roles: list[str], new_roles: list[str]) -> str:
        """ロール変更のアクションを決定します。

        Args:
            old_roles: 変更前ロール
            new_roles: 変更後ロール

        Returns:
            str: アクション（grant/revoke/update）
        """
        old_set = set(old_roles)
        new_set = set(new_roles)

        if not old_set and new_set:
            return "grant"
        elif old_set and not new_set:
            return "revoke"
        else:
            return "update"

    def _to_response(self, history: RoleHistory) -> RoleHistoryResponse:
        """履歴モデルをレスポンススキーマに変換します。

        Args:
            history: 履歴モデル

        Returns:
            RoleHistoryResponse: レスポンススキーマ
        """
        return RoleHistoryResponse(
            id=history.id,
            user_id=history.user_id,
            changed_by_id=history.changed_by_id,
            changed_by_name=history.changed_by.display_name if history.changed_by else None,
            action=RoleChangeActionEnum(history.action),
            role_type=RoleTypeEnum(history.role_type),
            project_id=history.project_id,
            project_name=history.project.name if history.project else None,
            old_roles=history.old_roles,
            new_roles=history.new_roles,
            reason=history.reason,
            changed_at=history.changed_at,
        )


__all__ = ["RoleHistoryService"]
