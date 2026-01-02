"""ドライバーツリーカテゴリリポジトリ。

このモジュールは、DriverTreeCategoryモデルに特化したデータベース操作を提供します。
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.driver_tree import DriverTreeCategory
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeCategoryRepository(BaseRepository[DriverTreeCategory, uuid.UUID]):
    """DriverTreeCategoryモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    業界分類・ドライバー型マッピングに特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """カテゴリリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTreeCategory, db)

    async def get_grouped_by_category(self) -> dict[uuid.UUID, dict[str, Any]]:
        """業界分類でグループ化したカテゴリ情報を取得します。

        Returns:
            dict: 業界分類ID → {業界分類名, 業界名ID → {業界名, ドライバー型のリスト}}
                例: {
                    1: {
                        "category_name": "農業、林業",
                        "industries": {
                            1: {
                                "industry_name": "農業",
                                "driver_types": [
                                    {
                                        "driver_type_id": 8,
                                        "driver_type": "生産_製造数量×出荷率型"
                                    }
                                ]
                            },
                            2: {
                                "industry_name": "林業",
                                "driver_types": [
                                    {
                                        "driver_type_id": 7,
                                        "driver_type": "採取数量×出荷率型"
                                    }
                                ]
                            }
                        }
                    },
                    2: {
                        "category_name": "漁業",
                        "industries": {
                            3: {
                                "industry_name": "漁業（水産養殖業を除く）",
                                "driver_types": [...]
                            }
                        }
                    },
                    ...
                }
        """
        result = await self.db.execute(
            select(DriverTreeCategory).order_by(
                DriverTreeCategory.category_id.asc(), DriverTreeCategory.industry_id.asc(), DriverTreeCategory.driver_type_id.asc()
            )
        )
        categories = result.scalars().all()

        # 業界分類ID → {業界分類名, 業界名ID → {業界名, ドライバー型}} の階層構造を構築
        grouped: dict[uuid.UUID, dict[str, Any]] = {}

        for category in categories:
            category_id = category.category_id
            category_name = category.category_name
            industry_id = category.industry_id
            industry_name = category.industry_name

            # 業界分類が存在しない場合は初期化
            if category_id not in grouped:
                grouped[category_id] = {"category_name": category_name, "industries": {}}

            # 業界名が存在しない場合は初期化
            if industry_id not in grouped[category_id]["industries"]:
                grouped[category_id]["industries"][industry_id] = {"industry_name": industry_name, "driver_types": []}

            # ドライバー型を追加
            grouped[category_id]["industries"][industry_id]["driver_types"].append(
                {
                    "driver_type_id": category.driver_type_id,
                    "driver_type": category.driver_type,
                }
            )

        return grouped
