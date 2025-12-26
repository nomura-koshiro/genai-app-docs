"""ドライバーツリーマスタデータサービス。

このモジュールは、ドライバーツリーのマスタデータ取得を提供します。
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.services.driver_tree.driver_tree.base import DriverTreeServiceBase

logger = get_logger(__name__)


class DriverTreeMasterService(DriverTreeServiceBase):
    """ドライバーツリーのマスタデータ取得を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーマスタサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    async def get_categories(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """業界分類一覧を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: Response schema に適合する形式
                {
                    "categories": [
                        {
                            "category_id": int,
                            "category_name": str,
                            "industries": [
                                {
                                    "industry_id": int,
                                    "industry_name": str,
                                    "driver_types": [
                                        {"driver_type_id": int, "driver_type": str},
                                        ...
                                    ]
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                }
        """
        logger.info("業界分類一覧を取得します", project_id=str(project_id), user_id=str(user_id))

        # Repositoryから階層構造を取得
        grouped_data = await self.category_repository.get_grouped_by_category()

        # Response schema に適合する形式に変換
        categories = []
        for category_id, category_data in grouped_data.items():
            # 業界名リストを構築
            industries = []
            for industry_id, industry_data in category_data["industries"].items():
                industries.append(
                    {
                        "industry_id": industry_id,
                        "industry_name": industry_data["industry_name"],
                        "driver_types": industry_data["driver_types"],  # 既に正しい形式
                    }
                )

            categories.append(
                {
                    "category_id": category_id,
                    "category_name": category_data["category_name"],
                    "industries": industries,
                }
            )

        logger.info(f"業界分類一覧を取得しました: {len(categories)}件", project_id=str(project_id))
        return {"categories": categories}

    async def get_formulas(
        self,
        project_id: uuid.UUID,
        driver_type_id: int,
        kpi: str,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """数式を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            driver_type_id: ドライバー型ID
            kpi: KPI
            user_id: ユーザーID

        Returns:
            dict[str, Any]: Response schema に適合する形式
                {
                    "formula": {
                        "formula_id": uuid,
                        "driver_type_id": int,
                        "driver_type": str,
                        "kpi": str,
                        "formulas": list[str]
                    }
                }

        Raises:
            NotFoundError: 数式が見つからない場合
        """
        logger.info(
            "数式を取得します",
            project_id=str(project_id),
            driver_type_id=driver_type_id,
            kpi=kpi,
            user_id=str(user_id),
        )

        formula = await self.formula_repository.get_by_driver_type_and_kpi(driver_type_id, kpi)

        if not formula:
            raise NotFoundError(
                "数式が見つかりません",
                details={"driver_type_id": driver_type_id, "kpi": kpi},
            )

        logger.info("数式を取得しました", formula_id=str(formula.id))

        # Response schema に適合する形式に変換
        return {
            "formula": {
                "formula_id": formula.id,
                "driver_type_id": formula.driver_type_id,
                "driver_type": formula.driver_type,
                "kpi": formula.kpi,
                "formulas": formula.formulas,
            }
        }
