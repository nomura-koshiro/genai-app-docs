"""分析セッション管理サービス。

このモジュールは、分析セッションのCRUD操作と結果取得を提供します。

主な機能:
    - 分析セッションの作成・取得・更新
    - プロジェクト配下のセッション一覧取得
    - セッション結果の詳細取得（ステップ・ファイル含む）

使用例:
    >>> from app.services.analysis.session import AnalysisSessionService
    >>> from app.schemas.analysis.session import AnalysisSessionCreate
    >>>
    >>> async with get_db() as db:
    ...     session_service = AnalysisSessionService(db)
    ...     session_data = AnalysisSessionCreate(
    ...         project_id=project_id,
    ...         policy="市場拡大",
    ...         issue="新規参入"
    ...     )
    ...     session = await session_service.create_session(
    ...         session_data=session_data,
    ...         creator_id=user_id
    ...     )
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.analysis import AnalysisSession
from app.repositories.analysis import AnalysisFileRepository, AnalysisSessionRepository, AnalysisStepRepository
from app.schemas import (
    AnalysisFileMetadata,
    AnalysisFileResponse,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisStepResponse,
    ValidationConfig,
)

logger = get_logger(__name__)


class AnalysisSessionService:
    """分析セッション管理サービス。

    このサービスは、データ分析セッションのCRUD操作を提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        session_repository: AnalysisSessionRepositoryインスタンス
        step_repository: AnalysisStepRepositoryインスタンス
        file_repository: AnalysisFileRepositoryインスタンス

    Example:
        >>> async with get_db() as db:
        ...     session_service = AnalysisSessionService(db)
        ...     session = await session_service.get_session(session_id)
    """

    def __init__(self, db: AsyncSession):
        """分析セッションサービスを初期化します。

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
            >>> session = await session_service.create_session(
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
            # ValidationConfigスキーマを使用してバリデーション設定を作成
            validation_config_obj = ValidationConfig(
                policy=session_data.policy,
                issue=session_data.issue,
            )

            # 初期スナップショットの作成（空のステップ配列）
            initial_snapshot: list[dict[str, Any]] = []

            # セッションを作成
            session = await self.session_repository.create(
                project_id=session_data.project_id,
                created_by=creator_id,
                validation_config=validation_config_obj.model_dump(),
                chat_history=[],
                snapshot_history=[initial_snapshot],  # list[list[dict]] - 空のステップリストを1つ含む
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
            >>> session = await session_service.get_session(session_id)
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
            >>> session = await session_service.get_session_with_details(session_id)
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
            >>> sessions = await session_service.list_project_sessions(
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
            >>> result = await session_service.get_session_result(session_id)
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
                file_metadata=AnalysisFileMetadata.model_validate(file.file_metadata) if file.file_metadata else None,
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

        return AnalysisSessionDetailResponse.model_validate(
            {
                "id": session.id,
                "project_id": session.project_id,
                "created_by": session.created_by,
                "session_name": session.session_name,
                "validation_config": session.validation_config,
                "steps": steps,
                "files": files,
                "chat_history": session.chat_history or [],
                "snapshot_history": session.snapshot_history,
                "is_active": session.is_active,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            }
        )
