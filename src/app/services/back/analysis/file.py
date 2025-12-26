"""分析ファイル管理サービス。

このモジュールは、データファイルのアップロード、検証、メタデータ管理などの
ファイル関連のビジネスロジックを提供します。

主な機能:
    - データファイルのアップロード・検証
    - ファイルメタデータの管理
    - ファイル一覧の取得
"""

import base64
import uuid
from io import BytesIO

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import AnalysisFile
from app.repositories import AnalysisFileRepository, AnalysisSessionRepository
from app.schemas import (
    AnalysisFileMetadata,
    AnalysisFileUploadRequest,
    AnalysisFileUploadResponse,
)
from app.services.analysis.agent.storage import AnalysisStorageService

logger = get_logger(__name__)


class AnalysisFileService:
    """分析ファイル管理サービスクラス。

    このサービスは、データファイルのアップロード、検証、メタデータ管理などの
    ファイル関連の操作を提供します。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        session_repository: AnalysisSessionRepositoryインスタンス
        file_repository: AnalysisFileRepositoryインスタンス
        storage_service: AnalysisStorageServiceインスタンス
    """

    def __init__(self, db: AsyncSession):
        """分析ファイルサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.session_repository = AnalysisSessionRepository(db)
        self.file_repository = AnalysisFileRepository(db)
        self.storage_service = AnalysisStorageService()

    @measure_performance
    @transactional
    @async_timeout(seconds=300)  # 5分タイムアウト
    async def upload_data_file(
        self,
        session_id: uuid.UUID,
        file_request: AnalysisFileUploadRequest,
        user_id: uuid.UUID,
    ) -> AnalysisFileUploadResponse:
        """データファイルをアップロードし、メタデータを保存します。

        このメソッドは以下の処理を実行します：
        1. ファイルのデコード（Base64）
        2. ファイル形式の検証（CSV, XLSX, XLS）
        3. DataFrameへの変換
        4. データ構造の検証
        5. ストレージへのアップロード（CSV形式）
        6. メタデータのデータベース保存
        7. 軸候補の抽出

        Args:
            session_id (uuid.UUID): セッションのUUID
            file_request (AnalysisFileUploadRequest): ファイルアップロードリクエスト
                - file_name: ファイル名（例: "sales_data.xlsx"）
                - file_data: Base64エンコードされたファイルデータ
                - table_name: テーブル名（例: "売上データ"）
            user_id (uuid.UUID): アップロードユーザーのUUID

        Returns:
            AnalysisFileUploadResponse: アップロード結果
                - file_id: 作成されたファイルのUUID
                - file_name: ファイル名
                - table_name: テーブル名
                - storage_path: ストレージパス
                - file_size: ファイルサイズ（バイト）
                - table_axis: 軸候補のリスト
                - row_count: 行数
                - column_count: 列数

        Raises:
            ValidationError: 以下の場合に発生
                - セッションが存在しない
                - ファイル形式が未対応
                - データ構造が不正
                - ファイルサイズが制限超過
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> import base64
            >>> with open("sales_data.xlsx", "rb") as f:
            ...     file_data = base64.b64encode(f.read()).decode()
            >>> file_request = AnalysisFileUploadRequest(
            ...     file_name="sales_data.xlsx",
            ...     file_data=file_data,
            ...     table_name="売上データ"
            ... )
            >>> result = await file_service.upload_data_file(
            ...     session_id=session_id,
            ...     file_request=file_request,
            ...     user_id=user_id
            ... )
            >>> print(f"Uploaded: {result.file_name}, Rows: {result.row_count}")
            Uploaded: sales_data.xlsx, Rows: 1000

        Note:
            - 対応フォーマット: CSV, XLSX, XLS
            - ストレージにはCSV形式（UTF-8）で保存されます
            - 軸候補は「値」列を除く全カラムから抽出されます
            - @async_timeoutデコレータにより5分でタイムアウトします
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "データファイルをアップロード中",
            session_id=str(session_id),
            file_name=file_request.file_name,
            table_name=file_request.table_name,
            user_id=str(user_id),
            action="upload_data_file",
        )

        try:
            # セッションの存在確認
            session = await self.session_repository.get(session_id)
            if not session:
                logger.warning(
                    "セッションが見つかりません",
                    session_id=str(session_id),
                )
                raise NotFoundError(
                    "セッションが見つかりません",
                    details={"session_id": str(session_id)},
                )

            # Base64デコード
            file_bytes = base64.b64decode(file_request.data)
            file_size = len(file_bytes)

            logger.debug(
                "ファイルをデコードしました",
                session_id=str(session_id),
                file_size=file_size,
            )

            # ファイル形式の検証とDataFrame変換
            file_extension = file_request.file_name.lower().split(".")[-1]
            df = None

            if file_extension == "csv":
                df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8")
            elif file_extension in ["xlsx", "xls"]:
                df = pd.read_excel(BytesIO(file_bytes))
            else:
                logger.warning(
                    "未対応のファイル形式",
                    file_name=file_request.file_name,
                    extension=file_extension,
                )
                raise ValidationError(
                    "未対応のファイル形式です。CSV、XLSX、XLSのみサポートされています。",
                    details={"file_name": file_request.file_name},
                )

            # データ構造の検証
            if df.empty:
                raise ValidationError(
                    "ファイルにデータが含まれていません",
                    details={"file_name": file_request.file_name},
                )

            logger.info(
                "DataFrameに変換しました",
                session_id=str(session_id),
                rows=len(df),
                columns=len(df.columns),
            )

            # 軸候補の抽出（「値」列以外の全カラム）
            table_axis = [col for col in df.columns if col != "値"]

            # ストレージパスの生成
            filename_base = file_request.file_name.rsplit(".", 1)[0]
            storage_path = await self.storage_service.save_dataframe(
                session_id=session_id,
                filename=filename_base,
                df=df,
                prefix="files",
            )

            logger.info(
                "ストレージにファイルを保存しました",
                session_id=str(session_id),
                storage_path=storage_path,
            )

            # メタデータの保存
            content_type = "text/csv" if file_extension == "csv" else "application/vnd.ms-excel"

            # AnalysisFileMetadataスキーマを使用してメタデータを作成
            file_metadata = AnalysisFileMetadata(
                row_count=len(df),
                column_count=len(df.columns),
                columns=list(df.columns),
            )

            analysis_file = await self.file_repository.create(
                session_id=session_id,
                uploaded_by=user_id,
                file_name=file_request.file_name,
                table_name=file_request.table_name,
                storage_path=storage_path,
                file_size=file_size,
                content_type=content_type,
                table_axis=table_axis,
                metadata=file_metadata.model_dump(),
                is_active=True,
            )

            logger.info(
                "データファイルを正常にアップロードしました",
                session_id=str(session_id),
                file_id=str(analysis_file.id),
                file_name=file_request.file_name,
                storage_path=storage_path,
                file_size=file_size,
                rows=len(df),
            )

            return AnalysisFileUploadResponse(
                id=analysis_file.id,
                session_id=analysis_file.session_id,
                file_name=analysis_file.file_name,
                table_name=analysis_file.table_name,
                storage_path=analysis_file.storage_path,
                file_size=analysis_file.file_size,
                content_type=analysis_file.content_type,
                table_axis=analysis_file.table_axis,
                uploaded_by=analysis_file.uploaded_by,
                created_at=analysis_file.created_at,
                message="ファイルが正常にアップロードされました",
            )

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "データファイルアップロード中に予期しないエラーが発生しました",
                session_id=str(session_id),
                file_name=file_request.file_name,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def list_session_files(self, session_id: uuid.UUID, is_active: bool | None = None) -> list[AnalysisFile]:
        """セッションのファイル一覧を取得します。

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのファイル
                True: アクティブなファイルのみ
                False: 非アクティブなファイルのみ

        Returns:
            list[AnalysisFile]: ファイルのリスト（created_at昇順）

        Example:
            >>> files = await file_service.list_session_files(session_id)
            >>> for file in files:
            ...     print(f"File: {file.file_name} ({file.table_name})")
            File: sales_data.xlsx (売上データ)
        """
        logger.debug(
            "セッションファイル一覧を取得中",
            session_id=str(session_id),
            is_active=is_active,
            action="list_session_files",
        )

        files = await self.file_repository.list_by_session(
            session_id=session_id,
            is_active=is_active,
        )

        logger.debug(
            "セッションファイル一覧を正常に取得しました",
            session_id=str(session_id),
            count=len(files),
        )

        return files
