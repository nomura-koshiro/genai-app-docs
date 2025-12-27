"""ダミーチャートマスタ管理サービス。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin import AnalysisDummyChartRepository
from app.schemas.admin.dummy_chart import (
    AnalysisDummyChartListResponse,
)
from app.schemas.analysis.analysis_template import (
    AnalysisDummyChartCreate,
    AnalysisDummyChartResponse,
    AnalysisDummyChartUpdate,
)

logger = get_logger(__name__)


class AdminDummyChartService:
    """ダミーチャートマスタ管理サービス。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = AnalysisDummyChartRepository(db)

    async def list_charts(
        self,
        skip: int = 0,
        limit: int = 100,
        issue_id: uuid.UUID | None = None,
    ) -> AnalysisDummyChartListResponse:
        """ダミーチャートマスタ一覧を取得。"""
        charts = await self.repository.list(skip=skip, limit=limit, issue_id=issue_id)
        total = await self.repository.count(issue_id=issue_id)

        return AnalysisDummyChartListResponse(
            charts=[AnalysisDummyChartResponse.model_validate(chart) for chart in charts],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_chart(self, chart_id: uuid.UUID) -> AnalysisDummyChartResponse:
        """ダミーチャートマスタ詳細を取得。"""
        chart = await self.repository.get_by_id(chart_id)
        if not chart:
            raise NotFoundError(f"ダミーチャートマスタが見つかりません: {chart_id}")

        return AnalysisDummyChartResponse.model_validate(chart)

    async def create_chart(self, chart_create: AnalysisDummyChartCreate) -> AnalysisDummyChartResponse:
        """ダミーチャートマスタを作成。"""
        chart = await self.repository.create(chart_create)
        await self.db.commit()

        logger.info(f"ダミーチャートマスタ作成: id={chart.id}")
        return AnalysisDummyChartResponse.model_validate(chart)

    async def update_chart(
        self,
        chart_id: uuid.UUID,
        chart_update: AnalysisDummyChartUpdate,
    ) -> AnalysisDummyChartResponse:
        """ダミーチャートマスタを更新。"""
        chart = await self.repository.get_by_id(chart_id)
        if not chart:
            raise NotFoundError(f"ダミーチャートマスタが見つかりません: {chart_id}")

        chart = await self.repository.update(chart, chart_update)
        await self.db.commit()

        logger.info(f"ダミーチャートマスタ更新: id={chart.id}")
        return AnalysisDummyChartResponse.model_validate(chart)

    async def delete_chart(self, chart_id: uuid.UUID) -> None:
        """ダミーチャートマスタを削除。"""
        chart = await self.repository.get_by_id(chart_id)
        if not chart:
            raise NotFoundError(f"ダミーチャートマスタが見つかりません: {chart_id}")

        await self.repository.delete(chart)
        await self.db.commit()

        logger.info(f"ダミーチャートマスタ削除: id={chart_id}")
