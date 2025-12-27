"""分析グラフ軸マスタリポジトリ。"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis.analysis_graph_axis_master import AnalysisGraphAxisMaster
from app.schemas.analysis.analysis_template import AnalysisGraphAxisCreate, AnalysisGraphAxisUpdate


class AnalysisGraphAxisRepository:
    """分析グラフ軸マスタリポジトリ。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, axis_id: uuid.UUID) -> AnalysisGraphAxisMaster | None:
        """IDでグラフ軸マスタを取得。"""
        result = await self.db.execute(select(AnalysisGraphAxisMaster).where(AnalysisGraphAxisMaster.id == axis_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        issue_id: uuid.UUID | None = None,
    ) -> list[AnalysisGraphAxisMaster]:
        """グラフ軸マスタ一覧を取得。"""
        query = select(AnalysisGraphAxisMaster).order_by(AnalysisGraphAxisMaster.axis_order)

        if issue_id:
            query = query.where(AnalysisGraphAxisMaster.issue_id == issue_id)

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self, issue_id: uuid.UUID | None = None) -> int:
        """グラフ軸マスタ件数を取得。"""
        query = select(func.count(AnalysisGraphAxisMaster.id))
        if issue_id:
            query = query.where(AnalysisGraphAxisMaster.issue_id == issue_id)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, axis_create: AnalysisGraphAxisCreate) -> AnalysisGraphAxisMaster:
        """グラフ軸マスタを作成。"""
        axis = AnalysisGraphAxisMaster(**axis_create.model_dump())
        self.db.add(axis)
        await self.db.flush()
        await self.db.refresh(axis)
        return axis

    async def update(
        self,
        axis: AnalysisGraphAxisMaster,
        axis_update: AnalysisGraphAxisUpdate,
    ) -> AnalysisGraphAxisMaster:
        """グラフ軸マスタを更新。"""
        update_data = axis_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(axis, key, value)
        await self.db.flush()
        await self.db.refresh(axis)
        return axis

    async def delete(self, axis: AnalysisGraphAxisMaster) -> None:
        """グラフ軸マスタを削除。"""
        await self.db.delete(axis)
        await self.db.flush()
