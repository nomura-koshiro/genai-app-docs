"""プロジェクトCRUDサービス。

このモジュールは、プロジェクトのCRUD操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import Project, ProjectMember, ProjectRole
from app.repositories import (
    AnalysisSessionRepository,
    DriverTreeRepository,
    ProjectFileRepository,
    ProjectMemberRepository,
)
from app.schemas import ProjectCreate, ProjectStatsResponse, ProjectUpdate
from app.services.project.project.base import ProjectServiceBase

logger = get_logger(__name__)


class ProjectCrudService(ProjectServiceBase):
    """プロジェクトのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

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
            project_data: プロジェクト作成用のPydanticスキーマ
            creator_id: プロジェクト作成者のユーザーID

        Returns:
            Project: 作成されたプロジェクトモデルインスタンス

        Raises:
            ValidationError: プロジェクトコードが既に使用されている場合
            Exception: データベース操作で予期しないエラーが発生した場合
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
                role=ProjectRole.PROJECT_MANAGER,
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
    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """プロジェクトIDでプロジェクト情報を取得します。

        Args:
            project_id: 取得対象のプロジェクトUUID

        Returns:
            Project | None: 該当するプロジェクトモデルインスタンス、存在しない場合はNone
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
            code: 検索対象のプロジェクトコード

        Returns:
            Project: 該当するプロジェクトモデルインスタンス

        Raises:
            NotFoundError: 指定されたコードのプロジェクトが存在しない場合
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
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            list[Project]: プロジェクトモデルインスタンスのリスト
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
            user_id: ユーザーのUUID
            skip: スキップするレコード数
            limit: 返す最大レコード数
            is_active: アクティブフラグフィルタ

        Returns:
            list[Project]: ユーザーが所属するプロジェクトのリスト
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
    async def update_project(
        self,
        project_id: uuid.UUID,
        update_data: ProjectUpdate,
        user_id: uuid.UUID,
    ) -> Project:
        """プロジェクト情報を更新します。

        このメソッドは、OWNER/ADMINロールを持つユーザーのみが実行できます。

        Args:
            project_id: 更新するプロジェクトのUUID
            update_data: 更新データ
            user_id: 更新を実行するユーザーのUUID

        Returns:
            Project: 更新されたプロジェクトモデルインスタンス

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: ユーザーがOWNER/ADMINロールを持っていない場合
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
            required_roles=[ProjectRole.PROJECT_MANAGER],
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
            project_id: 削除するプロジェクトのUUID
            user_id: 削除を実行するユーザーのUUID

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: ユーザーがOWNERロールを持っていない場合
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

        # 権限チェック: プロジェクト作成者のみが削除可能
        if project.created_by != user_id:
            logger.warning(
                "プロジェクト削除権限がありません（作成者のみ削除可能）",
                project_id=str(project_id),
                user_id=str(user_id),
                created_by=str(project.created_by),
            )
            raise AuthorizationError(
                "プロジェクトを削除する権限がありません（作成者のみ削除可能）",
                details={"project_id": str(project_id)},
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

    async def check_user_access(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """ユーザーがプロジェクトにアクセスできるかチェックします。

        Args:
            project_id: プロジェクトのUUID
            user_id: ユーザーのUUID

        Returns:
            bool: アクセス可能な場合はTrue、不可能な場合はFalse
        """
        result = await self.db.execute(
            select(ProjectMember).where(ProjectMember.project_id == project_id).where(ProjectMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()

        return member is not None

    @measure_performance
    async def get_project_stats(
        self,
        project_id: uuid.UUID,
    ) -> ProjectStatsResponse:
        """プロジェクトの統計情報を取得します。

        Args:
            project_id: プロジェクトのUUID

        Returns:
            ProjectStatsResponse: プロジェクト統計情報
                - member_count: メンバー数
                - file_count: ファイル数
                - session_count: 分析セッション数
                - tree_count: ドライバーツリー数
        """
        logger.debug(
            "プロジェクト統計情報を取得中",
            project_id=str(project_id),
            action="get_project_stats",
        )

        # 各リポジトリのカウントを取得
        member_repo = ProjectMemberRepository(self.db)
        file_repo = ProjectFileRepository(self.db)
        session_repo = AnalysisSessionRepository(self.db)
        tree_repo = DriverTreeRepository(self.db)

        member_count = await member_repo.count_by_project(project_id)
        file_count = await file_repo.count_by_project(project_id)
        session_count = await session_repo.count_by_project(project_id)
        tree_count = await tree_repo.count_by_project(project_id)

        logger.debug(
            "プロジェクト統計情報を取得しました",
            project_id=str(project_id),
            member_count=member_count,
            file_count=file_count,
            session_count=session_count,
            tree_count=tree_count,
        )

        return ProjectStatsResponse(
            member_count=member_count,
            file_count=file_count,
            session_count=session_count,
            tree_count=tree_count,
        )
