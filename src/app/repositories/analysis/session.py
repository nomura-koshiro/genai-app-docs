"""分析セッションモデル用のデータアクセスリポジトリ。

このモジュールは、AnalysisSessionモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、分析セッション固有のクエリメソッド（プロジェクト別検索、
ユーザー別検索、アクティブセッションの取得など）を追加しています。

主な機能:
    - プロジェクト別の分析セッション一覧取得
    - ユーザー別の分析セッション一覧取得
    - セッションの詳細取得（steps、filesを含む）
    - アクティブなセッションの取得
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.analysis import AnalysisSessionRepository
    >>>
    >>> async with get_db() as db:
    ...     session_repo = AnalysisSessionRepository(db)
    ...     sessions = await session_repo.list_by_project(project_id, limit=10)
    ...     for session in sessions:
    ...         print(f"Session: {session.session_name}")
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.analysis import AnalysisSession
from app.repositories.base import BaseRepository
from app.schemas.analysis import AnalysisChatMessage

logger = get_logger(__name__)


class AnalysisSessionRepository(BaseRepository[AnalysisSession, uuid.UUID]):
    """AnalysisSessionモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    分析セッション管理に特化したクエリメソッドを提供します。

    分析セッション検索機能:
        - list_by_project(): プロジェクト別のセッション一覧
        - list_by_user(): ユーザー別のセッション一覧
        - get_with_relations(): ステップとファイルを含む詳細取得
        - get_active_sessions(): アクティブなセッションのみを取得

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるセッション取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規セッション作成
        - update(): セッション情報更新
        - delete(): セッション削除
        - count(): セッション数カウント

    Example:
        >>> async with get_db() as db:
        ...     session_repo = AnalysisSessionRepository(db)
        ...
        ...     # プロジェクト別のセッション一覧
        ...     sessions = await session_repo.list_by_project(project_id, limit=20)
        ...
        ...     # 詳細情報を含むセッション取得
        ...     session = await session_repo.get_with_relations(session_id)
        ...     print(f"Steps: {len(session.steps)}, Files: {len(session.files)}")
        ...
        ...     # 新規セッション作成
        ...     new_session = await session_repo.create(
        ...         project_id=project_id,
        ...         created_by=user_id,
        ...         validation_config={"policy": "市場拡大", "issue": "新規参入"},
        ...         chat_history=[],
        ...         is_active=True
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - セッション削除時、CASCADE設定により関連データ（steps, files）も削除されます
    """

    def __init__(self, db: AsyncSession):
        """分析セッションリポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
                - DIコンテナから自動的に注入されます
                - トランザクションスコープはリクエスト単位で管理されます

        Note:
            - 親クラス（BaseRepository）の__init__を呼び出し、
              AnalysisSessionモデルとセッションを設定します
            - このコンストラクタは通常、FastAPIの依存性注入システムにより
              自動的に呼び出されます
        """
        super().__init__(AnalysisSession, db)

    async def get(self, id: uuid.UUID) -> AnalysisSession | None:
        """UUIDによって分析セッションを取得します。

        BaseRepositoryのget()メソッドをオーバーライドして、
        UUID型のIDに対応します。

        Args:
            id (uuid.UUID): セッションのUUID

        Returns:
            AnalysisSession | None: 該当するセッションインスタンス、見つからない場合はNone
                - すべてのセッション属性を含む
                - リレーションシップは遅延ロードされます

        Example:
            >>> session = await session_repo.get(session_id)
            >>> if session:
            ...     print(f"Found: {session.session_name}")
            ... else:
            ...     print("Session not found")
            Found: 2024年第1四半期分析
        """
        return await self.db.get(self.model, id)

    async def get_with_relations(self, id: uuid.UUID) -> AnalysisSession | None:
        """セッションをステップとファイルと共に取得します（N+1クエリ対策）。

        このメソッドは、selectinloadを使用してstepsとfilesリレーションシップを
        事前にロードするため、N+1クエリ問題を回避します。セッション詳細画面で
        使用されることを想定しています。

        パフォーマンス最適化:
            - selectinload でstepsとfilesを1クエリで事前ロード
            - 通常のget()と比較して2つの追加クエリのみ（N+1を回避）

        Args:
            id (uuid.UUID): セッションのUUID

        Returns:
            AnalysisSession | None: セッションインスタンス（steps、filesを含む）
                - None: セッションが存在しない場合

        Example:
            >>> session = await session_repo.get_with_relations(session_id)
            >>> if session:
            ...     print(f"Steps: {len(session.steps)}")
            ...     print(f"Files: {len(session.files)}")
            ...     # リレーションシップが事前ロード済み（追加クエリなし）
            ...     for step in session.steps:
            ...         print(f"  - {step.step_name}")
            Steps: 5
            Files: 2
              - 売上フィルタリング
              - データ集計

        Note:
            - steps は step_order 順にソートされます（モデル定義による）
            - 大量のステップ/ファイルがある場合、メモリ使用量に注意
        """
        result = await self.db.execute(
            select(AnalysisSession)
            .where(AnalysisSession.id == id)
            .options(
                selectinload(AnalysisSession.steps),
                selectinload(AnalysisSession.files),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[AnalysisSession]:
        """特定プロジェクトに属する分析セッションの一覧を取得します。

        このメソッドは、指定されたプロジェクトに紐づく分析セッションのみを
        フィルタリングします。プロジェクト管理画面でのセッション一覧表示に使用されます。

        クエリの最適化:
            - project_idにインデックスが設定されているため高速
            - created_at降順でソート（最新のセッションが先頭）

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
            list[AnalysisSession]: セッションのリスト
                - 指定されたプロジェクトに属するセッションのみ
                - created_at降順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> # プロジェクトのアクティブセッション一覧
            >>> sessions = await session_repo.list_by_project(
            ...     project_id=project_id,
            ...     skip=0,
            ...     limit=10,
            ...     is_active=True
            ... )
            >>> print(f"Active sessions: {len(sessions)}")
            Active sessions: 5

        Note:
            - created_at降順でソート（最新が先）
            - リレーションシップは遅延ロードされます
            - N+1クエリを避けるには list_by_project_with_relations() を使用
        """
        query = select(AnalysisSession).where(AnalysisSession.project_id == project_id)

        if is_active is not None:
            query = query.where(AnalysisSession.is_active == is_active)

        query = query.order_by(AnalysisSession.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[AnalysisSession]:
        """特定ユーザーが作成した分析セッションの一覧を取得します。

        このメソッドは、指定されたユーザーが作成したセッションのみを
        フィルタリングします。ユーザーのマイページでのセッション履歴表示に使用されます。

        Args:
            user_id (uuid.UUID): ユーザーのUUID
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのセッション
                True: アクティブなセッションのみ
                False: 非アクティブなセッションのみ

        Returns:
            list[AnalysisSession]: セッションのリスト
                - 指定されたユーザーが作成したセッションのみ
                - created_at降順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> # ユーザーの最近のセッション
            >>> recent_sessions = await session_repo.list_by_user(
            ...     user_id=user_id,
            ...     skip=0,
            ...     limit=5,
            ...     is_active=True
            ... )
            >>> for session in recent_sessions:
            ...     print(f"- {session.session_name or 'Unnamed'}")
            - 2024年第1四半期分析
            - 売上データ分析

        Note:
            - created_at降順でソート（最新が先）
            - created_byにインデックスが設定されているため高速
        """
        query = select(AnalysisSession).where(AnalysisSession.created_by == user_id)

        if is_active is not None:
            query = query.where(AnalysisSession.is_active == is_active)

        query = query.order_by(AnalysisSession.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_chat_history(self, session_id: uuid.UUID, chat_entry: AnalysisChatMessage) -> AnalysisSession | None:
        """セッションのチャット履歴に新しいエントリを追加します。

        このメソッドは、既存のchat_historyに新しいチャットエントリを追加します。
        JSONBカラムの更新を効率的に行うため、配列全体を更新します。

        Args:
            session_id (uuid.UUID): セッションのUUID
            chat_entry (AnalysisChatMessage): 追加するチャットエントリ
                - role (Literal["user", "assistant"]): メッセージの送信者
                - content (str): メッセージ内容
                - timestamp (str): タイムスタンプ（ISO 8601形式）

        Returns:
            AnalysisSession | None: 更新されたセッション、セッションが存在しない場合はNone

        Raises:
            ValueError: セッションが存在しない場合

        Example:
            >>> from datetime import datetime, UTC
            >>> from app.schemas.analysis import AnalysisChatMessage
            >>> chat_entry = AnalysisChatMessage(
            ...     role="user",
            ...     content="売上データを東京と大阪でフィルタリングしてください",
            ...     timestamp=datetime.now(UTC).isoformat()
            ... )
            >>> session = await session_repo.update_chat_history(session_id, chat_entry)
            >>> print(f"Chat history length: {len(session.chat_history)}")
            Chat history length: 3

        Note:
            - flush()のみ実行し、commit()は呼び出し側の責任
            - chat_historyはJSONB配列として保存されます
            - AnalysisChatMessageスキーマでバリデーション後、dictに変換してDB保存
        """
        session = await self.get(session_id)
        if not session:
            logger.warning("セッションが見つかりません", session_id=str(session_id))
            return None

        # chat_historyに新しいエントリを追加（Pydantic → dict）
        current_history = session.chat_history or []
        updated_history = current_history + [chat_entry.model_dump()]

        # セッションを更新
        session.chat_history = updated_history
        await self.db.flush()
        await self.db.refresh(session)

        logger.debug(
            "チャット履歴を更新しました",
            session_id=str(session_id),
            history_length=len(updated_history),
        )

        return session

    async def count_by_project(self, project_id: uuid.UUID, is_active: bool | None = None) -> int:
        """プロジェクト別のセッション数をカウントします。

        このメソッドは、特定のプロジェクトに属するセッション数を効率的にカウントします。
        ページネーションのtotal値として使用されます。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのセッション
                True: アクティブなセッションのみ
                False: 非アクティブなセッションのみ

        Returns:
            int: 条件に一致するセッション数

        Example:
            >>> total = await session_repo.count_by_project(project_id, is_active=True)
            >>> sessions = await session_repo.list_by_project(project_id, skip=0, limit=10)
            >>> print(f"Showing {len(sessions)} of {total} sessions")
            Showing 10 of 25 sessions
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(AnalysisSession).where(AnalysisSession.project_id == project_id)

        if is_active is not None:
            query = query.where(AnalysisSession.is_active == is_active)

        result = await self.db.execute(query)
        return result.scalar_one()
