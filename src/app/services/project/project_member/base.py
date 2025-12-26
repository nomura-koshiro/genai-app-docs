"""プロジェクトメンバーサービス共通ベース。

このモジュールは、プロジェクトメンバーサービスの共通機能を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import Project, ProjectMember, ProjectRole, UserAccount
from app.repositories import ProjectMemberRepository, ProjectRepository, UserAccountRepository

logger = get_logger(__name__)


class ProjectMemberServiceBase:
    """プロジェクトメンバーサービスの共通ベースクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバーサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = ProjectMemberRepository(db)
        self.project_repository = ProjectRepository(db)
        self.user_repository = UserAccountRepository(db)

        logger.info("プロジェクトメンバーサービスを初期化しました")

    async def _check_project_exists(self, project_id: uuid.UUID) -> Project:
        """プロジェクトの存在を確認します。

        Args:
            project_id: プロジェクトのUUID

        Returns:
            Project: プロジェクトインスタンス

        Raises:
            NotFoundError: プロジェクトが見つからない場合
        """
        logger.debug("プロジェクトの存在確認中", project_id=str(project_id))

        project = await self.project_repository.get(project_id)
        if not project:
            logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
            raise NotFoundError(
                "プロジェクトが見つかりません",
                details={"project_id": str(project_id)},
            )

        logger.debug(
            "プロジェクトの存在を確認しました",
            project_id=str(project_id),
            project_name=project.name,
        )

        return project

    async def _check_user_exists(self, user_id: uuid.UUID) -> UserAccount:
        """ユーザーの存在を確認します。

        Args:
            user_id: ユーザーのUUID

        Returns:
            UserAccount: ユーザーインスタンス

        Raises:
            NotFoundError: ユーザーが見つからない場合
        """
        logger.debug("ユーザーの存在確認中", user_id=str(user_id))

        user = await self.user_repository.get(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError(
                "ユーザーが見つかりません",
                details={"user_id": str(user_id)},
            )

        logger.debug("ユーザーの存在を確認しました", user_id=str(user_id), email=user.email)

        return user

    async def _get_requester_role(self, project_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectRole:
        """リクエスタのロールを取得します。

        Args:
            project_id: プロジェクトのUUID
            requester_id: リクエスタのユーザーUUID

        Returns:
            ProjectRole: リクエスタのロール

        Raises:
            AuthorizationError: リクエスタがプロジェクトのメンバーでない場合
        """
        logger.debug(
            "リクエスタのロール取得中",
            project_id=str(project_id),
            requester_id=str(requester_id),
        )

        role = await self.repository.get_user_role(project_id, requester_id)
        if role is None:
            logger.warning(
                "リクエスタはプロジェクトのメンバーではありません",
                project_id=str(project_id),
                requester_id=str(requester_id),
            )
            raise AuthorizationError(
                "このプロジェクトへのアクセス権限がありません",
                details={"project_id": str(project_id)},
            )

        logger.debug(
            "リクエスタのロールを取得しました",
            project_id=str(project_id),
            requester_id=str(requester_id),
            role=role.value,
        )

        return role

    async def _check_can_manage_members(self, requester_role: ProjectRole) -> None:
        """メンバー管理権限をチェックします。

        Args:
            requester_role: リクエスタのロール

        Raises:
            AuthorizationError: リクエスタがPROJECT_MANAGER/PROJECT_MODERATORでない場合
        """
        logger.debug("メンバー管理権限をチェック中", role=requester_role.value)

        if requester_role not in [
            ProjectRole.PROJECT_MANAGER,
            ProjectRole.PROJECT_MODERATOR,
        ]:
            logger.warning(
                "メンバー管理の権限がありません",
                role=requester_role.value,
            )
            raise AuthorizationError(
                "メンバーを管理する権限がありません",
                details={
                    "required_role": "project_manager or project_moderator",
                    "current_role": requester_role.value,
                },
            )

        logger.debug("メンバー管理権限を確認しました", role=requester_role.value)

    async def _check_moderator_limitations(
        self,
        requester_role: ProjectRole,
        target_role: ProjectRole,
        operation: str,
    ) -> None:
        """PROJECT_MODERATORの制限をチェックします。

        PROJECT_MODERATORは以下の操作が制限されています：
        - PROJECT_MANAGERロールの追加
        - PROJECT_MANAGERロールへの更新
        - PROJECT_MANAGERロールの削除

        Args:
            requester_role: リクエスタのロール
            target_role: 対象ユーザーのロール
            operation: 操作タイプ（"add", "update", "delete"）

        Raises:
            AuthorizationError: PROJECT_MODERATORがPROJECT_MANAGERに対する操作を実行しようとした場合
        """
        logger.debug(
            "PROJECT_MODERATOR制限をチェック中",
            requester_role=requester_role.value,
            target_role=target_role.value,
            operation=operation,
        )

        # PROJECT_MANAGERの場合はチェック不要
        if requester_role == ProjectRole.PROJECT_MANAGER:
            logger.debug("PROJECT_MANAGERのため制限チェックをスキップ")
            return

        # PROJECT_MODERATORの場合、PROJECT_MANAGERロールへの操作を禁止
        if requester_role == ProjectRole.PROJECT_MODERATOR and target_role == ProjectRole.PROJECT_MANAGER:
            logger.warning(
                "PROJECT_MODERATORはPROJECT_MANAGERロールを操作できません",
                operation=operation,
                target_role=target_role.value,
            )

            operation_messages = {
                "add": "PROJECT_MANAGERロールの追加にはPROJECT_MANAGER権限が必要です",
                "update": "PROJECT_MANAGERロールへの更新にはPROJECT_MANAGER権限が必要です",
                "delete": "PROJECT_MANAGERロールの削除にはPROJECT_MANAGER権限が必要です",
            }

            raise AuthorizationError(
                operation_messages.get(operation, "PROJECT_MANAGERロールへの操作にはPROJECT_MANAGER権限が必要です"),
                details={
                    "required_role": "project_manager",
                    "current_role": requester_role.value,
                },
            )

        logger.debug("PROJECT_MODERATOR制限チェック完了")

    async def _check_last_manager_protection(self, project_id: uuid.UUID, member: ProjectMember) -> None:
        """最後のPROJECT_MANAGERの保護チェックを実行します。

        プロジェクトには最低1人のPROJECT_MANAGERが必要です。
        最後のPROJECT_MANAGERのロール変更や削除を防ぎます。

        Args:
            project_id: プロジェクトのUUID
            member: 対象メンバー

        Raises:
            ValidationError: 対象メンバーが最後のPROJECT_MANAGERの場合
        """
        logger.debug(
            "最後のPROJECT_MANAGERチェック中",
            project_id=str(project_id),
            member_id=str(member.id),
            current_role=member.role.value,
        )

        # PROJECT_MANAGER以外の場合はチェック不要
        if member.role != ProjectRole.PROJECT_MANAGER:
            logger.debug("PROJECT_MANAGERではないためチェックをスキップ")
            return

        # PROJECT_MANAGERの人数をカウント
        manager_count = await self.repository.count_by_role(project_id, ProjectRole.PROJECT_MANAGER)

        if manager_count <= 1:
            logger.warning(
                "最後のPROJECT_MANAGERのため操作できません",
                project_id=str(project_id),
                manager_count=manager_count,
            )
            raise ValidationError(
                "プロジェクトには最低1人のPROJECT_MANAGERが必要です",
                details={
                    "project_id": str(project_id),
                    "current_manager_count": manager_count,
                },
            )

        logger.debug(
            "最後のPROJECT_MANAGERチェック完了",
            manager_count=manager_count,
        )
