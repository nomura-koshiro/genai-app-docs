"""ドライバーツリーファイルサービス。

このモジュールは、ドライバーツリーのファイル管理ビジネスロジックを提供します。

主な機能:
    - ファイルアップロード
    - アップロードファイル一覧取得
    - シート選択送信
    - データカラム設定送信
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.driver_tree import DriverTreeDataFrameRepository, DriverTreeFileRepository
from app.repositories.project import ProjectFileRepository
from app.services import storage as storage_module
from app.services.storage import StorageService

from .column_config import ColumnConfigMixin
from .file_operations import FileOperationsMixin
from .sheet_operations import SheetOperationsMixin


class DriverTreeFileService(FileOperationsMixin, SheetOperationsMixin, ColumnConfigMixin):
    """ドライバーツリーファイル管理のビジネスロジックを提供するサービスクラス。

    ファイルアップロード、シート選択、カラム設定を提供します。

    継承元:
        - FileOperationsMixin: ファイル操作（upload, delete, list）
        - SheetOperationsMixin: シート操作（select, delete, list_selected）
        - ColumnConfigMixin: カラム設定（update_column_config）

    Attributes:
        container: ストレージコンテナ名（全Mixin共通）
    """

    container = "driver_tree"

    def __init__(self, db: AsyncSession, storage: StorageService | None = None):
        """ドライバーツリーファイルサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
            storage: ストレージサービス（指定しない場合はデフォルトのストレージサービスを使用）
        """
        self.db = db
        self.file_repository = DriverTreeFileRepository(db)
        self.data_frame_repository = DriverTreeDataFrameRepository(db)
        self.project_file_repository = ProjectFileRepository(db)
        # モジュール経由でアクセスすることでテスト時のモックが効くようにする
        self.storage: StorageService = storage if storage is not None else storage_module.get_storage_service()
