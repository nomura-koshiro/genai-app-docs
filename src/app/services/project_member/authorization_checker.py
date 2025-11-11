"""プロジェクトメンバー操作の権限チェック専門サービス。

このモジュールは、プロジェクトメンバー操作における権限チェックロジックを集約し、
重複コードを削減します。

主な機能:
    - プロジェクト存在確認
    - ユーザー存在確認
    - リクエスタロール取得
    - メンバー管理権限チェック
    - PROJECT_MODERATOR制限チェック
    - 最後のPROJECT_MANAGER保護

使用例:
    >>> from app.services.project_member.authorization_checker import ProjectMemberAuthorizationChecker
    >>>
    >>> async with get_db() as db:
    ...     checker = ProjectMemberAuthorizationChecker(db)
    ...     await checker.check_project_exists(project_id)
    ...     role = await checker.get_requester_role(project_id, requester_id)
    ...     await checker.check_can_manage_members(role)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class ProjectMemberAuthorizationChecker:
    """プロジェクトメンバー操作の権限チェック専門クラス。

    このクラスは、プロジェクトメンバー操作における全ての権限チェックロジックを集約し、
    コードの重複を削減し、保守性を向上させます。

    Attributes:
        db (AsyncSession): データベースセッション
        project_repository (ProjectRepository): プロジェクトリポジトリ
        member_repository (ProjectMemberRepository): メンバーリポジトリ
        user_repository (UserRepository): ユーザーリポジトリ

    Example:
        >>> async with get_db() as db:
        ...     checker = ProjectMemberAuthorizationChecker(db)
        ...     await checker.check_project_exists(project_id)
    """

    def __init__(self, db: AsyncSession):
        """権限チェッカーを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
        """
        self.db = db
        self.project_repository = ProjectRepository(db)
        self.member_repository = ProjectMemberRepository(db)
        self.user_repository = UserRepository(db)

        logger.debug("権限チェッカーを初期化しました")

    async def check_project_exists(self, project_id: uuid.UUID) -> Project:
        """プロジェクトの存在を確認します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID

        Returns:
            Project: プロジェクトインスタンス

        Raises:
            NotFoundError: プロジェクトが見つからない場合

        Example:
            >>> project = await checker.check_project_exists(project_id)
            >>> print(f"Project found: {project.name}")

        Note:
            - プロジェクトが見つからない場合は NotFoundError を発生させます
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

    async def check_user_exists(self, user_id: uuid.UUID) -> User:
        """ユーザーの存在を確認します。

        Args:
            user_id (uuid.UUID): ユーザーのUUID

        Returns:
            User: ユーザーインスタンス

        Raises:
            NotFoundError: ユーザーが見つからない場合

        Example:
            >>> user = await checker.check_user_exists(user_id)
            >>> print(f"User found: {user.email}")

        Note:
            - ユーザーが見つからない場合は NotFoundError を発生させます
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

    async def get_requester_role(
        self, project_id: uuid.UUID, requester_id: uuid.UUID
    ) -> ProjectRole:
        """リクエスタのロールを取得します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            ProjectRole: リクエスタのロール

        Raises:
            AuthorizationError: リクエスタがプロジェクトのメンバーでない場合

        Example:
            >>> role = await checker.get_requester_role(project_id, requester_id)
            >>> print(f"Requester role: {role.value}")

        Note:
            - リクエスタがプロジェクトのメンバーでない場合は AuthorizationError を発生させます
        """
        logger.debug(
            "リクエスタのロール取得中",
            project_id=str(project_id),
            requester_id=str(requester_id),
        )

        role = await self.member_repository.get_user_role(project_id, requester_id)
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

    async def check_can_manage_members(self, requester_role: ProjectRole) -> None:
        """メンバー管理権限をチェックします。

        Args:
            requester_role (ProjectRole): リクエスタのロール

        Raises:
            AuthorizationError: リクエスタがPROJECT_MANAGER/PROJECT_MODERATORでない場合

        Example:
            >>> await checker.check_can_manage_members(requester_role)

        Note:
            - PROJECT_MANAGER または PROJECT_MODERATOR の権限が必要です
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

    async def check_moderator_limitations(
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
            requester_role (ProjectRole): リクエスタのロール
            target_role (ProjectRole): 対象ユーザーのロール
            operation (str): 操作タイプ（"add", "update", "delete"）

        Raises:
            AuthorizationError: PROJECT_MODERATORがPROJECT_MANAGERに対する操作を実行しようとした場合

        Example:
            >>> await checker.check_moderator_limitations(
            ...     ProjectRole.PROJECT_MODERATOR,
            ...     ProjectRole.PROJECT_MANAGER,
            ...     "add"
            ... )
            AuthorizationError: PROJECT_MANAGERロールの追加にはPROJECT_MANAGER権限が必要です

        Note:
            - PROJECT_MANAGERの場合はこのチェックをスキップします
            - PROJECT_MODERATORは VIEWER/MEMBER/PROJECT_MODERATOR のみ操作可能です
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
        if (
            requester_role == ProjectRole.PROJECT_MODERATOR
            and target_role == ProjectRole.PROJECT_MANAGER
        ):
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
                operation_messages.get(
                    operation, "PROJECT_MANAGERロールへの操作にはPROJECT_MANAGER権限が必要です"
                ),
                details={
                    "required_role": "project_manager",
                    "current_role": requester_role.value,
                },
            )

        logger.debug("PROJECT_MODERATOR制限チェック完了")

    async def check_last_manager_protection(
        self, project_id: uuid.UUID, member: ProjectMember
    ) -> None:
        """最後のPROJECT_MANAGERの保護チェックを実行します。

        プロジェクトには最低1人のPROJECT_MANAGERが必要です。
        最後のPROJECT_MANAGERのロール変更や削除を防ぎます。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            member (ProjectMember): 対象メンバー

        Raises:
            ValidationError: 対象メンバーが最後のPROJECT_MANAGERの場合

        Example:
            >>> await checker.check_last_manager_protection(project_id, member)

        Note:
            - PROJECT_MANAGER以外のロールの場合はチェックをスキップします
            - PROJECT_MANAGERが2人以上いる場合はチェックをパスします
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
        manager_count = await self.member_repository.count_by_role(
            project_id, ProjectRole.PROJECT_MANAGER
        )

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
