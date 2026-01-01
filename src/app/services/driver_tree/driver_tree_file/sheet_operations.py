"""シート操作モジュール。

シート選択、削除、一覧取得を提供します。
"""

import uuid
from datetime import UTC
from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.driver_tree import DriverTreeDataFrameRepository, DriverTreeFileRepository
from app.repositories.project import ProjectFileRepository
from app.services.storage import StorageService

from .excel_parser import parse_driver_tree_excel

logger = get_logger(__name__)


class SheetOperationsMixin:
    """シート操作機能を提供するMixinクラス。

    Attributes:
        db: データベースセッション
        file_repository: DriverTreeFileリポジトリ
        data_frame_repository: DriverTreeDataFrameリポジトリ
        project_file_repository: ProjectFileリポジトリ
        storage: ストレージサービス
        container: コンテナ名（service.pyで定義）
    """

    db: AsyncSession
    file_repository: DriverTreeFileRepository
    data_frame_repository: DriverTreeDataFrameRepository
    project_file_repository: ProjectFileRepository
    storage: StorageService
    container: str

    @measure_performance
    async def list_selected_sheets(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """選択済みシート一覧を取得します。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 選択済みシート一覧
        """
        logger.info(
            "選択済みシート一覧取得リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            action="list_selected_sheets",
        )

        # 1. プロジェクトの全ProjectFileを取得
        project_files = await self.project_file_repository.list_by_project(project_id)

        # 2. 各ファイルに対してシート情報を取得（選択済みのもののみ）
        result_files = []
        for project_file in project_files:
            # 各ファイルに紐づくシート一覧を取得
            driver_tree_files = await self.file_repository.list_by_project_file(project_file.id)

            # 選択済みシート情報を構築
            sheets = []
            for driver_tree_file in driver_tree_files:
                # axis_configが空でないシートのみを処理（選択済みシート）
                axis_config = driver_tree_file.axis_config or {}
                if not axis_config:
                    continue

                # axis_configからカラム情報を取得
                columns = []

                # axis_configの各カラムをcolumnsリストに変換
                for column_id, config in axis_config.items():
                    if not isinstance(config, dict):
                        continue

                    column_name = config.get("column_name", "")
                    role = config.get("role", "利用しない")
                    items = config.get("items", [])
                    if not items:
                        continue

                    columns.append(
                        {
                            "column_id": column_id,
                            "column_name": column_name,
                            "role": role,
                            "items": items,
                        }
                    )
                if columns:
                    sheets.append(
                        {
                            "sheet_id": driver_tree_file.id,
                            "sheet_name": driver_tree_file.sheet_name,
                            "columns": columns,
                        }
                    )

            # 選択済みのシートがある場合のみファイルを結果に追加
            if sheets:
                result_files.append(
                    {
                        "file_id": project_file.id,
                        "filename": project_file.original_filename,
                        "uploaded_at": project_file.uploaded_at,
                        "sheets": sheets,
                    }
                )

        logger.info(
            "選択済みシート一覧を取得しました",
            user_id=str(user_id),
            project_id=str(project_id),
            file_count=len(result_files),
        )

        return {"files": result_files}

    @transactional
    @measure_performance
    async def select_sheet(
        self,
        project_id: uuid.UUID,
        file_id: uuid.UUID,
        sheet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """シートを選択して送信します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            sheet_id: シートID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 選択結果

        Raises:
            NotFoundError: ファイルまたはシートが見つからない場合
        """
        logger.info(
            "シート選択リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            action="select_sheet",
        )

        # 1. ProjectFileを取得
        project_file = await self.project_file_repository.get(file_id)
        if not project_file:
            raise NotFoundError(
                "ファイルが見つかりません",
                details={"file_id": str(file_id)},
            )

        # 2. プロジェクトIDの確認
        if project_file.project_id != project_id:
            raise NotFoundError(
                "このプロジェクト内で該当ファイルが見つかりません",
                details={"file_id": str(file_id), "project_id": str(project_id)},
            )

        # 3. DriverTreeFileを取得（sheet_id = DriverTreeFile.id）
        driver_tree_file = await self.file_repository.get(sheet_id)
        if not driver_tree_file:
            raise NotFoundError(
                "シートが見つかりません",
                details={"sheet_id": str(sheet_id)},
            )

        # 4. DriverTreeFileがProjectFileに紐づいているか確認
        if driver_tree_file.project_file_id != file_id:
            raise NotFoundError(
                "このファイル内で該当シートが見つかりません",
                details={"sheet_id": str(sheet_id), "file_id": str(file_id)},
            )

        # 5. 既存のDataFrameをチェック（既に選択済みかどうか）
        if driver_tree_file.axis_config and len(driver_tree_file.axis_config) > 0:
            logger.info(
                "シートは既に選択済みです",
                sheet_id=str(sheet_id),
            )

            result = {"success": False}
            result.update(await self.list_selected_sheets(project_id, user_id))
            return result

        # 6. StorageServiceを使用してExcelファイルを読み込み、2つのDataFrameに分割
        excel_bytes = await self.storage.download(self.container, project_file.file_path)
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), driver_tree_file.sheet_name)

        # 7. axis_configを構築
        axis_config = self._build_axis_config(df_metadata, df_data)

        # 8. DriverTreeFileを取得して、axis_configを更新
        driver_tree_file = await self.file_repository.get(sheet_id)
        if not driver_tree_file:
            raise NotFoundError("ドライバーツリーが見つかりません", details={"file_id": str(sheet_id)})

        await self.file_repository.update(driver_tree_file, axis_config=axis_config)

        # 9. DriverTreeDataFrameにデータを保存
        await self._save_data_frames(sheet_id, df_metadata, df_data)

        logger.info(
            "シートを選択しました",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            column_count=len(axis_config),
            data_frame_count=len(df_metadata.columns) + 1,
        )

        result = {"success": True}
        result.update(await self.list_selected_sheets(project_id, user_id))
        return result

    def _build_axis_config(self, df_metadata: pd.DataFrame, df_data: pd.DataFrame) -> dict[str, Any]:
        """axis_configを構築します。

        Args:
            df_metadata: メタデータDataFrame
            df_data: データDataFrame

        Returns:
            dict[str, Any]: axis_config
        """
        axis_config: dict[str, Any] = {}

        # メタデータの各列を処理（FY、地域、対象など）
        for column_name in df_metadata.columns:
            if pd.isna(column_name):
                continue

            column_name_str = str(column_name)
            column_series = df_metadata[column_name]
            items_all = [str(item) if not pd.isna(item) else "" for item in column_series]

            # 重複を削除しつつ順序を保持
            items_unique = list(dict.fromkeys(items_all))
            items = items_unique[:5]

            column_id = str(uuid.uuid4())
            axis_config[column_id] = {
                "column_name": column_name_str,
                "role": "利用しない",
                "items": items,
            }

        # データの列名を「科目」として処理
        data_column_names = [str(col) for col in df_data.columns if pd.notna(col)]
        available_count = min(5, len(data_column_names))
        items = data_column_names[:available_count]

        column_id = str(uuid.uuid4())
        axis_config[column_id] = {
            "column_name": "科目",
            "role": "利用しない",
            "items": items,
        }

        return axis_config

    async def _save_data_frames(
        self,
        sheet_id: uuid.UUID,
        df_metadata: pd.DataFrame,
        df_data: pd.DataFrame,
    ) -> None:
        """DriverTreeDataFrameにデータを保存します。

        Args:
            sheet_id: シートID
            df_metadata: メタデータDataFrame
            df_data: データDataFrame
        """
        # メタデータの各列をDriverTreeDataFrameに保存
        for column_name in df_metadata.columns:
            if pd.isna(column_name):
                continue

            column_name_str = str(column_name)
            column_series = df_metadata[column_name]

            data_dict = {}
            for idx, value in enumerate(column_series):
                if not pd.isna(value):
                    data_dict[str(idx)] = str(value)

            await self.data_frame_repository.create(
                driver_tree_file_id=sheet_id,
                column_name=column_name_str,
                data=data_dict,
            )

        # 「科目」列のデータをDriverTreeDataFrameに保存
        subject_data_dict: dict[str, Any] = {}
        for column_name in df_data.columns:
            if pd.isna(column_name):
                continue
            column_name_str = str(column_name)

            column_series = df_data[column_name]
            for idx, value in enumerate(column_series):
                if not pd.isna(value):
                    if column_name_str not in subject_data_dict:
                        subject_data_dict[column_name_str] = {}
                    subject_data_dict[column_name_str][str(idx)] = str(value) if isinstance(value, str) else float(value)

        await self.data_frame_repository.create(
            driver_tree_file_id=sheet_id,
            column_name="科目",
            data=subject_data_dict,
        )

    @transactional
    @measure_performance
    async def delete_sheet(
        self,
        project_id: uuid.UUID,
        file_id: uuid.UUID,
        sheet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """選択済みシートを削除します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            sheet_id: シートID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 削除結果

        Raises:
            NotFoundError: ファイルまたはシートが見つからない場合
        """
        logger.info(
            "シート削除リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            action="delete_sheet",
        )

        # 1. ProjectFileが存在するか確認
        project_file = await self.project_file_repository.get(file_id)
        if not project_file:
            raise NotFoundError("ファイルが見つかりません", details={"file_id": str(file_id)})

        # 2. ProjectFileがこのプロジェクトに紐づいているか確認
        if project_file.project_id != project_id:
            raise NotFoundError(
                "このプロジェクト内で該当ファイルが見つかりません",
                details={"file_id": str(file_id), "project_id": str(project_id)},
            )

        # 3. DriverTreeFileが存在するか確認
        driver_tree_file = await self.file_repository.get(sheet_id)
        if not driver_tree_file:
            raise NotFoundError("シートが見つかりません", details={"sheet_id": str(sheet_id)})

        # 4. DriverTreeFileがProjectFileに紐づいているか確認
        if driver_tree_file.project_file_id != file_id:
            raise NotFoundError(
                "このファイル内で該当シートが見つかりません",
                details={"sheet_id": str(sheet_id), "file_id": str(file_id)},
            )

        # 5. axis_configをクリア（選択を解除）
        await self.file_repository.update(driver_tree_file, axis_config={})

        # 6. 関連するDriverTreeDataFrameを全削除
        data_frames = await self.data_frame_repository.list_by_file(sheet_id)
        for data_frame in data_frames:
            await self.data_frame_repository.delete(data_frame.id)

        logger.info(
            "シートを削除しました",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            deleted_data_frames=len(data_frames),
        )

        # 7. 削除後の選択済みシート一覧を返す
        result = {"success": True}
        result.update(await self.list_selected_sheets(project_id, user_id))
        return result

    @transactional
    @measure_performance
    async def refresh_sheet(
        self,
        project_id: uuid.UUID,
        file_id: uuid.UUID,
        sheet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """シートのデータを元ファイルから再読み込みして更新します。

        ファイルの内容が更新された場合に、最新のデータを反映させるために使用します。
        axis_config（カラム設定）は保持したまま、データのみを更新します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            sheet_id: シートID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 更新結果
                - success (bool): 更新成功フラグ
                - updated_at (datetime): 更新日時
                - files (list): 更新後の選択済みシート一覧

        Raises:
            NotFoundError: ファイルまたはシートが見つからない場合
        """
        from datetime import datetime

        logger.info(
            "シートデータ更新リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            action="refresh_sheet",
        )

        # 1. ProjectFileを取得
        project_file = await self.project_file_repository.get(file_id)
        if not project_file:
            raise NotFoundError(
                "ファイルが見つかりません",
                details={"file_id": str(file_id)},
            )

        # 2. プロジェクトIDの確認
        if project_file.project_id != project_id:
            raise NotFoundError(
                "このプロジェクト内で該当ファイルが見つかりません",
                details={"file_id": str(file_id), "project_id": str(project_id)},
            )

        # 3. DriverTreeFileを取得
        driver_tree_file = await self.file_repository.get(sheet_id)
        if not driver_tree_file:
            raise NotFoundError(
                "シートが見つかりません",
                details={"sheet_id": str(sheet_id)},
            )

        # 4. DriverTreeFileがProjectFileに紐づいているか確認
        if driver_tree_file.project_file_id != file_id:
            raise NotFoundError(
                "このファイル内で該当シートが見つかりません",
                details={"sheet_id": str(sheet_id), "file_id": str(file_id)},
            )

        # 5. シートが選択済みか確認
        if not driver_tree_file.axis_config or len(driver_tree_file.axis_config) == 0:
            raise NotFoundError(
                "シートが選択されていません",
                details={"sheet_id": str(sheet_id)},
            )

        # 6. 既存のDataFrameを全削除
        existing_data_frames = await self.data_frame_repository.list_by_file(sheet_id)
        for data_frame in existing_data_frames:
            await self.data_frame_repository.delete(data_frame.id)

        # 7. StorageServiceを使用してExcelファイルを再読み込み
        excel_bytes = await self.storage.download(self.container, project_file.file_path)
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), driver_tree_file.sheet_name)

        # 8. 新しいaxis_configを構築（カラム情報を更新）
        new_axis_config = self._build_axis_config(df_metadata, df_data)

        # 9. DriverTreeFileのaxis_configを更新
        await self.file_repository.update(driver_tree_file, axis_config=new_axis_config)

        # 10. 新しいDataFrameを保存
        await self._save_data_frames(sheet_id, df_metadata, df_data)

        updated_at = datetime.now(UTC)

        logger.info(
            "シートデータを更新しました",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            column_count=len(new_axis_config),
            updated_at=updated_at.isoformat(),
        )

        result = {
            "success": True,
            "updated_at": updated_at,
        }
        result.update(await self.list_selected_sheets(project_id, user_id))
        return result

    @measure_performance
    async def get_sheet_detail(
        self,
        project_id: uuid.UUID,
        file_id: uuid.UUID,
        sheet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """シート詳細を取得します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            sheet_id: シートID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: シート詳細情報
                - sheet_id (uuid.UUID): シートID
                - sheet_name (str): シート名
                - columns (list[dict]): カラム情報リスト
                - row_count (int): 行数
                - sample_data (list[dict]): サンプルデータ（最初の10行）

        Raises:
            NotFoundError: ファイルまたはシートが見つからない場合
        """
        logger.info(
            "シート詳細取得リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            action="get_sheet_detail",
        )

        # 1. ProjectFileを取得
        project_file = await self.project_file_repository.get(file_id)
        if not project_file:
            raise NotFoundError(
                "ファイルが見つかりません",
                details={"file_id": str(file_id)},
            )

        # 2. プロジェクトIDの確認
        if project_file.project_id != project_id:
            raise NotFoundError(
                "このプロジェクト内で該当ファイルが見つかりません",
                details={"file_id": str(file_id), "project_id": str(project_id)},
            )

        # 3. DriverTreeFileを取得
        driver_tree_file = await self.file_repository.get(sheet_id)
        if not driver_tree_file:
            raise NotFoundError(
                "シートが見つかりません",
                details={"sheet_id": str(sheet_id)},
            )

        # 4. DriverTreeFileがProjectFileに紐づいているか確認
        if driver_tree_file.project_file_id != file_id:
            raise NotFoundError(
                "このファイル内で該当シートが見つかりません",
                details={"sheet_id": str(sheet_id), "file_id": str(file_id)},
            )

        # 5. StorageServiceを使用してExcelファイルを読み込み
        excel_bytes = await self.storage.download(self.container, project_file.file_path)
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), driver_tree_file.sheet_name)

        # 6. カラム情報を解析
        columns = self._analyze_columns(df_metadata, df_data)

        # 7. サンプルデータを構築（最初の10行）
        sample_data = self._build_sample_data(df_metadata, df_data, limit=10)

        # 8. 行数を計算
        row_count = len(df_metadata)

        logger.info(
            "シート詳細を取得しました",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            sheet_id=str(sheet_id),
            column_count=len(columns),
            row_count=row_count,
        )

        return {
            "sheet_id": sheet_id,
            "sheet_name": driver_tree_file.sheet_name,
            "columns": columns,
            "row_count": row_count,
            "sample_data": sample_data,
        }

    def _analyze_columns(self, df_metadata: pd.DataFrame, df_data: pd.DataFrame) -> list[dict[str, Any]]:
        """DataFrameからカラム情報を解析します。

        Args:
            df_metadata: メタデータDataFrame
            df_data: データDataFrame

        Returns:
            list[dict[str, Any]]: カラム情報リスト
        """
        columns = []

        # メタデータの各列を処理
        for column_name in df_metadata.columns:
            if pd.isna(column_name):
                continue

            column_name_str = str(column_name)
            column_series = df_metadata[column_name]

            # データ型を推定
            data_type = self._infer_data_type(column_series)

            # 役割を推定
            role = self._infer_role(column_name_str, data_type)

            columns.append(
                {
                    "name": column_name_str,
                    "display_name": column_name_str,
                    "data_type": data_type,
                    "role": role,
                }
            )

        # データの「科目」列を追加
        columns.append(
            {
                "name": "科目",
                "display_name": "科目",
                "data_type": "string",
                "role": "カテゴリ",
            }
        )

        return columns

    def _infer_data_type(self, series: pd.Series) -> str:
        """シリーズからデータ型を推定します。

        Args:
            series: Pandasシリーズ

        Returns:
            str: データ型（string/number/datetime/boolean）
        """
        # NaN以外の最初の値を取得
        first_value = None
        for value in series:
            if not pd.isna(value):
                first_value = value
                break

        if first_value is None:
            return "string"

        if isinstance(first_value, bool):
            return "boolean"

        if isinstance(first_value, int | float):
            return "number"

        if isinstance(first_value, pd.Timestamp):
            return "datetime"

        # 文字列の場合、日付として解析できるか試す
        if isinstance(first_value, str):
            try:
                pd.to_datetime(first_value)
                return "datetime"
            except (ValueError, TypeError):
                pass

        return "string"

    def _infer_role(self, column_name: str, data_type: str) -> str:
        """カラム名とデータ型から役割を推定します。

        Args:
            column_name: カラム名
            data_type: データ型

        Returns:
            str: 役割（推移/値/カテゴリ）
        """
        name_lower = column_name.lower()

        # 日付関連の列名または日時型の場合は「推移」
        if "date" in name_lower or "日付" in name_lower or "fy" in name_lower or data_type == "datetime":
            return "推移"

        # 数値型の場合は「値」
        if data_type == "number":
            return "値"

        # その他は「カテゴリ」
        return "カテゴリ"

    def _build_sample_data(
        self,
        df_metadata: pd.DataFrame,
        df_data: pd.DataFrame,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """サンプルデータを構築します。

        Args:
            df_metadata: メタデータDataFrame
            df_data: データDataFrame
            limit: 取得する行数

        Returns:
            list[dict[str, Any]]: サンプルデータ
        """
        sample_data = []

        # メタデータとデータを結合してサンプルデータを作成
        for idx in range(min(limit, len(df_metadata))):
            row_data: dict[str, Any] = {}

            # メタデータの値を追加
            for column_name in df_metadata.columns:
                if pd.isna(column_name):
                    continue

                column_name_str = str(column_name)
                value = df_metadata.iloc[idx][column_name]

                if pd.isna(value):
                    row_data[column_name_str] = None
                else:
                    row_data[column_name_str] = str(value)

            # データの最初の列の値を「科目」として追加（サンプル表示用）
            if len(df_data.columns) > 0:
                first_data_col = df_data.columns[0]
                if idx < len(df_data):
                    value = df_data.iloc[idx][first_data_col]
                    if not pd.isna(value):
                        row_data["科目"] = str(first_data_col)
                        row_data["値"] = float(value) if isinstance(value, int | float) else str(value)

            sample_data.append(row_data)

        return sample_data
