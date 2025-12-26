"""分析テンプレート（施策・課題）リポジトリ。

このモジュールは、AnalysisValidationMaster、AnalysisIssueMasterモデルに特化した
データベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.analysis import AnalysisIssueMaster, AnalysisValidationMaster
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisValidationRepository(BaseRepository[AnalysisValidationMaster, uuid.UUID]):
    """AnalysisValidationMasterモデル用のリポジトリクラス。

    施策マスタデータの取得を提供します。
    """

    def __init__(self, db: AsyncSession):
        """施策リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisValidationMaster, db)

    async def list_with_issues(self) -> list[AnalysisValidationMaster]:
        """課題を含む施策一覧を取得します。

        Returns:
            list[AnalysisValidationMaster]: 施策一覧（課題含む、順序順）
        """
        result = await self.db.execute(
            select(AnalysisValidationMaster)
            .options(selectinload(AnalysisValidationMaster.issues))
            .order_by(AnalysisValidationMaster.validation_order.asc())
        )
        validations = list(result.scalars().all())

        # 各施策内の課題をissue_orderでソート
        for validation in validations:
            validation.issues.sort(key=lambda x: x.issue_order)

        return validations


class AnalysisIssueRepository(BaseRepository[AnalysisIssueMaster, uuid.UUID]):
    """AnalysisIssueMasterモデル用のリポジトリクラス。

    課題マスタデータの取得を提供します。
    """

    def __init__(self, db: AsyncSession):
        """課題リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisIssueMaster, db)

    async def get_with_details(self, issue_id: uuid.UUID) -> AnalysisIssueMaster | None:
        """詳細情報を含む課題を取得します。

        Args:
            issue_id: 課題ID

        Returns:
            AnalysisIssueMaster | None: 課題（軸設定、計算式、チャート含む）
        """
        result = await self.db.execute(
            select(AnalysisIssueMaster)
            .where(AnalysisIssueMaster.id == issue_id)
            .options(
                selectinload(AnalysisIssueMaster.validation),
                selectinload(AnalysisIssueMaster.graph_axes),
                selectinload(AnalysisIssueMaster.dummy_formulas),
                selectinload(AnalysisIssueMaster.dummy_charts),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_validation(self, validation_id: uuid.UUID) -> list[AnalysisIssueMaster]:
        """施策に属する課題一覧を取得します。

        Args:
            validation_id: 施策ID

        Returns:
            list[AnalysisIssueMaster]: 課題一覧（順序順）
        """
        result = await self.db.execute(
            select(AnalysisIssueMaster)
            .where(AnalysisIssueMaster.validation_id == validation_id)
            .order_by(AnalysisIssueMaster.issue_order.asc())
        )
        return list(result.scalars().all())

    async def list_catalog(self) -> list[AnalysisIssueMaster]:
        """カタログ用の課題一覧を取得します（施策情報含む）。

        Returns:
            list[AnalysisIssueMaster]: 課題一覧（施策含む、施策順序→課題順序でソート）
        """
        result = await self.db.execute(
            select(AnalysisIssueMaster)
            .options(selectinload(AnalysisIssueMaster.validation))
            .join(AnalysisIssueMaster.validation)
            .order_by(
                AnalysisValidationMaster.validation_order.asc(),
                AnalysisIssueMaster.issue_order.asc(),
            )
        )
        return list(result.scalars().all())
