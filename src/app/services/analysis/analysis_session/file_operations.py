"""ファイル操作サービス。

セッションのファイル登録、設定更新、入力ファイル選択を提供します。
"""

import uuid
from io import BytesIO
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisFileConfigResponse,
    AnalysisFileCreate,
    AnalysisFileResponse,
    AnalysisFileUpdate,
    AnalysisSessionDetailResponse,
)
from app.services.analysis.analysis_session.base import AnalysisSessionServiceBase
from app.services.analysis.analysis_session.excel_parser import parse_hierarchical_excel
from app.services.storage.excel import get_excel_sheet_names, read_excel_sheet

logger = get_logger(__name__)


class AnalysisSessionFileService(AnalysisSessionServiceBase):
    """ファイル操作機能を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ファイル操作サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    async def list_session_files(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> list[AnalysisFileResponse]:
        """セッションに登録されたファイル一覧を取得します。

        ファイルID、PJTファイル名、シート名、軸、データを含みます。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID

        Returns:
            list[AnalysisFileResponse]: ファイル一覧

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションの存在確認
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # ファイル一覧を取得
        files = await self.file_repository.list_by_session(session_id)

        return [
            AnalysisFileResponse(
                id=f.id,
                session_id=f.session_id,
                project_file_id=f.project_file_id,
                project_file_name=f.project_file.original_filename if f.project_file else "",
                sheet_name=f.sheet_name,
                axis_config=f.axis_config,
                data=f.data if f.data else [],
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in files
        ]

    @transactional
    async def upload_session_file(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        file_create: AnalysisFileCreate,
    ) -> AnalysisFileConfigResponse:
        """セッションにファイルを登録します。

        - PJTファイル名
        - シート名と軸の候補

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            file_create: ファイル作成リクエスト

        Returns:
            AnalysisFileConfigResponse: 登録されたファイル情報

        Raises:
            NotFoundError: セッションまたはプロジェクトファイルが見つからない場合
            ValidationError: ファイル形式が不正、またはExcel処理に失敗した場合
        """
        # セッションの存在確認
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # プロジェクトファイルを取得
        project_file = await self.project_file_repository.get(file_create.project_file_id)
        if not project_file or project_file.project_id != project_id:
            raise NotFoundError(
                "Project file not found",
                details={"project_file_id": str(file_create.project_file_id)},
            )

        # StorageServiceを使ってファイルをダウンロード
        excel_bytes = await self.storage.download("", project_file.file_path)
        excel_io = BytesIO(excel_bytes)

        # シート名一覧を取得（共通関数使用）
        project_file_sheet_list = get_excel_sheet_names(excel_io)

        # シートごとに軸候補を生成
        config_list = []
        for sheet_name in project_file_sheet_list:
            try:
                excel_io.seek(0)  # BytesIOを先頭に戻す
                sheet_data = read_excel_sheet(excel_io, sheet_name)
                axis, values, header_section, data_section = parse_hierarchical_excel(sheet_data)
                axis_name = [a[0] for a in axis][:-1]  # index=-1の科目軸は必須なので、選択候補から除外
                config_list.append(
                    {
                        "sheet_name": sheet_name,
                        "axis": axis_name,
                    }
                )
            except Exception as e:
                logger.warning(
                    "シートの処理をスキップしました",
                    sheet_name=sheet_name,
                    project_file_id=str(file_create.project_file_id),
                    error=str(e),
                )
                # 問題があるシートはスキップして続行
                continue

        if len(config_list) == 0:
            raise ValidationError(
                "No valid sheets found in the Excel file. The file must contain at least one sheet with proper header/data format.",
                details={"project_file_id": str(file_create.project_file_id)},
            )

        # 分析ファイルを作成（初期状態）
        analysis_file = await self.file_repository.create(
            session_id=session_id,
            project_file_id=file_create.project_file_id,
            sheet_name="",  # 後でupdate_file_configで設定
            axis_config={},
            data=[],
        )

        return AnalysisFileConfigResponse(
            id=analysis_file.id,
            config_list=config_list,
        )

    @transactional
    async def update_file_config(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        file_id: uuid.UUID,
        config_data: AnalysisFileUpdate,
    ) -> AnalysisFileResponse:
        """ファイルの設定(シート、軸)を更新します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            file_id: ファイルID
            config_data: 設定データ（シート選択、軸選択）

        Returns:
            AnalysisFileResponse: 更新結果

        Raises:
            NotFoundError: セッションまたはファイルが見つからない場合
            ValidationError: シート名・軸名が不正、またはExcel処理に失敗した場合
        """
        # セッションの存在確認
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # ファイルの存在確認
        analysis_file = await self.file_repository.get_with_project_file(file_id)
        if not analysis_file or analysis_file.session_id != session_id:
            raise NotFoundError(
                "File not found",
                details={"file_id": str(file_id)},
            )

        # ファイル設定を更新
        update_data: dict[str, Any] = {}

        # シート名の決定
        sheet_name_to_use: str
        if config_data.sheet_name is not None:
            sheet_name_to_use = config_data.sheet_name
        elif analysis_file.sheet_name:
            sheet_name_to_use = analysis_file.sheet_name
        else:
            raise ValidationError(
                "Sheet name must be specified",
                details={"file_id": str(file_id)},
            )
        update_data["sheet_name"] = sheet_name_to_use

        # 軸設定の決定
        axis_config_to_use: dict[str, str]
        if config_data.axis_config is not None:
            axis_config_to_use = config_data.axis_config
        elif analysis_file.axis_config:
            axis_config_to_use = analysis_file.axis_config
        else:
            raise ValidationError(
                "Axis config must be specified",
                details={"file_id": str(file_id)},
            )
        update_data["axis_config"] = axis_config_to_use

        # プロジェクトファイルを取得
        project_file = await self.project_file_repository.get(analysis_file.project_file_id)
        if not project_file or project_file.project_id != project_id:
            raise NotFoundError(
                "Project file not found",
                details={"project_file_id": str(analysis_file.project_file_id)},
            )

        # StorageServiceを使ってファイルをダウンロード
        excel_bytes = await self.storage.download("", project_file.file_path)
        excel_io = BytesIO(excel_bytes)

        # シート名一覧を取得してバリデーション（共通関数使用）
        available_sheets = get_excel_sheet_names(excel_io)

        # シート名の存在確認
        if sheet_name_to_use not in available_sheets:
            raise ValidationError(
                f"Sheet '{sheet_name_to_use}' not found in Excel file",
                details={
                    "sheet_name": sheet_name_to_use,
                    "available_sheets": available_sheets,
                },
            )

        # シートデータを読み込み（共通関数使用）
        excel_io.seek(0)
        sheet_data = read_excel_sheet(excel_io, sheet_name_to_use)
        axis, values, header_section, data_section = parse_hierarchical_excel(sheet_data)

        # 利用可能な軸名を取得（科目を除く）
        available_axis_names = [a[0] for a in axis][:-1]

        # 選択された軸名のバリデーション
        selected_axis_values = list(axis_config_to_use.values())
        invalid_axis = [ax for ax in selected_axis_values if ax not in available_axis_names]
        if invalid_axis:
            raise ValidationError(
                f"Invalid axis name(s): {', '.join(invalid_axis)}",
                details={
                    "invalid_axis": invalid_axis,
                    "available_axis": available_axis_names,
                },
            )

        # 選択された軸に基づいてデータを整形
        required_columns = selected_axis_values + ["科目", "値"]
        update_data["data"] = values[required_columns].to_dict(orient="records")  # type: ignore[call-overload]

        # ファイルを更新
        analysis_file = await self.file_repository.update(analysis_file, **update_data)

        # リレーションを再取得
        updated_file = await self.file_repository.get_with_project_file(file_id)
        if not updated_file:
            raise NotFoundError(
                "File not found after update",
                details={"file_id": str(file_id)},
            )

        logger.info(
            "ファイル設定を更新しました",
            file_id=str(file_id),
            sheet_name=sheet_name_to_use,
            axis_config=axis_config_to_use,
        )

        return AnalysisFileResponse(
            id=updated_file.id,
            session_id=updated_file.session_id,
            project_file_id=updated_file.project_file_id,
            project_file_name=updated_file.project_file.original_filename if updated_file.project_file else "",
            sheet_name=updated_file.sheet_name,
            axis_config=updated_file.axis_config,
            data=updated_file.data,
            created_at=updated_file.created_at,
            updated_at=updated_file.updated_at,
        )

    @transactional
    async def select_input_file(
        self,
        session_id: uuid.UUID,
        file_id: uuid.UUID | None,
    ) -> AnalysisSessionDetailResponse:
        """分析に使用する入力ファイルを選択します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            session_id: セッションID
            file_id: 分析ファイルID

        Returns:
            AnalysisSessionDetailResponse: 選択結果（ファイル名、シート名、軸、データ）

        Raises:
            NotFoundError: セッションまたはファイルが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get_with_relations(session_id)
        if not session:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # ファイルの存在確認（指定がある場合）
        if file_id is not None and file_id != session.input_file_id:
            analysis_file = await self.file_repository.get(file_id)
            if not analysis_file or analysis_file.session_id != session_id:
                raise NotFoundError(
                    "File not found",
                    details={"file_id": str(file_id)},
                )

        # セッションの入力ファイルを更新
        session = await self.session_repository.update(session, input_file_id=file_id)

        # 0より大きなsnapshot（後続分）を削除する（chat, stepも一緒に）
        snapshots = await self.snapshot_repository.list_by_session(session_id)
        for snap in snapshots:
            if snap.snapshot_order > 0:
                await self._delete_snapshot(snap.id)

        # スナップショットを取得
        snapshots = await self.snapshot_repository.list_by_session_with_relations(session_id)

        # ファイルを取得
        files = await self.file_repository.list_by_session(session_id)

        return self._build_session_detail_response(session, snapshots, files)
