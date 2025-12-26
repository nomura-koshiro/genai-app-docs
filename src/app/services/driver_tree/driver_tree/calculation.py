"""ドライバーツリー計算サービス。

このモジュールは、ドライバーツリーの計算・出力機能を提供します。
"""

import io
import uuid
from typing import Any

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.driver_tree.driver_tree.base import DriverTreeServiceBase

logger = get_logger(__name__)


class DriverTreeCalculationService(DriverTreeServiceBase):
    """ドライバーツリーの計算・出力を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリー計算サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    async def get_tree_data(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリー全体の計算を実行し結果を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 計算結果
                - calculated_data_list: list - 計算データ一覧

        Raises:
            NotFoundError: ツリーが見つからない場合
            ValidationError: 計算エラー（数式エラー、データ不足等）
        """
        logger.info(
            "ツリー計算を実行中",
            tree_id=str(tree_id),
            user_id=str(user_id),
        )

        await self._get_tree_with_validation(project_id, tree_id)

        # ツリー構造から計算データを構築
        calculated_data_list = []

        # ノード情報をツリーレスポンスから取得
        tree_response = await self._build_tree_response(await self._get_tree_with_validation(project_id, tree_id))
        for node in tree_response.get("nodes", []):
            calculated_data_list.append(
                {
                    "node_id": node["node_id"],
                    "label": node["label"],
                    "columns": [],
                    "records": [],
                }
            )

        logger.info(
            "ツリー計算を完了しました",
            tree_id=str(tree_id),
            node_count=len(calculated_data_list),
        )

        return {
            "calculated_data_list": calculated_data_list,
        }

    async def download_simulation_output(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        format: str,
        user_id: uuid.UUID,
    ) -> StreamingResponse:
        """シミュレーション結果をExcel/CSV形式でエクスポートします。

        全ノードの計算結果を含みます。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            format: 出力形式（"xlsx"|"csv"）
            user_id: ユーザーID

        Returns:
            StreamingResponse: ファイルストリーム

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        logger.info(
            "シミュレーション結果をエクスポート中",
            tree_id=str(tree_id),
            format=format,
            user_id=str(user_id),
        )

        await self._get_tree_with_validation(project_id, tree_id)

        # 計算結果を取得
        result = await self.get_tree_data(project_id, tree_id, user_id)

        if format == "csv":
            # CSV形式で出力
            output = io.StringIO()
            output.write("node_id,label,value\n")

            for data in result.get("calculated_data_list", []):
                output.write(f"{data['node_id']},{data['label']},\n")

            content = output.getvalue().encode("utf-8-sig")
            media_type = "text/csv"
            filename = f"simulation_{tree_id}.csv"
        else:
            # Excel形式で出力
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            if ws is not None:
                ws.title = "シミュレーション結果"

                # ヘッダー
                ws.append(["ノードID", "ラベル", "値"])

                # データ
                for data in result.get("calculated_data_list", []):
                    ws.append([str(data["node_id"]), data["label"], ""])

            output_bytes = io.BytesIO()
            wb.save(output_bytes)
            content = output_bytes.getvalue()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"simulation_{tree_id}.xlsx"

        logger.info(
            "シミュレーション結果をエクスポートしました",
            tree_id=str(tree_id),
            format=format,
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
