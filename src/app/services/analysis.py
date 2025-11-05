"""分析機能のビジネスロジックサービス。

このモジュールは、データ分析セッションの作成・管理、ファイルアップロード、
分析ステップの実行、AIエージェントとのチャット、結果の取得などの
ビジネスロジックを提供します。

主な機能:
    - 分析セッションの作成・取得・更新・削除
    - データファイルのアップロード・検証
    - 分析ステップの作成・実行・管理
    - AIエージェントとのチャットインターフェース
    - 分析結果の取得・スナップショット管理

使用例:
    >>> from app.services.analysis import AnalysisService
    >>> from app.schemas.analysis_session import AnalysisSessionCreate
    >>>
    >>> async with get_db() as db:
    ...     analysis_service = AnalysisService(db)
    ...     session_data = AnalysisSessionCreate(
    ...         project_id=project_id,
    ...         policy="市場拡大",
    ...         issue="新規参入"
    ...     )
    ...     session = await analysis_service.create_session(
    ...         session_data=session_data,
    ...         creator_id=user_id
    ...     )
"""

import uuid
from datetime import UTC, datetime
from io import BytesIO

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.analysis_file import AnalysisFile
from app.models.analysis_session import AnalysisSession
from app.models.analysis_step import AnalysisStep
from app.repositories.analysis_file import AnalysisFileRepository
from app.repositories.analysis_session import AnalysisSessionRepository
from app.repositories.analysis_step import AnalysisStepRepository
from app.schemas.analysis_session import (
    AnalysisFileUploadRequest,
    AnalysisFileUploadResponse,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisStepCreate,
    AnalysisStepResponse,
    ChatRequest,
    ChatResponse,
    DummyDataResponse,
    ValidationConfigResponse,
)
from app.services.analysis_storage import AnalysisStorageService

logger = get_logger(__name__)


