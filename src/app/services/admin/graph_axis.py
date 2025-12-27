"""グラフ軸マスタ管理サービス。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin import AnalysisGraphAxisRepository
from app.schemas.admin.graph_axis import (
    AnalysisGraphAxisListResponse,
)
from app.schemas.analysis.analysis_template import (
    AnalysisGraphAxisCreate,
    AnalysisGraphAxisResponse,
    AnalysisGraphAxisUpdate,
)

logger = get_logger(__name__)


class AdminGraphAxisService:
    """グラフ軸マスタ管理サービス。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = AnalysisGraphAxisRepository(db)

    async def list_axes(
        self,
        skip: int = 0,
        limit: int = 100,
        issue_id: uuid.UUID | None = None,
    ) -> AnalysisGraphAxisListResponse:
        """グラフ軸マスタ一覧を取得。"""
        axes = await self.repository.list(skip=skip, limit=limit, issue_id=issue_id)
        total = await self.repository.count(issue_id=issue_id)

        return AnalysisGraphAxisListResponse(
            axes=[AnalysisGraphAxisResponse.model_validate(axis) for axis in axes],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_axis(self, axis_id: uuid.UUID) -> AnalysisGraphAxisResponse:
        """グラフ軸マスタ詳細を取得。"""
        axis = await self.repository.get_by_id(axis_id)
        if not axis:
            raise NotFoundError(f"グラフ軸マスタが見つかりません: {axis_id}")

        return AnalysisGraphAxisResponse.model_validate(axis)

    async def create_axis(self, axis_create: AnalysisGraphAxisCreate) -> AnalysisGraphAxisResponse:
        """グラフ軸マスタを作成。"""
        axis = await self.repository.create(axis_create)
        await self.db.commit()

        logger.info(f"グラフ軸マスタ作成: id={axis.id}")
        return AnalysisGraphAxisResponse.model_validate(axis)

    async def update_axis(
        self,
        axis_id: uuid.UUID,
        axis_update: AnalysisGraphAxisUpdate,
    ) -> AnalysisGraphAxisResponse:
        """グラフ軸マスタを更新。"""
        axis = await self.repository.get_by_id(axis_id)
        if not axis:
            raise NotFoundError(f"グラフ軸マスタが見つかりません: {axis_id}")

        axis = await self.repository.update(axis, axis_update)
        await self.db.commit()

        logger.info(f"グラフ軸マスタ更新: id={axis.id}")
        return AnalysisGraphAxisResponse.model_validate(axis)

    async def delete_axis(self, axis_id: uuid.UUID) -> None:
        """グラフ軸マスタを削除。"""
        axis = await self.repository.get_by_id(axis_id)
        if not axis:
            raise NotFoundError(f"グラフ軸マスタが見つかりません: {axis_id}")

        await self.repository.delete(axis)
        await self.db.commit()

        logger.info(f"グラフ軸マスタ削除: id={axis_id}")
