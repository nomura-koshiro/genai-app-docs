"""ドライバーツリーテンプレートサービス。

このモジュールは、ドライバーツリーテンプレートのビジネスロジックを提供します。

主な機能:
    - テンプレート一覧取得
    - テンプレート作成（ツリーから）
    - テンプレート削除
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.repositories.driver_tree import DriverTreeRepository, DriverTreeTemplateRepository
from app.schemas.driver_tree import (
    DriverTreeTemplateCreateRequest,
    DriverTreeTemplateCreateResponse,
    DriverTreeTemplateDeleteResponse,
    DriverTreeTemplateInfo,
    DriverTreeTemplateListResponse,
)

logger = get_logger(__name__)


class DriverTreeTemplateService:
    """ドライバーツリーテンプレート管理のビジネスロジックを提供するサービスクラス。

    テンプレート一覧の取得、テンプレート作成、削除を提供します。
    """

    def __init__(self, db: AsyncSession):
        """ドライバーツリーテンプレートサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.template_repository = DriverTreeTemplateRepository(db)
        self.tree_repository = DriverTreeRepository(db)

    async def list_templates(
        self,
        project_id: uuid.UUID,
        include_public: bool = True,
        category: str | None = None,
    ) -> DriverTreeTemplateListResponse:
        """テンプレート一覧を取得します。

        Args:
            project_id: プロジェクトID
            include_public: 公開テンプレートを含めるか
            category: カテゴリでフィルタ

        Returns:
            テンプレート一覧レスポンス
        """
        templates = await self.template_repository.list_by_project(
            project_id=project_id, include_public=include_public, category=category
        )

        template_infos = [
            DriverTreeTemplateInfo(
                template_id=t.id,
                name=t.name,
                description=t.description,
                category=t.category,
                node_count=len(t.template_config.get("nodes", [])) if t.template_config else 0,
                is_public=t.is_public,
                usage_count=t.usage_count,
                created_by=t.created_by,
                created_by_name=f"{t.creator.email}" if t.creator else None,
                created_at=t.created_at,
            )
            for t in templates
        ]

        logger.info(
            "ドライバーツリーテンプレート一覧取得",
            project_id=str(project_id),
            count=len(template_infos),
        )

        return DriverTreeTemplateListResponse(
            templates=template_infos,
            total=len(template_infos),
        )

    async def create_template(
        self,
        project_id: uuid.UUID,
        request: DriverTreeTemplateCreateRequest,
        user_id: uuid.UUID,
    ) -> DriverTreeTemplateCreateResponse:
        """ツリーからテンプレートを作成します。

        Args:
            project_id: プロジェクトID
            request: テンプレート作成リクエスト
            user_id: 作成者ユーザーID

        Returns:
            作成されたテンプレート情報

        Raises:
            NotFoundError: 元ツリーが見つからない
            AuthorizationError: 権限がない
        """
        # 元ツリーの取得（ノード含む）
        source_tree = await self.tree_repository.get_with_relations(request.source_tree_id)
        if not source_tree:
            raise NotFoundError("元ツリーが見つかりません")

        # プロジェクトIDの検証
        if source_tree.project_id != project_id:
            raise AuthorizationError("他のプロジェクトのツリーからテンプレートを作成できません")

        # ノード情報を取得
        nodes = source_tree.nodes

        # ノードリストを作成
        nodes_config = [
            {
                "label": node.label,
                "nodeType": node.node_type,
                "relativeX": node.position_x if node.position_x is not None else 0,
                "relativeY": node.position_y if node.position_y is not None else 0,
            }
            for node in nodes
        ]
        node_count = len(nodes_config)

        # テンプレート設定を作成
        template_config = {
            "nodes": nodes_config,
            "relationships": [
                {
                    "parentLabel": rel.parent_node.label if rel.parent_node else "",
                    "childLabels": [child.child_node.label for child in rel.children if child.child_node],
                    "operator": rel.operator or "",
                }
                for rel in source_tree.relationships
            ],
        }

        # テンプレート作成
        template = await self.template_repository.create(
            project_id=project_id if not request.is_public else None,  # 公開テンプレートはグローバル
            name=request.name,
            description=request.description,
            category=request.category,
            template_config=template_config,
            source_tree_id=request.source_tree_id,
            is_public=request.is_public,
            created_by=user_id,
        )

        logger.info(
            "ドライバーツリーテンプレート作成完了",
            template_id=str(template.id),
            project_id=str(project_id),
            user_id=str(user_id),
            node_count=node_count,
        )

        return DriverTreeTemplateCreateResponse(
            template_id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            template_config=template.template_config,
            node_count=node_count,
            created_at=template.created_at,
        )

    async def delete_template(
        self,
        project_id: uuid.UUID,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DriverTreeTemplateDeleteResponse:
        """テンプレートを削除します。

        Args:
            project_id: プロジェクトID
            template_id: テンプレートID
            user_id: リクエストユーザーID

        Returns:
            削除レスポンス

        Raises:
            NotFoundError: テンプレートが見つからない
            ForbiddenError: 削除権限がない
        """
        # テンプレートの取得
        template = await self.template_repository.get_by_id(template_id)
        if not template:
            raise NotFoundError("テンプレートが見つかりません")

        # 権限チェック: プロジェクト固有テンプレートの場合、同じプロジェクトであること
        if template.project_id and template.project_id != project_id:
            raise AuthorizationError("他のプロジェクトのテンプレートは削除できません")

        # 作成者のみ削除可能
        if template.created_by != user_id:
            raise AuthorizationError("テンプレートの作成者のみ削除できます")

        # 削除実行
        deleted = await self.template_repository.delete(template_id)
        if not deleted:
            raise NotFoundError("テンプレートが見つかりません")

        logger.info(
            "ドライバーツリーテンプレート削除完了",
            template_id=str(template_id),
            project_id=str(project_id),
            user_id=str(user_id),
        )

        return DriverTreeTemplateDeleteResponse(
            success=True,
            deleted_at=datetime.now(UTC),
        )
