"""プロジェクトモデル用のデータアクセスリポジトリ。

このモジュールは、Projectモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、プロジェクト固有のクエリメソッド（コード検索、
ユーザーのプロジェクト一覧取得など）を追加しています。

主な機能:
    - プロジェクトコードによる検索（一意性検証に使用）
    - ユーザーが所属するプロジェクト一覧の取得
    - アクティブなプロジェクトの取得
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.project.project import ProjectRepository
    >>>
    >>> async with get_db() as db:
    ...     project_repo = ProjectRepository(db)
    ...     project = await project_repo.get_by_code("PROJ-001")
    ...     if project:
    ...         print(f"Found project: {project.name}")
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Project, ProjectMember
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ProjectRepository(BaseRepository[Project, uuid.UUID]):
    """Projectモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    プロジェクト管理に特化したクエリメソッドを提供します。

    プロジェクト検索機能:
        - get_by_code(): プロジェクトコードによる検索（重複チェックで使用）
        - list_by_user(): ユーザーが所属するプロジェクト一覧
        - get_active_projects(): アクティブなプロジェクトのみを取得

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるプロジェクト取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規プロジェクト作成
        - update(): プロジェクト情報更新
        - delete(): プロジェクト削除
        - count(): プロジェクト数カウント

    Example:
        >>> async with get_db() as db:
        ...     project_repo = ProjectRepository(db)
        ...
        ...     # コードでプロジェクトを検索
        ...     project = await project_repo.get_by_code("PROJ-001")
        ...
        ...     # ユーザーが所属するプロジェクト一覧
        ...     user_projects = await project_repo.list_by_user(user_id, limit=50)
        ...
        ...     # 新規プロジェクト作成
        ...     new_project = await project_repo.create(
        ...         name="New Project",
        ...         code="PROJ-002",
        ...         description="Project description",
        ...         created_by=user_id
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - プロジェクト削除時、CASCADE設定により関連データ（members, files）も削除されます
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトリポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
                - DIコンテナから自動的に注入されます
                - トランザクションスコープはリクエスト単位で管理されます

        Note:
            - 親クラス（BaseRepository）の__init__を呼び出し、
              Projectモデルとセッションを設定します
            - このコンストラクタは通常、FastAPIの依存性注入システムにより
              自動的に呼び出されます
        """
        super().__init__(Project, db)

    async def get(self, id: uuid.UUID) -> Project | None:
        """UUIDによってプロジェクトを取得します。

        BaseRepositoryのget()メソッドをオーバーライドして、
        UUID型のIDに対応します。

        Args:
            id (uuid.UUID): プロジェクトのUUID

        Returns:
            Project | None: 該当するプロジェクトインスタンス、見つからない場合はNone
                - すべてのプロジェクト属性を含む
                - リレーションシップは遅延ロードされます

        Example:
            >>> project = await project_repo.get(project_id)
            >>> if project:
            ...     print(f"Found: {project.name}")
            ... else:
            ...     print("Project not found")
            Found: AI Project
        """
        return await self.db.get(self.model, id)

    async def get_by_code(self, code: str) -> Project | None:
        """プロジェクトコードによりプロジェクトを検索します。

        このメソッドは、プロジェクト作成時の重複チェックや、
        コードによるプロジェクト検索に使用されます。プロジェクトコードは
        データベースでUNIQUE制約が設定されているため、最大1件のみが返されます。

        クエリの最適化:
            - Project.codeにインデックスが設定されているため高速です
            - scalar_one_or_none()により、0件または1件のみを保証

        Args:
            code (str): 検索対象のプロジェクトコード
                - 大文字小文字を区別します
                - 例: "PROJ-001", "AI-2024"

        Returns:
            Project | None: 該当するプロジェクトインスタンス、見つからない場合はNone
                - Project: コードに一致するプロジェクトモデル
                - None: 該当するプロジェクトが存在しない

        Example:
            >>> project = await project_repo.get_by_code("PROJ-001")
            >>> if project:
            ...     print(f"Found project: {project.name}")
            ... else:
            ...     print("Code is available")
            Found project: AI Development Project

        Note:
            - プロジェクトコードはUNIQUE制約により重複しません
            - 大文字小文字を区別するため、"PROJ-001"と"proj-001"は別のコードです
            - インデックスが設定されているため、検索は高速です
        """
        result = await self.db.execute(select(Project).where(Project.code == code))
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[Project]:
        """特定ユーザーが所属するプロジェクトの一覧を取得します。

        このメソッドは、ProjectMemberテーブルを介して、
        指定されたユーザーがメンバーとして所属するプロジェクトのみをフィルタリングします。
        ユーザーのダッシュボードでのプロジェクト一覧表示に使用されます。

        クエリの最適化:
            - joinによりProjectMemberテーブルと結合
            - project_membersテーブルのuser_idにインデックスが設定されているため高速

        Args:
            user_id (uuid.UUID): ユーザーのUUID
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのプロジェクト
                True: アクティブなプロジェクトのみ
                False: 非アクティブなプロジェクトのみ

        Returns:
            list[Project]: プロジェクトのリスト
                - ユーザーがメンバーとして所属するプロジェクトのみ
                - created_at降順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> # ユーザーのアクティブプロジェクト一覧
            >>> projects = await project_repo.list_by_user(
            ...     user_id=user_id,
            ...     skip=0,
            ...     limit=10,
            ...     is_active=True
            ... )
            >>> print(f"User's projects: {len(projects)}")
            User's projects: 5

        Note:
            - ユーザーがメンバーでないプロジェクトは含まれません
            - プロジェクトロール（OWNER/ADMIN/MEMBER/VIEWER）に関係なくすべて取得
            - ロールでのフィルタリングが必要な場合は別途実装が必要です
        """
        query = select(Project).join(ProjectMember, Project.id == ProjectMember.project_id).where(ProjectMember.user_id == user_id)

        # アクティブフラグでフィルタ
        if is_active is not None:
            query = query.where(Project.is_active == is_active)

        query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_projects(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """アクティブなプロジェクトの一覧を取得します。

        このメソッドは、is_active=Trueのプロジェクトのみをフィルタリングして取得します。
        管理画面でのプロジェクト一覧表示や、アクティブプロジェクトの統計取得に使用されます。

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100

        Returns:
            list[Project]: アクティブプロジェクトのリスト
                - is_active=Trueのプロジェクトのみ
                - created_at降順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> active_projects = await project_repo.get_active_projects(skip=0, limit=10)
            >>> print(f"Active projects: {len(active_projects)}")
            Active projects: 8
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            is_active=True,
            order_by="created_at",
        )

    async def delete(self, id: uuid.UUID) -> bool:
        """プロジェクトを削除します。

        BaseRepositoryのdelete()メソッドをオーバーライドして、
        UUID型のIDに対応します。

        CASCADE削除の注意:
            - データベースのCASCADE制約により、関連レコード（members, files）も削除されます
            - プロジェクト削除前に、メンバーやファイルの存在確認を行うことを推奨します

        Args:
            id (uuid.UUID): 削除するプロジェクトのUUID

        Returns:
            bool: 削除が成功した場合はTrue、レコードが見つからない場合はFalse

        Example:
            >>> success = await project_repo.delete(project_id)
            >>> if success:
            ...     await db.commit()
            ...     print("Project deleted")
            ... else:
            ...     print("Project not found")
        """
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False

    async def count_by_user(
        self,
        user_id: uuid.UUID,
        is_active: bool | None = None,
    ) -> int:
        """特定ユーザーが所属するプロジェクトの総数を取得します。

        ページネーションのtotal値として使用されます。

        Args:
            user_id (uuid.UUID): ユーザーのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのプロジェクト
                True: アクティブなプロジェクトのみ
                False: 非アクティブなプロジェクトのみ

        Returns:
            int: 条件に一致するプロジェクトの総数

        Example:
            >>> total = await project_repo.count_by_user(user_id, is_active=True)
            >>> print(f"User's active projects: {total}")
            User's active projects: 15
        """
        from sqlalchemy import func

        query = (
            select(func.count())
            .select_from(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
        )

        if is_active is not None:
            query = query.where(Project.is_active == is_active)

        result = await self.db.execute(query)
        return result.scalar_one()
