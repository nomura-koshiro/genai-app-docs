"""分析ファイルモデル用のデータアクセスリポジトリ。

このモジュールは、AnalysisFileモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、分析ファイル固有のクエリメソッド（セッション別検索、
ファイル名検索、ストレージパス取得など）を追加しています。

主な機能:
    - セッション別のファイル一覧取得
    - ファイル名による検索
    - ストレージパスによる検索
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.analysis_file import AnalysisFileRepository
    >>>
    >>> async with get_db() as db:
    ...     file_repo = AnalysisFileRepository(db)
    ...     files = await file_repo.list_by_session(session_id)
    ...     for file in files:
    ...         print(f"File: {file.file_name} ({file.file_size} bytes)")
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analysis_file import AnalysisFile
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisFileRepository(BaseRepository[AnalysisFile, uuid.UUID]):
    """AnalysisFileモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    分析ファイル管理に特化したクエリメソッドを提供します。

    分析ファイル検索機能:
        - list_by_session(): セッション別のファイル一覧
        - get_by_storage_path(): ストレージパスによる検索
        - count_by_session(): セッション別のファイル数カウント

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるファイル取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規ファイル作成
        - update(): ファイル情報更新
        - delete(): ファイル削除
        - count(): ファイル数カウント

    Example:
        >>> async with get_db() as db:
        ...     file_repo = AnalysisFileRepository(db)
        ...
        ...     # セッションのファイル一覧
        ...     files = await file_repo.list_by_session(session_id)
        ...     for file in files:
        ...         print(f"{file.file_name}: {file.file_size} bytes")
        ...
        ...     # 新規ファイル作成
        ...     new_file = await file_repo.create(
        ...         session_id=session_id,
        ...         uploaded_by=user_id,
        ...         file_name="sales_data.xlsx",
        ...         table_name="売上データ",
        ...         storage_path="analysis/{session_id}/sales_data.csv",
        ...         file_size=1024000,
        ...         content_type="application/vnd.ms-excel",
        ...         table_axis=["地域", "商品"]
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - ファイル削除時、実際のストレージファイルは削除されません（メタデータのみ削除）
    """

    def __init__(self, db: AsyncSession):
        """分析ファイルリポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
                - DIコンテナから自動的に注入されます
                - トランザクションスコープはリクエスト単位で管理されます

        Note:
            - 親クラス（BaseRepository）の__init__を呼び出し、
              AnalysisFileモデルとセッションを設定します
        """
        super().__init__(AnalysisFile, db)

    async def get(self, id: uuid.UUID) -> AnalysisFile | None:
        """UUIDによって分析ファイルを取得します。

        Args:
            id (uuid.UUID): ファイルのUUID

        Returns:
            AnalysisFile | None: 該当するファイルインスタンス、見つからない場合はNone

        Example:
            >>> file = await file_repo.get(file_id)
            >>> if file:
            ...     print(f"File: {file.file_name} ({file.table_name})")
            File: sales_data.xlsx (売上データ)
        """
        return await self.db.get(self.model, id)

    async def list_by_session(
        self,
        session_id: uuid.UUID,
        is_active: bool | None = None,
    ) -> list[AnalysisFile]:
        """特定セッションに属する分析ファイルの一覧を取得します。

        このメソッドは、指定されたセッションに紐づくファイルのみを
        フィルタリングします。アップロード順（created_at昇順）でソートされます。

        クエリの最適化:
            - session_idにインデックスが設定されているため高速
            - created_at昇順でソート（アップロード順）

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのファイル
                True: アクティブなファイルのみ
                False: 非アクティブなファイルのみ

        Returns:
            list[AnalysisFile]: ファイルのリスト（created_at昇順）
                - 指定されたセッションに属するファイルのみ
                - created_at昇順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> files = await file_repo.list_by_session(session_id)
            >>> for file in files:
            ...     print(f"- {file.file_name} ({file.table_name})")
            ...     print(f"  Size: {file.file_size} bytes")
            ...     print(f"  Axis: {file.table_axis}")
            - sales_data.xlsx (売上データ)
              Size: 1024000 bytes
              Axis: ['地域', '商品']

        Note:
            - created_at昇順でソート（アップロード順）
            - table_axisは軸候補のリスト（Noneの場合もあり）
        """
        query = select(AnalysisFile).where(AnalysisFile.session_id == session_id)

        if is_active is not None:
            query = query.where(AnalysisFile.is_active == is_active)

        query = query.order_by(AnalysisFile.created_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_storage_path(self, storage_path: str) -> AnalysisFile | None:
        """ストレージパスによりファイルを検索します。

        このメソッドは、Blob Storageのパスからファイルメタデータを検索します。
        ファイルダウンロード時などに使用されます。

        Args:
            storage_path (str): ストレージパス
                - 例: "analysis/{session_id}/sales_data.csv"

        Returns:
            AnalysisFile | None: 該当するファイルインスタンス、見つからない場合はNone

        Example:
            >>> file = await file_repo.get_by_storage_path(
            ...     "analysis/abc-123/sales_data.csv"
            ... )
            >>> if file:
            ...     print(f"Found: {file.file_name}")
            ... else:
            ...     print("File not found in database")
            Found: sales_data.xlsx

        Note:
            - storage_pathは完全一致で検索されます
            - ファイルが削除された場合（is_active=False）でも検索されます
        """
        result = await self.db.execute(select(AnalysisFile).where(AnalysisFile.storage_path == storage_path))
        return result.scalar_one_or_none()

    async def count_by_session(self, session_id: uuid.UUID, is_active: bool | None = None) -> int:
        """セッション別のファイル数をカウントします。

        このメソッドは、特定のセッションに属するファイル数を効率的にカウントします。

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのファイル
                True: アクティブなファイルのみ
                False: 非アクティブなファイルのみ

        Returns:
            int: 条件に一致するファイル数

        Example:
            >>> total_files = await file_repo.count_by_session(session_id)
            >>> print(f"Total files: {total_files}")
            Total files: 3
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(AnalysisFile).where(AnalysisFile.session_id == session_id)

        if is_active is not None:
            query = query.where(AnalysisFile.is_active == is_active)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_total_size_by_session(self, session_id: uuid.UUID) -> int:
        """セッション内の全ファイルの合計サイズを取得します。

        このメソッドは、セッションにアップロードされた全ファイルの
        合計サイズ（バイト）を計算します。ストレージ使用量の監視に使用されます。

        Args:
            session_id (uuid.UUID): セッションのUUID

        Returns:
            int: ファイルの合計サイズ（バイト）
                - ファイルが存在しない場合は0を返します

        Example:
            >>> total_size = await file_repo.get_total_size_by_session(session_id)
            >>> print(f"Total storage: {total_size / 1024 / 1024:.2f} MB")
            Total storage: 10.5 MB

        Note:
            - is_active=Trueのファイルのみカウントされます
            - ファイルサイズはバイト単位で返されます
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.sum(AnalysisFile.file_size)).where(
                AnalysisFile.session_id == session_id,
                AnalysisFile.is_active == True,  # noqa: E712
            )
        )
        total_size = result.scalar_one_or_none()
        return total_size if total_size is not None else 0