class AnalysisService:
    """分析機能のビジネスロジックを提供するサービスクラス。

    このサービスは、データ分析に関する全ての操作を提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        session_repository: AnalysisSessionRepositoryインスタンス
        step_repository: AnalysisStepRepositoryインスタンス
        file_repository: AnalysisFileRepositoryインスタンス
        storage_service: AnalysisStorageServiceインスタンス

    Example:
        >>> async with get_db() as db:
        ...     analysis_service = AnalysisService(db)
        ...     session = await analysis_service.get_session(session_id)
    """

    def __init__(self, db: AsyncSession):
        """分析サービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.session_repository = AnalysisSessionRepository(db)
        self.step_repository = AnalysisStepRepository(db)
        self.file_repository = AnalysisFileRepository(db)
        self.storage_service = AnalysisStorageService()

    @measure_performance
    @transactional
    async def create_session(
        self,
        session_data: AnalysisSessionCreate,
        creator_id: uuid.UUID,
    ) -> AnalysisSession:
        """新しい分析セッションを作成します。

        このメソッドは以下の処理を実行します：
        1. validation_config（施策・課題）の設定
        2. セッションレコードの作成
        3. 初期スナップショット（snapshot_id=0）の作成
        4. 空のチャット履歴の初期化
        5. 作成イベントのロギング

        Args:
            session_data (AnalysisSessionCreate): セッション作成用のPydanticスキーマ
                - project_id: プロジェクトID
                - policy: 施策名（例: "市場拡大"）
                - issue: 課題名（例: "新規参入"）
            creator_id (uuid.UUID): セッション作成者のユーザーID

        Returns:
            AnalysisSession: 作成されたセッションモデルインスタンス
                - id: 自動生成されたUUID
                - created_by: 作成者のユーザーID
                - validation_config: 施策・課題の設定
                - chat_history: 空のリスト
                - snapshot_history: 初期スナップショット
                - is_active: True（デフォルト）
                - created_at, updated_at: 自動生成されたタイムスタンプ

        Raises:
            ValidationError: 以下の場合に発生
                - プロジェクトが存在しない
                - validation_configの形式が不正
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> session_data = AnalysisSessionCreate(
            ...     project_id=uuid.UUID("12345678-1234-1234-1234-123456789abc"),
            ...     policy="市場拡大",
            ...     issue="新規参入"
            ... )
            >>> session = await analysis_service.create_session(
            ...     session_data=session_data,
            ...     creator_id=user_id
            ... )
            >>> print(f"Created session: {session.id}")
            Created session: 12345678-1234-1234-1234-123456789abc

        Note:
            - validation_configは {"policy": "...", "issue": "..."} 形式で保存されます
            - 初期スナップショットはsnapshot_id=0で作成されます
            - すべての操作は構造化ログに記録されます
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "分析セッションを作成中",
            project_id=str(session_data.project_id),
            creator_id=str(creator_id),
            policy=session_data.policy,
            issue=session_data.issue,
            action="create_analysis_session",
        )

        try:
            # validation_configの構築
            validation_config = {
                "policy": session_data.policy,
                "issue": session_data.issue,
            }

            # 初期スナップショットの作成
            initial_snapshot = {
                "snapshot_id": 0,
                "timestamp": datetime.now(UTC).isoformat(),
                "description": "初期状態",
                "steps": [],
                "files": [],
            }

            # セッションを作成
            session = await self.session_repository.create(
                project_id=session_data.project_id,
                created_by=creator_id,
                validation_config=validation_config,
                chat_history=[],
                snapshot_history=[initial_snapshot],
                session_name=None,  # 後で設定可能
                is_active=True,
            )

            logger.info(
                "分析セッションを正常に作成しました",
                session_id=str(session.id),
                project_id=str(session.project_id),
                creator_id=str(creator_id),
                policy=session_data.policy,
                issue=session_data.issue,
            )

            return session

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "分析セッション作成中に予期しないエラーが発生しました",
                project_id=str(session_data.project_id),
                creator_id=str(creator_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_session(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """セッションIDで分析セッション情報を取得します。

        Args:
            session_id (uuid.UUID): 取得対象のセッションUUID

        Returns:
            AnalysisSession | None: 該当するセッションモデルインスタンス、存在しない場合はNone
                - すべてのセッション属性を含む
                - リレーションシップ（steps, files）は遅延ロードされます

        Example:
            >>> session = await analysis_service.get_session(session_id)
            >>> if session:
            ...     print(f"Found session: {session.id}")
            ... else:
            ...     print("Session not found")
            Found session: 12345678-1234-1234-1234-123456789abc
        """
        logger.debug(
            "分析セッションを取得中",
            session_id=str(session_id),
            action="get_analysis_session",
        )

        session = await self.session_repository.get(session_id)
        if not session:
            logger.warning("分析セッションが見つかりません", session_id=str(session_id))
            return None

        logger.debug(
            "分析セッションを正常に取得しました",
            session_id=str(session.id),
            project_id=str(session.project_id),
        )
        return session

    @measure_performance
    async def get_session_with_details(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """セッションをステップとファイルと共に取得します（N+1クエリ対策）。

        このメソッドは、selectinloadを使用してstepsとfilesリレーションシップを
        事前にロードするため、N+1クエリ問題を回避します。

        Args:
            session_id (uuid.UUID): セッションのUUID

        Returns:
            AnalysisSession | None: セッションインスタンス（steps、filesを含む）
                - None: セッションが存在しない場合

        Example:
            >>> session = await analysis_service.get_session_with_details(session_id)
            >>> if session:
            ...     print(f"Steps: {len(session.steps)}")
            ...     print(f"Files: {len(session.files)}")
            Steps: 5
            Files: 2

        Note:
            - steps は step_order 順にソートされます
            - 大量のステップ/ファイルがある場合、メモリ使用量に注意
        """
        logger.debug(
            "分析セッション詳細を取得中",
            session_id=str(session_id),
            action="get_session_with_details",
        )

        session = await self.session_repository.get_with_relations(session_id)
        if not session:
            logger.warning("分析セッションが見つかりません", session_id=str(session_id))
            return None

        logger.debug(
            "分析セッション詳細を正常に取得しました",
            session_id=str(session.id),
            steps_count=len(session.steps),
            files_count=len(session.files),
        )
        return session

    @measure_performance
    async def list_project_sessions(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[AnalysisSession]:
        """プロジェクトに属する分析セッションの一覧を取得します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのセッション
                True: アクティブなセッションのみ
                False: 非アクティブなセッションのみ

        Returns:
            list[AnalysisSession]: セッションのリスト（created_at降順）

        Example:
            >>> sessions = await analysis_service.list_project_sessions(
            ...     project_id=project_id,
            ...     skip=0,
            ...     limit=10,
            ...     is_active=True
            ... )
            >>> print(f"Active sessions: {len(sessions)}")
            Active sessions: 5
        """
        logger.debug(
            "プロジェクトの分析セッション一覧を取得中",
            project_id=str(project_id),
            skip=skip,
            limit=limit,
            is_active=is_active,
            action="list_project_sessions",
        )

        sessions = await self.session_repository.list_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )

        logger.debug(
            "プロジェクトの分析セッション一覧を正常に取得しました",
            project_id=str(project_id),
            count=len(sessions),
        )

        return sessions

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
            >>> result = await analysis_service.upload_data_file(
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
            import base64

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

            analysis_file = await self.file_repository.create(
                session_id=session_id,
                uploaded_by=user_id,
                file_name=file_request.file_name,
                table_name=file_request.table_name,
                storage_path=storage_path,
                file_size=file_size,
                content_type=content_type,
                table_axis=table_axis,
                metadata={
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                },
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
    @transactional
    async def create_step(
        self,
        session_id: uuid.UUID,
        step_data: AnalysisStepCreate,
    ) -> AnalysisStep:
        """新しい分析ステップを作成します。

        このメソッドは以下の処理を実行します：
        1. セッションの存在確認
        2. 次のステップ順序番号の取得
        3. ステップレコードの作成
        4. 作成イベントのロギング

        Args:
            session_id (uuid.UUID): セッションのUUID
            step_data (AnalysisStepCreate): ステップ作成用のPydanticスキーマ
                - step_name: ステップ名（例: "売上フィルタリング"）
                - step_type: ステップタイプ（filter/aggregate/transform/summary）
                - data_source: データソース（original/step_0/step_1/...）
                - config: ステップ設定（JSONB）

        Returns:
            AnalysisStep: 作成されたステップモデルインスタンス
                - id: 自動生成されたUUID
                - step_order: 自動採番された順序番号
                - is_active: True（デフォルト）
                - created_at, updated_at: 自動生成されたタイムスタンプ

        Raises:
            NotFoundError: セッションが存在しない場合
            ValidationError: ステップ設定が不正な場合
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> step_data = AnalysisStepCreate(
            ...     step_name="売上フィルタリング",
            ...     step_type="filter",
            ...     data_source="original",
            ...     config={
            ...         "category_filter": {"地域": ["東京", "大阪"]}
            ...     }
            ... )
            >>> step = await analysis_service.create_step(
            ...     session_id=session_id,
            ...     step_data=step_data
            ... )
            >>> print(f"Created step: {step.step_name} (order: {step.step_order})")
            Created step: 売上フィルタリング (order: 0)

        Note:
            - step_orderは自動的に採番されます（0から開始）
            - すべての操作は構造化ログに記録されます
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "分析ステップを作成中",
            session_id=str(session_id),
            step_name=step_data.step_name,
            step_type=step_data.step_type,
            data_source=step_data.data_source,
            action="create_analysis_step",
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

            # 次のステップ順序番号を取得
            next_order = await self.step_repository.get_next_order(session_id)

            # ステップを作成
            step = await self.step_repository.create(
                session_id=session_id,
                step_name=step_data.step_name,
                step_type=step_data.step_type,
                step_order=next_order,
                data_source=step_data.data_source,
                config=step_data.config,
                result_data_path=None,
                result_chart=None,
                result_formula=None,
                is_active=True,
            )

            logger.info(
                "分析ステップを正常に作成しました",
                session_id=str(session_id),
                step_id=str(step.id),
                step_name=step.step_name,
                step_order=step.step_order,
            )

            return step

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "分析ステップ作成中に予期しないエラーが発生しました",
                session_id=str(session_id),
                step_name=step_data.step_name,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    @async_timeout(seconds=600)  # 10分タイムアウト
    async def execute_chat(
        self,
        session_id: uuid.UUID,
        chat_request: ChatRequest,
    ) -> ChatResponse:
        """AIエージェントとチャットを実行します（準備中）。

        このメソッドは、ユーザーのメッセージを受け取り、AIエージェントに処理を依頼します。
        Phase 3.1で完全実装予定です。

        Args:
            session_id (uuid.UUID): セッションのUUID
            chat_request (ChatRequest): チャットリクエスト
                - message: ユーザーメッセージ

        Returns:
            ChatResponse: チャットレスポンス
                - message: アシスタントの応答メッセージ
                - snapshot_id: スナップショットID

        Raises:
            NotFoundError: セッションが存在しない場合
            ValidationError: チャット処理でエラーが発生した場合

        Example:
            >>> chat_request = ChatRequest(
            ...     message="東京と大阪の売上を表示してください"
            ... )
            >>> response = await analysis_service.execute_chat(
            ...     session_id=session_id,
            ...     chat_request=chat_request
            ... )
            >>> print(f"Assistant: {response.message}")
            Assistant: 東京と大阪の売上データをフィルタリングしました

        Note:
            - Phase 3.1でAIエージェント統合予定
            - @async_timeoutデコレータにより10分でタイムアウトします
            - 現在はプレースホルダー実装です
        """
        logger.info(
            "チャット実行中",
            session_id=str(session_id),
            message_length=len(chat_request.message),
            action="execute_chat",
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

            # TODO: Phase 3.1でAIエージェント統合
            # 現在はプレースホルダー実装
            response_message = "AIエージェント機能は現在準備中です。Phase 3.1で実装予定です。"

            # チャット履歴を更新
            snapshot_id = len(session.chat_history) // 2  # 仮のスナップショットID
            chat_entry = {
                "role": "assistant",
                "message": response_message,
                "snapshot_id": snapshot_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            await self.session_repository.update_chat_history(session_id, chat_entry)

            logger.info(
                "チャット実行完了",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
            )

            return ChatResponse(
                message=response_message,
                snapshot_id=snapshot_id,
                steps_added=0,
                steps_modified=0,
                analysis_result=None,
            )

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "チャット実行中に予期しないエラーが発生しました",
                session_id=str(session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_session_result(self, session_id: uuid.UUID) -> AnalysisSessionDetailResponse:
        """分析セッションの結果を取得します。

        このメソッドは、セッションの詳細情報（ステップ、ファイル、チャット履歴）を
        すべて含む完全なレスポンスを返します。

        Args:
            session_id (uuid.UUID): セッションのUUID

        Returns:
            AnalysisSessionDetailResponse: セッション結果
                - session_id: セッションID
                - project_id: プロジェクトID
                - validation_config: 施策・課題設定
                - steps: ステップのリスト
                - files: ファイルのリスト
                - chat_history: チャット履歴
                - created_at: 作成日時
                - updated_at: 更新日時

        Raises:
            NotFoundError: セッションが存在しない場合

        Example:
            >>> result = await analysis_service.get_session_result(session_id)
            >>> print(f"Steps: {len(result.steps)}, Files: {len(result.files)}")
            Steps: 5, Files: 2

        Note:
            - N+1クエリを回避するため、selectinloadを使用します
            - ステップはstep_order順にソートされます
        """
        logger.debug(
            "セッション結果を取得中",
            session_id=str(session_id),
            action="get_session_result",
        )

        session = await self.session_repository.get_with_relations(session_id)
        if not session:
            logger.warning("セッションが見つかりません", session_id=str(session_id))
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        # ステップをAnalysisStepResponseに変換

        steps = [
            AnalysisStepResponse(
                id=step.id,
                session_id=step.session_id,
                step_name=step.step_name,
                step_type=step.step_type,
                step_order=step.step_order,
                data_source=step.data_source,
                config=step.config,
                result_data_path=step.result_data_path,
                result_chart=step.result_chart,
                result_formula=step.result_formula,
                is_active=step.is_active,
                created_at=step.created_at,
                updated_at=step.updated_at,
            )
            for step in session.steps
        ]

        # ファイルをAnalysisFileResponseに変換
        from app.schemas.analysis_session import AnalysisFileResponse

        files = [
            AnalysisFileResponse(
                id=file.id,
                session_id=file.session_id,
                uploaded_by=file.uploaded_by,
                file_name=file.file_name,
                table_name=file.table_name,
                storage_path=file.storage_path,
                file_size=file.file_size,
                content_type=file.content_type,
                table_axis=file.table_axis,
                file_metadata=file.file_metadata,
                is_active=file.is_active,
                created_at=file.created_at,
                updated_at=file.updated_at,
            )
            for file in session.files
        ]

        logger.debug(
            "セッション結果を正常に取得しました",
            session_id=str(session.id),
            steps_count=len(steps),
            files_count=len(files),
        )

        return AnalysisSessionDetailResponse(
            id=session.id,
            project_id=session.project_id,
            created_by=session.created_by,
            session_name=session.session_name,
            validation_config=session.validation_config,
            steps=steps,
            files=files,
            chat_history=session.chat_history or [],
            snapshot_history=session.snapshot_history or [],
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    @measure_performance
    async def list_session_steps(self, session_id: uuid.UUID, is_active: bool | None = None) -> list[AnalysisStep]:
        """セッションの分析ステップ一覧を取得します。

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのステップ
                True: アクティブなステップのみ
                False: 非アクティブなステップのみ

        Returns:
            list[AnalysisStep]: ステップのリスト（step_order昇順）

        Example:
            >>> steps = await analysis_service.list_session_steps(session_id)
            >>> for step in steps:
            ...     print(f"Step {step.step_order}: {step.step_name}")
            Step 0: 売上フィルタリング
            Step 1: 地域別集計
        """
        logger.debug(
            "セッションステップ一覧を取得中",
            session_id=str(session_id),
            is_active=is_active,
            action="list_session_steps",
        )

        steps = await self.step_repository.list_by_session(
            session_id=session_id,
            is_active=is_active,
        )

        logger.debug(
            "セッションステップ一覧を正常に取得しました",
            session_id=str(session_id),
            count=len(steps),
        )

        return steps

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
            >>> files = await analysis_service.list_session_files(session_id)
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

    @measure_performance
    @transactional
    async def delete_step(self, step_id: uuid.UUID) -> None:
        """分析ステップを削除します。

        Args:
            step_id (uuid.UUID): 削除するステップのUUID

        Raises:
            NotFoundError: ステップが存在しない場合

        Example:
            >>> await analysis_service.delete_step(step_id)
            >>> print("Step deleted")

        Note:
            - 論理削除ではなく物理削除されます
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "分析ステップを削除中",
            step_id=str(step_id),
            action="delete_step",
        )

        step = await self.step_repository.get(step_id)
        if not step:
            logger.warning("ステップが見つかりません", step_id=str(step_id))
            raise NotFoundError(
                "ステップが見つかりません",
                details={"step_id": str(step_id)},
            )

        await self.step_repository.delete(step_id)

        logger.info(
            "分析ステップを削除しました",
            step_id=str(step_id),
            step_name=step.step_name,
        )

    @measure_performance
    @async_timeout(10.0)
    async def get_validation_config(self) -> ValidationConfigResponse:
        """検証設定を取得します。

        このメソッドは、validation.ymlファイルから検証設定を読み込みます。

        Returns:
            ValidationConfigResponse: 検証設定
                - validation_config: 検証設定の全体

        Example:
            >>> config = await analysis_service.get_validation_config()
            >>> print(f"Policies: {config.validation_config.get('policies', [])}")
            Policies: ['市場拡大', '既存市場深耕', ...]

        Note:
            - 設定はapp/data/analysis/validation.ymlから読み込まれます
            - キャッシュは実装していません（必要に応じて追加）
        """
        logger.debug("検証設定を取得中", action="get_validation_config")

        try:
            from pathlib import Path

            import yaml

            config_path = Path(__file__).parent.parent / "data" / "analysis" / "validation.yml"

            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            logger.debug("検証設定を正常に取得しました")

            return ValidationConfigResponse(
                validation_config=config,
            )

        except Exception as e:
            logger.error(
                "検証設定の取得中にエラーが発生しました",
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                "検証設定の取得に失敗しました",
                details={"error": str(e)},
            ) from e

    @measure_performance
    @async_timeout(10.0)
    async def get_dummy_data(self, chart_type: str) -> DummyDataResponse:
        """ダミーチャートデータを取得します。

        このメソッドは、指定されたチャートタイプのダミーデータを返します。

        Args:
            chart_type (str): チャートタイプ
                - 例: "bar", "line", "pie", "scatter", など

        Returns:
            DummyDataResponse: ダミーデータレスポンス
                - formula: ダミー数式
                - input: ダミー入力データ
                - chart: ダミーチャート
                - hint: ヒント文章

        Raises:
            NotFoundError: 指定されたチャートタイプが存在しない場合
            ValidationError: ファイル読み込みエラー

        Example:
            >>> chart_data = await analysis_service.get_dummy_data("bar")
            >>> print(f"Hint: {chart_data.hint}")

        Note:
            - ダミーデータはapp/data/analysis/dummy/chart/配下から読み込まれます
        """
        logger.debug(
            "ダミーデータを取得中",
            chart_type=chart_type,
            action="get_dummy_data",
        )

        try:
            import json
            from pathlib import Path

            dummy_path = Path(__file__).parent.parent / "data" / "analysis" / "dummy" / "chart" / f"{chart_type}.json"

            if not dummy_path.exists():
                logger.warning(
                    "ダミーデータファイルが見つかりません",
                    chart_type=chart_type,
                    path=str(dummy_path),
                )
                raise NotFoundError(
                    "指定されたチャートタイプのダミーデータが存在しません",
                    details={"chart_type": chart_type},
                )

            with open(dummy_path, encoding="utf-8") as f:
                dummy_data = json.load(f)

            logger.debug(
                "ダミーデータを正常に取得しました",
                chart_type=chart_type,
            )

            return DummyDataResponse(
                formula=dummy_data.get("formula", []),
                input=dummy_data.get("input", []),
                chart=dummy_data.get("chart", []),
                hint=dummy_data.get("hint", ""),
            )

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ダミーデータの取得中にエラーが発生しました",
                chart_type=chart_type,
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                "ダミーデータの取得に失敗しました",
                details={"chart_type": chart_type, "error": str(e)},
            ) from e

    @measure_performance
    @transactional
    async def restore_snapshot(self, session_id: uuid.UUID, snapshot_id: int) -> AnalysisSession:
        """スナップショットから状態を復元します（準備中）。

        このメソッドは、指定されたスナップショットIDからセッションの状態を復元します。
        Phase 3.1で完全実装予定です。

        Args:
            session_id (uuid.UUID): セッションのUUID
            snapshot_id (int): スナップショットID

        Returns:
            AnalysisSession: 復元されたセッション

        Raises:
            NotFoundError: セッションまたはスナップショットが存在しない場合
            ValidationError: 復元処理でエラーが発生した場合

        Example:
            >>> session = await analysis_service.restore_snapshot(
            ...     session_id=session_id,
            ...     snapshot_id=2
            ... )
            >>> print(f"Restored to snapshot {snapshot_id}")

        Note:
            - Phase 3.1で実装予定
            - @transactionalデコレータにより自動コミットされます
            - 現在はプレースホルダー実装です
        """
        logger.info(
            "スナップショットから復元中",
            session_id=str(session_id),
            snapshot_id=snapshot_id,
            action="restore_snapshot",
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

            # TODO: Phase 3.1でスナップショット復元ロジック実装
            logger.warning(
                "スナップショット復元機能は現在準備中です",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
            )

            raise ValidationError(
                "スナップショット復元機能は現在準備中です。Phase 3.1で実装予定です。",
                details={"session_id": str(session_id), "snapshot_id": snapshot_id},
            )

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "スナップショット復元中に予期しないエラーが発生しました",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
                error=str(e),
                exc_info=True,
            )
            raise
