"""ProjectFile シーダー。"""

import uuid
from typing import Any

from app.models import Project, ProjectFile, UserAccount
from app.models.driver_tree import DriverTreeDataFrame, DriverTreeFile

from .base import BaseSeeder


class ProjectFileSeederMixin(BaseSeeder):
    """ProjectFile作成用Mixin。"""

    async def create_project_file(
        self,
        *,
        project: Project,
        uploader: UserAccount | None = None,
        filename: str = "test_file.xlsx",
        original_filename: str = "original_test_file.xlsx",
        file_path: str = "/uploads/test_file.xlsx",
        file_size: int = 1024,
        mime_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        uploaded_by: uuid.UUID | None = None,
    ) -> ProjectFile:
        """プロジェクトファイルを作成。

        Args:
            project: プロジェクト
            uploader: アップロードユーザー（後方互換性のため残す）
            filename: ファイル名
            original_filename: 元ファイル名
            file_path: ファイルパス
            file_size: ファイルサイズ
            mime_type: MIMEタイプ
            uploaded_by: アップロードユーザーID

        Returns:
            ProjectFile: 作成されたプロジェクトファイル
        """
        # uploaded_byの決定（uploaderが指定されている場合はそのidを使用）
        uploader_id = uploaded_by
        if uploader is not None:
            uploader_id = uploader.id

        project_file = ProjectFile(
            project_id=project.id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=uploader_id,
        )
        self.db.add(project_file)
        await self.db.flush()
        await self.db.refresh(project_file)
        self._created_data.files.append(project_file)
        return project_file

    async def create_driver_tree_file(
        self,
        *,
        project_file: ProjectFile,
        sheet_name: str = "Sheet1",
        axis_config: dict[str, Any] | None = None,
        added_by: uuid.UUID | None = None,
    ) -> DriverTreeFile:
        """ドライバーツリーファイルを作成。

        Args:
            project_file: プロジェクトファイル
            sheet_name: シート名
            axis_config: 軸設定
            added_by: 追加者ユーザーID

        Returns:
            DriverTreeFile: 作成されたドライバーツリーファイル
        """
        driver_tree_file = DriverTreeFile(
            project_file_id=project_file.id,
            sheet_name=sheet_name,
            axis_config=axis_config or {},
            added_by=added_by,
        )
        self.db.add(driver_tree_file)
        await self.db.flush()
        await self.db.refresh(driver_tree_file)
        return driver_tree_file

    async def create_driver_tree_data_frame(
        self,
        *,
        driver_tree_file: DriverTreeFile,
        column_name: str = "テスト列",
        data: dict[str, Any] | None = None,
    ) -> DriverTreeDataFrame:
        """ドライバーツリーデータフレームを作成。

        Args:
            driver_tree_file: ドライバーツリーファイル
            column_name: 列名
            data: データ

        Returns:
            DriverTreeDataFrame: 作成されたドライバーツリーデータフレーム
        """
        data_frame = DriverTreeDataFrame(
            driver_tree_file_id=driver_tree_file.id,
            column_name=column_name,
            data=data or {},
        )
        self.db.add(data_frame)
        await self.db.flush()
        await self.db.refresh(data_frame)
        return data_frame
