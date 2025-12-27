"""分析ダミーチャートマスタリポジトリ。"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis.analysis_dummy_chart_master import AnalysisDummyChartMaster
from app.schemas.analysis.analysis_template import (
    AnalysisDummyChartCreate,
    AnalysisDummyChartUpdate,
)


class AnalysisDummyChartRepository:
    """分析ダミーチャートマスタリポジトリ。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, chart_id: uuid.UUID) -> AnalysisDummyChartMaster | None:
        """IDでダミーチャートマスタを取得。"""
        result = await self.db.execute(select(AnalysisDummyChartMaster).where(AnalysisDummyChartMaster.id == chart_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        issue_id: uuid.UUID | None = None,
    ) -> list[AnalysisDummyChartMaster]:
        """ダミーチャートマスタ一覧を取得。"""
        query = select(AnalysisDummyChartMaster).order_by(AnalysisDummyChartMaster.chart_order)

        if issue_id:
            query = query.where(AnalysisDummyChartMaster.issue_id == issue_id)

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self, issue_id: uuid.UUID | None = None) -> int:
        """ダミーチャートマスタ件数を取得。"""
        query = select(func.count(AnalysisDummyChartMaster.id))
        if issue_id:
            query = query.where(AnalysisDummyChartMaster.issue_id == issue_id)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, chart_create: AnalysisDummyChartCreate) -> AnalysisDummyChartMaster:
        """ダミーチャートマスタを作成。"""
        chart = AnalysisDummyChartMaster(**chart_create.model_dump())
        self.db.add(chart)
        await self.db.flush()
        await self.db.refresh(chart)
        return chart

    async def update(
        self,
        chart: AnalysisDummyChartMaster,
        chart_update: AnalysisDummyChartUpdate,
    ) -> AnalysisDummyChartMaster:
        """ダミーチャートマスタを更新。"""
        update_data = chart_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(chart, key, value)
        await self.db.flush()
        await self.db.refresh(chart)
        return chart

    async def delete(self, chart: AnalysisDummyChartMaster) -> None:
        """ダミーチャートマスタを削除。"""
        await self.db.delete(chart)
        await self.db.flush()
