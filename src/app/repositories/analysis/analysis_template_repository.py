"""分析テンプレートリポジトリ。

このモジュールは、分析テンプレートのデータアクセスロジックを提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.analysis.analysis_template import AnalysisTemplate
from app.models.user_account.user_account import UserAccount

logger = get_logger(__name__)


class AnalysisTemplateRepository:
    """分析テンプレートリポジトリ。

    分析テンプレートのCRUD操作を提供します。
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
        template_type: str,
        template_config: dict,
        source_session_id: uuid.UUID | None,
        is_public: bool,
        created_by: uuid.UUID,
    ) -> AnalysisTemplate:
        """テンプレートを作成します。

        Args:
            project_id: プロジェクトID（NULLの場合はグローバル）
            name: テンプレート名
            description: 説明
            template_type: テンプレートタイプ
            template_config: テンプレート設定
            source_session_id: 元セッションID
            is_public: 公開フラグ
            created_by: 作成者ID

        Returns:
            作成されたテンプレート
        """
        template = AnalysisTemplate(
            project_id=project_id,
            name=name,
            description=description,
            template_type=template_type,
            template_config=template_config,
            source_session_id=source_session_id,
            is_public=is_public,
            created_by=created_by,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(
            "分析テンプレート作成完了",
            template_id=str(template.id),
            name=name,
        )

        return template

    async def get_by_id(self, template_id: uuid.UUID) -> AnalysisTemplate | None:
        """IDでテンプレートを取得します。

        Args:
            template_id: テンプレートID

        Returns:
            テンプレート、または見つからない場合はNone
        """
        result = await self.db.execute(
            select(AnalysisTemplate)
            .where(AnalysisTemplate.id == template_id)
            .options(selectinload(AnalysisTemplate.creator))
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        include_public: bool = True,
        template_type: str | None = None,
    ) -> list[AnalysisTemplate]:
        """プロジェクトのテンプレート一覧を取得します。

        Args:
            project_id: プロジェクトID
            include_public: 公開テンプレートを含めるか
            template_type: テンプレートタイプでフィルタ

        Returns:
            テンプレート一覧
        """
        query = select(AnalysisTemplate).options(selectinload(AnalysisTemplate.creator))

        # プロジェクト固有 or グローバル公開テンプレート
        if include_public:
            query = query.where(
                (AnalysisTemplate.project_id == project_id)
                | ((AnalysisTemplate.project_id.is_(None)) & (AnalysisTemplate.is_public == True))  # noqa: E712
            )
        else:
            query = query.where(AnalysisTemplate.project_id == project_id)

        # タイプフィルタ
        if template_type:
            query = query.where(AnalysisTemplate.template_type == template_type)

        query = query.order_by(AnalysisTemplate.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete(self, template_id: uuid.UUID) -> bool:
        """テンプレートを削除します。

        Args:
            template_id: テンプレートID

        Returns:
            削除成功した場合True
        """
        result = await self.db.execute(delete(AnalysisTemplate).where(AnalysisTemplate.id == template_id))
        await self.db.commit()

        logger.info(
            "分析テンプレート削除完了",
            template_id=str(template_id),
            deleted=result.rowcount > 0,
        )

        return result.rowcount > 0

    async def increment_usage_count(self, template_id: uuid.UUID) -> None:
        """使用回数をインクリメントします。

        Args:
            template_id: テンプレートID
        """
        await self.db.execute(
            update(AnalysisTemplate)
            .where(AnalysisTemplate.id == template_id)
            .values(usage_count=AnalysisTemplate.usage_count + 1)
        )
        await self.db.commit()

        logger.debug("テンプレート使用回数インクリメント", template_id=str(template_id))
