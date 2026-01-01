"""ドライバーツリーノードCRUDサービス。

このモジュールは、ドライバーツリーノードのCRUD操作を提供します。
"""

import io
import uuid
from typing import Any

from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.decorators import transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.driver_tree import (
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
)
from app.services.driver_tree.driver_tree_node.base import DriverTreeNodeServiceBase

logger = get_logger(__name__)


class DriverTreeNodeCrudService(DriverTreeNodeServiceBase):
    """ドライバーツリーノードのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーノードCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @transactional
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
        """ツリーに新規ノードを作成します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            label: ノード名
            node_type: ノードタイプ（入力|計算|定数）
            position_x: X座標
            position_y: Y座標
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 作成結果
                - tree: dict - ツリー全体の最新構造
                - created_node_id: uuid - 作成されたノードID

        Raises:
            NotFoundError: ツリーが見つからない場合
            ValidationError: 不正なノード設定の場合
        """
        logger.info(
            "ノードを作成中",
            tree_id=str(tree_id),
            label=label,
            node_type=node_type,
            user_id=str(user_id),
        )

        # ツリーを取得
        tree = await self.tree_repository.get_with_relations(tree_id)
        if not tree:
            raise NotFoundError(
                "ツリーが見つかりません",
                details={"tree_id": str(tree_id)},
            )

        if tree.project_id != project_id:
            raise NotFoundError(
                "このプロジェクトにツリーが見つかりません",
                details={"tree_id": str(tree_id), "project_id": str(project_id)},
            )

        # ノードタイプのバリデーション
        valid_node_types = ["入力", "計算", "定数"]
        if node_type not in valid_node_types:
            raise ValidationError(
                "不正なノードタイプです",
                details={"node_type": node_type, "valid_types": valid_node_types},
            )

        # ノードを作成
        node = await self.node_repository.create(
            driver_tree_id=tree.id,
            label=label,
            node_type=node_type,
            position_x=position_x,
            position_y=position_y,
        )

        logger.info(
            "ノードを作成しました",
            node_id=str(node.id),
            tree_id=str(tree_id),
            label=label,
        )

        tree_response = await self._build_tree_response(tree)

        return {
            "tree": tree_response,
            "created_node_id": node.id,
        }

    async def get_node(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノードの詳細情報を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: ノード情報

        Raises:
            NotFoundError: ノードが見つからない場合
        """
        logger.info(
            "ノード詳細を取得中",
            node_id=str(node_id),
            user_id=str(user_id),
        )

        node = await self._get_node_with_validation(node_id)

        # 入力ノードのデータを取得
        data = None
        if node.node_type == "入力" and node.data_frame:
            data = node.data_frame.data

        # 計算ノードの親子関係を取得
        relationship = None
        result = await self.db.execute(
            select(DriverTreeRelationship)
            .where(DriverTreeRelationship.parent_node_id == node_id)
            .options(selectinload(DriverTreeRelationship.children))
        )
        rel = result.scalar_one_or_none()
        if rel:
            relationship = {
                "operator": rel.operator,
                "child_id_list": [c.child_node_id for c in rel.children],
            }

        logger.info(
            "ノード詳細を取得しました",
            node_id=str(node_id),
        )

        return {
            "node_id": node.id,
            "label": node.label,
            "position_x": node.position_x or 0,
            "position_y": node.position_y or 0,
            "node_type": node.node_type,
            "data": data,
            "relationship": relationship,
        }

    @transactional
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
        """ノード情報を更新します（PATCH）。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            label: ノード名（オプション）
            node_type: ノードタイプ（オプション）
            position_x: X座標（オプション）
            position_y: Y座標（オプション）
            operator: 計算ノード演算子（オプション）
            children_id_list: 計算ノードの子ノードIDリスト（オプション）
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 更新結果
                - tree: dict - ツリー全体の最新構造

        Raises:
            NotFoundError: ノードが見つからない場合
            ValidationError: バリデーションエラー
        """
        logger.info(
            "ノードを更新中",
            node_id=str(node_id),
            user_id=str(user_id),
        )

        node = await self._get_node_with_validation(node_id)

        # ノード基本情報の更新
        update_data: dict[str, Any] = {}
        if label is not None:
            update_data["label"] = label
        if node_type is not None:
            valid_node_types = ["入力", "計算", "定数"]
            if node_type not in valid_node_types:
                raise ValidationError(
                    "不正なノードタイプです",
                    details={"node_type": node_type, "valid_types": valid_node_types},
                )
            update_data["node_type"] = node_type
        if position_x is not None:
            update_data["position_x"] = position_x
        if position_y is not None:
            update_data["position_y"] = position_y

        if update_data:
            await self.node_repository.update(node, **update_data)

        # リレーションシップの更新（operator, children_id_list）
        if operator is not None or children_id_list is not None:
            # 既存のリレーションシップを取得
            result = await self.db.execute(
                select(DriverTreeRelationship)
                .where(DriverTreeRelationship.parent_node_id == node_id)
                .options(selectinload(DriverTreeRelationship.children))
            )
            existing_rel = result.scalar_one_or_none()

            if existing_rel:
                # 演算子の更新
                if operator is not None:
                    existing_rel.operator = operator

                # 子ノードの更新
                if children_id_list is not None:
                    # 循環参照チェック
                    await self._validate_no_circular_reference(node_id, children_id_list)

                    # 既存の子を削除
                    for child in existing_rel.children:
                        await self.db.delete(child)

                    # 新しい子を追加（正規化されたorder_indexを使用）
                    normalized_indices = self._normalize_order_indices(len(children_id_list))
                    for i, child_id in enumerate(children_id_list):
                        child_rel = DriverTreeRelationshipChild(
                            relationship_id=existing_rel.id,
                            child_node_id=child_id,
                            order_index=normalized_indices[i],
                        )
                        self.db.add(child_rel)

                await self.db.flush()

        # ノードが属するツリーを取得
        tree = await self._get_tree_by_node(node_id)
        if not tree:
            raise NotFoundError(
                "ノードが属するツリーが見つかりません",
                details={"node_id": str(node_id)},
            )

        logger.info(
            "ノードを更新しました",
            node_id=str(node_id),
        )

        tree_response = await self._build_tree_response(tree)

        return {"tree": tree_response}

    @transactional
    async def delete_node(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ノードを削除します。

        子ノードは自動的に削除されません。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 削除結果
                - tree: dict - ツリー全体の最新構造

        Raises:
            NotFoundError: ノードが見つからない場合
        """
        logger.info(
            "ノードを削除中",
            node_id=str(node_id),
            user_id=str(user_id),
        )

        await self._get_node_with_validation(node_id)

        # ノードが属するツリーを取得
        tree = await self._get_tree_by_node(node_id)
        if not tree:
            raise NotFoundError(
                "ノードが属するツリーが見つかりません",
                details={"node_id": str(node_id)},
            )

        # ルートノードの削除は禁止
        if tree.root_node_id == node_id:
            raise ValidationError(
                "ルートノードは削除できません",
                details={"node_id": str(node_id)},
            )

        # 親ノードとしてのリレーションシップを削除
        result = await self.db.execute(select(DriverTreeRelationship).where(DriverTreeRelationship.parent_node_id == node_id))
        for rel in result.scalars().all():
            await self.db.delete(rel)

        # 子ノードとしてのリレーションシップエントリを削除
        result = await self.db.execute(select(DriverTreeRelationshipChild).where(DriverTreeRelationshipChild.child_node_id == node_id))
        for child_rel in result.scalars().all():
            await self.db.delete(child_rel)

        # ノードを削除
        await self.node_repository.delete(node_id)

        logger.info(
            "ノードを削除しました",
            node_id=str(node_id),
        )

        tree_response = await self._build_tree_response(tree)

        return {"tree": tree_response}

    async def download_node_preview(
        self,
        project_id: uuid.UUID,
        node_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> StreamingResponse:
        """ノードデータをCSV形式でエクスポートします。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            node_id: ノードID
            user_id: ユーザーID

        Returns:
            StreamingResponse: CSVファイルストリーム

        Raises:
            NotFoundError: ノードが見つからない場合
        """
        logger.info(
            "ノードプレビューをダウンロード中",
            node_id=str(node_id),
            user_id=str(user_id),
        )

        node = await self._get_node_with_validation(node_id)

        # CSV形式で出力
        output = io.StringIO()
        output.write("node_id,label,node_type,value\n")

        # 入力ノードのデータを出力
        if node.node_type == "入力" and node.data_frame and node.data_frame.data:
            raw_data = node.data_frame.data
            for key, value in raw_data.items():
                output.write(f"{node.id},{node.label},{node.node_type},{key}:{value}\n")
        else:
            output.write(f"{node.id},{node.label},{node.node_type},\n")

        content = output.getvalue().encode("utf-8-sig")
        filename = f"node_preview_{node_id}.csv"

        logger.info(
            "ノードプレビューをダウンロードしました",
            node_id=str(node_id),
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
