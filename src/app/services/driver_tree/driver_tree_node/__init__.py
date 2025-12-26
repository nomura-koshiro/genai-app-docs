"""ドライバーツリーノードサービス。

このモジュールは、ドライバーツリーのノード管理ビジネスロジックを提供します。

主な機能:
    - ノードCRUD（作成、取得、更新、削除）
    - 入力ノードプレビューダウンロード
    - 施策設定CRUD

Note:
    実際の実装は各サブモジュールに分割されています:
    - base.py: 共通ヘルパー
    - crud.py: ノードCRUD操作
    - policy.py: 施策設定CRUD
"""

import uuid
from typing import Any

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.driver_tree.driver_tree_node.crud import DriverTreeNodeCrudService
from app.services.driver_tree.driver_tree_node.policy import DriverTreeNodePolicyService


class DriverTreeNodeService:
    """ドライバーツリーノード管理のビジネスロジックを提供するサービスクラス。

    ノードのCRUD、プレビューダウンロード、施策設定を提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """ドライバーツリーノードサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._crud_service = DriverTreeNodeCrudService(db)
        self._policy_service = DriverTreeNodePolicyService(db)

    # ================================================================================
    # ノード CRUD
    # ================================================================================

    async def create_node(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        label: str,
        node_type: str,
        position_x: int,
        position_y: int,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーに新規ノードを作成します。"""
        return await self._crud_service.create_node(project_id, tree_id, label, node_type, position_x, position_y, user_id)

    async def get_node(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノードの詳細情報を取得します。"""
        return await self._crud_service.get_node(project_id, node_id, user_id)

    async def update_node(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        label: str | None,
        node_type: str | None,
        position_x: int | None,
        position_y: int | None,
        operator: str | None,
        children_id_list: list[uuid.UUID] | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノード情報を更新します（PATCH）。"""
        return await self._crud_service.update_node(
            project_id, node_id, label, node_type, position_x, position_y, operator, children_id_list, user_id
        )

    async def delete_node(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノードを削除します。"""
        return await self._crud_service.delete_node(project_id, node_id, user_id)

    async def download_node_preview(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> StreamingResponse:
        """ノードデータをCSV形式でエクスポートします。"""
        return await self._crud_service.download_node_preview(project_id, node_id, user_id)

    # ================================================================================
    # 施策設定 CRUD
    # ================================================================================

    async def create_policy(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        name: str,
        value: float,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """施策を設定します。"""
        return await self._policy_service.create_policy(project_id, node_id, name, value, user_id)

    async def list_policies(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノードに設定されている全施策の一覧を取得します。"""
        return await self._policy_service.list_policies(project_id, node_id, user_id)

    async def update_policy(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        policy_id: uuid.UUID,
        name: str | None,
        value: float | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """施策設定を更新します。"""
        return await self._policy_service.update_policy(project_id, node_id, policy_id, name, value, user_id)

    async def delete_policy(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        policy_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """施策設定を削除します。"""
        return await self._policy_service.delete_policy(project_id, node_id, policy_id, user_id)


__all__ = ["DriverTreeNodeService"]
