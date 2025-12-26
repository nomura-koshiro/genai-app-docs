"""ドライバーツリー数式リポジトリ。

このモジュールは、DriverTreeFormulaモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.driver_tree import DriverTreeFormula
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeFormulaRepository(BaseRepository[DriverTreeFormula, uuid.UUID]):
    """DriverTreeFormulaモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    数式マスタ管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """数式リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTreeFormula, db)

    async def get_by_driver_type_and_kpi(
        self,
        driver_type_id: int,
        kpi: str,
    ) -> DriverTreeFormula | None:
        """ドライバー型IDとKPIで数式を検索します。

        Args:
            driver_type_id: ドライバー型ID
            kpi: KPI

        Returns:
            DriverTreeFormula | None: 数式
        """
        result = await self.db.execute(
            select(DriverTreeFormula).where(DriverTreeFormula.driver_type_id == driver_type_id).where(DriverTreeFormula.kpi == kpi)
        )
        return result.scalar_one_or_none()

    async def list_by_driver_type(self, driver_type_id: int) -> list[DriverTreeFormula]:
        """ドライバー型IDで数式一覧を取得します。
        TODO: KPI選択で数式取得方法を確認し、必要なFuncだけ残す
        Args:
            driver_type_id: ドライバー型ID

        Returns:
            list[DriverTreeFormula]: 数式一覧（KPI別）
        """
        result = await self.db.execute(
            select(DriverTreeFormula).where(DriverTreeFormula.driver_type_id == driver_type_id).order_by(DriverTreeFormula.kpi.asc())
        )
        return list(result.scalars().all())
