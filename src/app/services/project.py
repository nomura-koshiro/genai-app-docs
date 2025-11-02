"""プロジェクト管理のビジネスロジックサービス。

このモジュールは、プロジェクトの作成、取得、更新、削除などのビジネスロジックを提供します。
すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

主な機能:
    - プロジェクトの作成（作成者を自動的にOWNERとして追加）
    - プロジェクトコードの重複チェック
    - ユーザーの権限チェック（OWNER/ADMIN/MEMBER/VIEWER）
    - プロジェクトメンバーシップの管理
    - プロジェクト削除時の関連データ確認

使用例:
    >>> from app.services.project import ProjectService
    >>> from app.schemas.project import ProjectCreate
    >>>
    >>> async with get_db() as db:
    ...     project_service = ProjectService(db)
    ...     project_data = ProjectCreate(
    ...         name="AI Development Project",
    ...         code="AI-001",
    ...         description="Project for AI model development"
    ...     )
    ...     project = await project_service.create_project(project_data, creator_id)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = get_logger(__name__)


class ProjectService:
    """プロジェクト管理のビジネスロジックを提供するサービスクラス。

    このサービスは、プロジェクトの作成、取得、更新、削除などの操作を提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        repository: ProjectRepositoryインスタンス（データベースアクセス用）

    Example:
        >>> async with get_db() as db:
        ...     project_service = ProjectService(db)
        ...     project = await project_service.get_project(project_id)
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.repository = ProjectRepository(db)

    @measure_performance
    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """プロジェクトIDでプロジェクト情報を取得します。

        Args:
            project_id (uuid.UUID): 取得対象のプロジェクトUUID

        Returns:
            Project | None: 該当するプロジェクトモデルインスタンス、存在しない場合はNone
                - すべてのプロジェクト属性を含む
                - リレーションシップは遅延ロードされます

        Example:
            >>> project = await project_service.get_project(project_id)
            >>> if project:
            ...     print(f"Found project: {project.name}")
            ... else:
            ...     print("Project not found")
            Found project: AI Project
        """
        logger.debug(
            "プロジェクトIDでプロジェクトを取得中",
            project_id=str(project_id),
            action="get_project",
        )

        project = await self.repository.get(project_id)
        if not project:
            logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
            return None

        logger.debug(
            "プロジェクトを正常に取得しました",
            project_id=str(project.id),
            name=project.name,
        )
        return project

    @measure_performance
    async def get_project_by_code(self, code: str) -> Project:
        """プロジェクトコードでプロジェクト情報を取得します。

        Args:
            code (str): 検索対象のプロジェクトコード

        Returns:
            Project: 該当するプロジェクトモデルインスタンス

        Raises:
            NotFoundError: 指定されたコードのプロジェクトが存在しない場合

        Example:
            >>> project = await project_service.get_project_by_code("AI-001")
            >>> print(f"Found project: {project.name}")
            Found project: AI Project
        """
        logger.debug(
            "プロジェクトコードでプロジェクトを取得中",
            code=code,
            action="get_project_by_code",
        )

        project = await self.repository.get_by_code(code)
        if not project:
            logger.warning("プロジェクトが見つかりません", code=code)
            raise NotFoundError(
                "プロジェクトが見つかりません",
                details={"code": code},
            )

        logger.debug(
            "プロジェクトを正常に取得しました",
            project_id=str(project.id),
            code=project.code,
        )
        return project

    @measure_performance
    async def list_projects(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """プロジェクトの一覧を取得します（管理者用）。

        Args:
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100

        Returns:
            list[Project]: プロジェクトモデルインスタンスのリスト

        Example:
            >>> projects = await project_service.list_projects(skip=0, limit=10)
            >>> print(f"Found {len(projects)} projects")
            Found 10 projects
        """
        logger.debug(
            "プロジェクト一覧を取得中",
            skip=skip,
            limit=limit,
            action="list_projects",
        )

        projects = await self.repository.get_multi(skip=skip, limit=limit)

        logger.debug(
            "プロジェクト一覧を正常に取得しました",
            count=len(projects),
            skip=skip,
            limit=limit,
        )

        return projects

    @measure_performance
    async def list_user_projects(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[Project]:
        """特定ユーザーが所属するプロジェクトの一覧を取得します。

        Args:
            user_id (uuid.UUID): ユーザーのUUID
            skip (int): スキップするレコード数
                デフォルト: 0
            limit (int): 返す最大レコード数
                デフォルト: 100
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのプロジェクト
                True: アクティブなプロジェクトのみ
                False: 非アクティブなプロジェクトのみ

        Returns:
            list[Project]: ユーザーが所属するプロジェクトのリスト

        Example:
            >>> projects = await project_service.list_user_projects(
            ...     user_id=user_id,
            ...     skip=0,
            ...     limit=10,
            ...     is_active=True
            ... )
            >>> print(f"User's projects: {len(projects)}")
            User's projects: 5
        """
        logger.debug(
            "ユーザーのプロジェクト一覧を取得中",
            user_id=str(user_id),
            skip=skip,
            limit=limit,
            is_active=is_active,
            action="list_user_projects",
        )

        projects = await self.repository.list_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )

        logger.debug(
            "ユーザーのプロジェクト一覧を正常に取得しました",
            user_id=str(user_id),
            count=len(projects),
        )

        return projects

    @measure_performance
    @transactional
    async def create_project(
        self,
        project_data: ProjectCreate,
        creator_id: uuid.UUID,
    ) -> Project:
        """新しいプロジェクトを作成します。

        このメソッドは以下の処理を実行します：
        1. プロジェクトコードの重複チェック
        2. プロジェクトレコードの作成
        3. 作成者を自動的にOWNERとしてプロジェクトメンバーに追加
        4. 作成イベントのロギング

        Args:
            project_data (ProjectCreate): プロジェクト作成用のPydanticスキーマ
                - name: プロジェクト名
                - code: プロジェクトコード（一意制約）
                - description: プロジェクト説明（オプション）
            creator_id (uuid.UUID): プロジェクト作成者のユーザーID
                - 自動的にOWNERとして追加されます

        Returns:
            Project: 作成されたプロジェクトモデルインスタンス
                - id: 自動生成されたUUID
                - created_by: 作成者のユーザーID
                - is_active: True（デフォルト）
                - created_at, updated_at: 自動生成されたタイムスタンプ

        Raises:
            ValidationError: 以下の場合に発生
                - プロジェクトコードが既に使用されている
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> project_data = ProjectCreate(
            ...     name="AI Project",
            ...     code="AI-001",
            ...     description="AI development project"
            ... )
            >>> project = await project_service.create_project(project_data, user_id)
            >>> print(f"Created project: {project.code}")
            Created project: AI-001

        Note:
            - 作成者は自動的にOWNERロールとしてプロジェクトメンバーに追加されます
            - プロジェクトコードは一意である必要があります
            - すべての操作は構造化ログに記録されます
        """
        logger.info(
            "プロジェクトを作成中",
            name=project_data.name,
            code=project_data.code,
            creator_id=str(creator_id),
            action="project_creation",
        )

        try:
            # プロジェクトコードの重複チェック
            existing_project = await self.repository.get_by_code(project_data.code)
            if existing_project:
                logger.warning(
                    "プロジェクト作成失敗: コードが既に存在します",
                    code=project_data.code,
                    existing_project_id=str(existing_project.id),
                )
                raise ValidationError(
                    "このプロジェクトコードは既に使用されています",
                    details={"code": project_data.code},
                )

            # プロジェクトを作成
            project = await self.repository.create(
                name=project_data.name,
                code=project_data.code,
                description=project_data.description,
                created_by=creator_id,
                is_active=True,
            )

            # 作成者をOWNERとして追加
            project_member = ProjectMember(
                project_id=project.id,
                user_id=creator_id,
                role=ProjectRole.OWNER,
                added_by=creator_id,
            )
            self.db.add(project_member)

            await self.db.flush()
            await self.db.refresh(project)

            logger.info(
                "プロジェクトを正常に作成しました",
                project_id=str(project.id),
                name=project.name,
                code=project.code,
                creator_id=str(creator_id),
            )

            return project

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "プロジェクト作成中に予期しないエラーが発生しました",
                name=project_data.name,
                code=project_data.code,
                creator_id=str(creator_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    @transactional
    async def update_project(
        self,
        project_id: uuid.UUID,
        update_data: ProjectUpdate,
        user_id: uuid.UUID,
    ) -> Project:
        """プロジェクト情報を更新します。

        このメソッドは、OWNER/ADMINロールを持つユーザーのみが実行できます。

        Args:
            project_id (uuid.UUID): 更新するプロジェクトのUUID
            update_data (ProjectUpdate): 更新データ
                - name: プロジェクト名（オプション）
                - description: プロジェクト説明（オプション）
                - is_active: アクティブフラグ（オプション）
            user_id (uuid.UUID): 更新を実行するユーザーのUUID

        Returns:
            Project: 更新されたプロジェクトモデルインスタンス

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: ユーザーがOWNER/ADMINロールを持っていない場合

        Example:
            >>> update_data = ProjectUpdate(
            ...     name="Updated Project Name",
            ...     description="Updated description"
            ... )
            >>> project = await project_service.update_project(
            ...     project_id=project_id,
            ...     update_data=update_data,
            ...     user_id=user_id
            ... )
            >>> print(f"Updated: {project.name}")
            Updated: Updated Project Name

        Note:
            - プロジェクトコード（code）は更新できません
            - OWNER/ADMINロールのみが更新を実行できます
        """
        logger.info(
            "プロジェクト情報更新",
            project_id=str(project_id),
            user_id=str(user_id),
            update_fields=update_data.model_dump(exclude_unset=True),
            action="update_project",
        )

        # プロジェクトを取得
        project = await self.repository.get(project_id)
        if not project:
            logger.warning(
                "更新対象のプロジェクトが見つかりません",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise NotFoundError(
                "プロジェクトが見つかりません",
                details={"project_id": str(project_id)},
            )

        # 権限チェック: OWNER/ADMINのみが更新可能
        await self._check_user_role(
            project_id=project_id,
            user_id=user_id,
            required_roles=[ProjectRole.OWNER, ProjectRole.ADMIN],
        )

        # プロジェクト情報を更新
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            logger.info(
                "更新フィールドが指定されていません",
                project_id=str(project_id),
            )
            return project

        updated_project = await self.repository.update(project, **update_dict)

        logger.info(
            "プロジェクト情報を更新しました",
            project_id=str(project.id),
            user_id=str(user_id),
            updated_fields=list(update_dict.keys()),
        )

        return updated_project

    @measure_performance
    @transactional
    async def delete_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトを削除します。

        このメソッドは、OWNERロールを持つユーザーのみが実行できます。
        CASCADE設定により、関連する ProjectMember と ProjectFile も自動削除されます。

        Args:
            project_id (uuid.UUID): 削除するプロジェクトのUUID
            user_id (uuid.UUID): 削除を実行するユーザーのUUID

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: ユーザーがOWNERロールを持っていない場合

        Example:
            >>> await project_service.delete_project(
            ...     project_id=project_id,
            ...     user_id=user_id
            ... )
            >>> print("Project deleted")

        Note:
            - OWNERロールのみが削除を実行できます
            - CASCADE設定により、関連するメンバーとファイルも削除されます
            - この操作は取り消せません（物理削除）
            - 関連する物理ファイルも削除されます（エラー時はログ記録して処理継続）
        """
        logger.info(
            "プロジェクト削除",
            project_id=str(project_id),
            user_id=str(user_id),
            action="delete_project",
        )

        # プロジェクトを取得
        project = await self.repository.get(project_id)
        if not project:
            logger.warning(
                "削除対象のプロジェクトが見つかりません",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise NotFoundError(
                "プロジェクトが見つかりません",
                details={"project_id": str(project_id)},
            )

        # 権限チェック: OWNERのみが削除可能
        await self._check_user_role(
            project_id=project_id,
            user_id=user_id,
            required_roles=[ProjectRole.OWNER],
        )

        # 関連する物理ファイルを削除（エラーログは記録するが処理は継続）
        await self._delete_physical_files(project)

        # プロジェクトを削除（CASCADEでDBからもファイルメタデータ削除）
        await self.repository.delete(project_id)

        logger.info(
            "プロジェクトを削除しました",
            project_id=str(project_id),
            user_id=str(user_id),
            project_code=project.code,
        )

    async def _check_user_role(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        required_roles: list[ProjectRole],
    ) -> ProjectMember:
        """ユーザーのプロジェクトロールをチェックします。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID
            required_roles (list[ProjectRole]): 必要なロールのリスト

        Returns:
            ProjectMember: ユーザーのメンバーシップ情報

        Raises:
            AuthorizationError: ユーザーが必要なロールを持っていない場合

        Note:
            - 内部ヘルパーメソッド（外部からは呼び出されません）
        """
        from sqlalchemy import select

        # ユーザーのメンバーシップを取得
        result = await self.db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()

        if not member:
            logger.warning(
                "ユーザーはプロジェクトのメンバーではありません",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise AuthorizationError(
                "このプロジェクトへのアクセス権限がありません",
                details={
                    "project_id": str(project_id),
                    "user_id": str(user_id),
                },
            )

        if member.role not in required_roles:
            logger.warning(
                "ユーザーは必要なロールを持っていません",
                project_id=str(project_id),
                user_id=str(user_id),
                current_role=member.role.value,
                required_roles=[role.value for role in required_roles],
            )
            raise AuthorizationError(
                "この操作を実行する権限がありません",
                details={
                    "current_role": member.role.value,
                    "required_roles": [role.value for role in required_roles],
                },
            )

        return member

    async def _delete_physical_files(self, project) -> None:
        """プロジェクトに関連する物理ファイルを削除します。

        Args:
            project: プロジェクトモデルインスタンス

        Note:
            - ファイル削除失敗時もエラーログを記録して処理を継続します
            - データベースからの削除は別途CASCADEで実行されます
        """
        from pathlib import Path

        from sqlalchemy import select

        from app.models.project_file import ProjectFile

        # プロジェクトに関連するファイルを取得（リレーションシップを明示的にロード）
        result = await self.db.execute(
            select(ProjectFile).where(ProjectFile.project_id == project.id)
        )
        project_files = result.scalars().all()

        if not project_files:
            logger.debug(
                "削除対象のファイルがありません",
                project_id=str(project.id),
            )
            return

        logger.info(
            "物理ファイル削除開始",
            project_id=str(project.id),
            file_count=len(project_files),
        )

        deleted_count = 0
        failed_count = 0

        for project_file in project_files:
            try:
                filepath = Path(project_file.file_path)
                if filepath.exists():
                    filepath.unlink()
                    deleted_count += 1
                    logger.debug(
                        "物理ファイル削除成功",
                        file_id=str(project_file.id),
                        file_path=str(filepath),
                    )
                else:
                    logger.warning(
                        "物理ファイルが存在しません（スキップ）",
                        file_id=str(project_file.id),
                        file_path=str(filepath),
                    )
            except Exception as e:
                failed_count += 1
                logger.error(
                    "物理ファイル削除エラー（処理継続）",
                    file_id=str(project_file.id),
                    file_path=project_file.file_path,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )

        logger.info(
            "物理ファイル削除完了",
            project_id=str(project.id),
            deleted_count=deleted_count,
            failed_count=failed_count,
        )

    async def check_user_access(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """ユーザーがプロジェクトにアクセスできるかチェックします。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Returns:
            bool: アクセス可能な場合はTrue、不可能な場合はFalse

        Example:
            >>> has_access = await project_service.check_user_access(
            ...     project_id=project_id,
            ...     user_id=user_id
            ... )
            >>> if has_access:
            ...     print("User can access this project")
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()

        return member is not None
