"""ドライバーツリーノード施策サービス。

このモジュールは、ドライバーツリーノードの施策設定CRUD操作を提供します。
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.services.driver_tree.driver_tree_node.base import DriverTreeNodeServiceBase

logger = get_logger(__name__)


class DriverTreeNodePolicyService(DriverTreeNodeServiceBase):
    """ドライバーツリーノードの施策設定CRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーノード施策サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @transactional
    async def create_policy(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        name: str,
        value: float,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """施策を設定します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            name: 施策名
            value: 施策値
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 作成結果
                - node_id: uuid - ノードID
                - policies: list[dict] - 施策リスト
        """
        logger.info(
            "施策を作成中",
            node_id=str(node_id),
            name=name,
            value=value,
            user_id=str(user_id),
        )

        await self._get_node_with_validation(node_id)

        # 施策を作成
        await self.policy_repository.create(
            node_id=node_id,
            label=name,
            value=value,
        )

        logger.info(
            "施策を作成しました",
            node_id=str(node_id),
            name=name,
        )

        return await self._build_policies_response(node_id)

    async def list_policies(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノードに設定されている全施策の一覧を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 施策一覧
                - node_id: uuid - ノードID
                - policies: list[dict] - 施策リスト
        """
        logger.info(
            "施策一覧を取得中",
            node_id=str(node_id),
            user_id=str(user_id),
        )

        await self._get_node_with_validation(node_id)

        logger.info(
            "施策一覧を取得しました",
            node_id=str(node_id),
        )

        return await self._build_policies_response(node_id)

    @transactional
    async def update_policy(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        policy_id: uuid.UUID,
        name: str | None,
        value: float | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """施策設定を更新します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            policy_id: 施策ID
            name: 施策名（オプション）
            value: 施策値（オプション）
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 更新結果
                - node_id: uuid - ノードID
                - policies: list[dict] - 施策リスト
        """
        logger.info(
            "施策を更新中",
            node_id=str(node_id),
            policy_id=str(policy_id),
            user_id=str(user_id),
        )

        await self._get_node_with_validation(node_id)

        # 施策を取得
        policy = await self.policy_repository.get(policy_id)
        if not policy:
            raise NotFoundError(
                "施策が見つかりません",
                details={"policy_id": str(policy_id)},
            )

        if policy.node_id != node_id:
            raise NotFoundError(
                "このノードに施策が見つかりません",
                details={"policy_id": str(policy_id), "node_id": str(node_id)},
            )

        # 更新データを構築
        update_data: dict[str, Any] = {}
        if name is not None:
            update_data["label"] = name
        if value is not None:
            update_data["value"] = value

        if update_data:
            await self.policy_repository.update(policy, **update_data)

        logger.info(
            "施策を更新しました",
            node_id=str(node_id),
            policy_id=str(policy_id),
        )

        return await self._build_policies_response(node_id)

    @transactional
    async def delete_policy(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        policy_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """施策設定を削除します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            policy_id: 施策ID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 削除結果
                - node_id: uuid - ノードID
                - policies: list[dict] - 施策リスト
        """
        logger.info(
            "施策を削除中",
            node_id=str(node_id),
            policy_id=str(policy_id),
            user_id=str(user_id),
        )

        await self._get_node_with_validation(node_id)

        # 施策を取得
        policy = await self.policy_repository.get(policy_id)
        if not policy:
            raise NotFoundError(
                "施策が見つかりません",
                details={"policy_id": str(policy_id)},
            )

        if policy.node_id != node_id:
            raise NotFoundError(
                "このノードに施策が見つかりません",
                details={"policy_id": str(policy_id), "node_id": str(node_id)},
            )

        # 施策を削除
        await self.policy_repository.delete(policy_id)

        logger.info(
            "施策を削除しました",
            node_id=str(node_id),
            policy_id=str(policy_id),
        )

        return await self._build_policies_response(node_id)
