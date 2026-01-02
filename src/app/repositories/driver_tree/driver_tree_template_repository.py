"""ドライバーツリーテンプレートリポジトリ。

このモジュールは、ドライバーツリーテンプレートのデータアクセスロジックを提供します。
"""

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.driver_tree.driver_tree_template import DriverTreeTemplate

logger = get_logger(__name__)


class DriverTreeTemplateRepository:
    """ドライバーツリーテンプレートリポジトリ。

    ドライバーツリーテンプレートのCRUD操作を提供します。
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: データベースセッション
        """
        self.db = db

    async def create(
        self,
        project_id: uuid.UUID | None,
        name: str,
        description: str | None,
        category: str | None,
        template_config: dict,
        source_tree_id: uuid.UUID | None,
        is_public: bool,
        created_by: uuid.UUID,
    ) -> DriverTreeTemplate:
        """テンプレートを作成します。

        Args:
            project_id: プロジェクトID（NULLの場合はグローバル）
            name: テンプレート名
            description: 説明
            category: カテゴリ（業種）
            template_config: テンプレート設定
            source_tree_id: 元ツリーID
            is_public: 公開フラグ
            created_by: 作成者ID

        Returns:
            作成されたテンプレート
        """
        template = DriverTreeTemplate(
            project_id=project_id,
            name=name,
            description=description,
            category=category,
            template_config=template_config,
            source_tree_id=source_tree_id,
            is_public=is_public,
            created_by=created_by,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(
            "ドライバーツリーテンプレート作成完了",
            template_id=str(template.id),
            name=name,
        )

        return template

    async def get_by_id(self, template_id: uuid.UUID) -> DriverTreeTemplate | None:
        """IDでテンプレートを取得します。

        Args:
            template_id: テンプレートID

        Returns:
            テンプレート、または見つからない場合はNone
        """
        result = await self.db.execute(
            select(DriverTreeTemplate)
            .where(DriverTreeTemplate.id == template_id)
            .options(selectinload(DriverTreeTemplate.creator))
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        include_public: bool = True,
        category: str | None = None,
    ) -> list[DriverTreeTemplate]:
        """プロジェクトのテンプレート一覧を取得します。

        Args:
            project_id: プロジェクトID
            include_public: 公開テンプレートを含めるか
            category: カテゴリでフィルタ

        Returns:
            テンプレート一覧
        """
        query = select(DriverTreeTemplate).options(selectinload(DriverTreeTemplate.creator))

        # プロジェクト固有 or グローバル公開テンプレート
        if include_public:
            query = query.where(
                (DriverTreeTemplate.project_id == project_id)
                | ((DriverTreeTemplate.project_id.is_(None)) & (DriverTreeTemplate.is_public == True))  # noqa: E712
            )
        else:
            query = query.where(DriverTreeTemplate.project_id == project_id)

        # カテゴリフィルタ
        if category:
            query = query.where(DriverTreeTemplate.category == category)

        query = query.order_by(DriverTreeTemplate.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete(self, template_id: uuid.UUID) -> bool:
        """テンプレートを削除します。

        Args:
            template_id: テンプレートID

        Returns:
            削除成功した場合True
        """
        result = await self.db.execute(delete(DriverTreeTemplate).where(DriverTreeTemplate.id == template_id))
        await self.db.commit()

        # TODO: SQLAlchemy 2.0の型スタブではResult型にrowcount属性が定義されていない
        # DML操作（delete/update）後のresultは実際にはCursorResultでrowcount属性を持つ
        deleted = (result.rowcount or 0) > 0  # type: ignore[attr-defined]
        logger.info(
            "ドライバーツリーテンプレート削除完了",
            template_id=str(template_id),
            deleted=deleted,
        )

        return deleted

    async def increment_usage_count(self, template_id: uuid.UUID) -> None:
        """使用回数をインクリメントします。

        Args:
            template_id: テンプレートID
        """
        await self.db.execute(
            update(DriverTreeTemplate)
            .where(DriverTreeTemplate.id == template_id)
            .values(usage_count=DriverTreeTemplate.usage_count + 1)
        )
        await self.db.commit()

        logger.debug("テンプレート使用回数インクリメント", template_id=str(template_id))
