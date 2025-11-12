"""プロジェクトメンバー削除のビジネスロジックサービス。

このモジュールは、プロジェクトメンバーの削除・退出に関するビジネスロジックを提供します。
権限チェックは ProjectMemberAuthorizationChecker に委譲し、コードの重複を削減します。

主な機能:
    - メンバーの削除（管理者による削除）
    - プロジェクト退出（自身による退出）
    - 権限チェック（PROJECT_MANAGER/PROJECT_MODERATOR）
    - 最後のPROJECT_MANAGERの保護
    - 自己削除禁止

使用例:
    >>> from app.services.project.member.remover import ProjectMemberRemover
    >>>
    >>> async with get_db() as db:
    ...     remover = ProjectMemberRemover(db)
    ...     await remover.remove_member(member_id, requester_id)
    ...     # または
    ...     await remover.leave_project(project_id, user_id)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.project.member import ProjectMemberRepository
from app.services.project.member.authorization import (
    ProjectMemberAuthorizationChecker,
)

logger = get_logger(__name__)


class ProjectMemberRemover:
    """プロジェクトメンバー削除のビジネスロジックを提供するサービスクラス。

    このサービスは、プロジェクトメンバーの削除・退出操作を提供します。
    権限チェックは ProjectMemberAuthorizationChecker に委譲し、
    コードの重複を削減します。

    Attributes:
        db (AsyncSession): データベースセッション
        repository (ProjectMemberRepository): メンバーリポジトリ
        auth_checker (ProjectMemberAuthorizationChecker): 権限チェッカー

    Example:
        >>> async with get_db() as db:
        ...     remover = ProjectMemberRemover(db)
        ...     await remover.remove_member(member_id, requester_id)
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバー削除サービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.repository = ProjectMemberRepository(db)
        self.auth_checker = ProjectMemberAuthorizationChecker(db)

        logger.debug("プロジェクトメンバー削除サービスを初期化しました")

    @measure_performance
    @transactional
    async def remove_member(
        self,
        member_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> None:
        """プロジェクトからメンバーを削除します。

        このメソッドは以下の処理を実行します：
        1. メンバーの存在確認
        2. リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR、auth_checkerに委譲）
        3. PROJECT_MODERATOR制限チェック（auth_checkerに委譲）
        4. 自分自身の削除禁止
        5. 最後のPROJECT_MANAGER保護（auth_checkerに委譲）
        6. メンバー削除

        Args:
            member_id (uuid.UUID): メンバーシップのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合
            ValidationError:
                - 自分自身を削除しようとした場合
                - 最後のPROJECT_MANAGERを削除しようとした場合

        Example:
            >>> await remover.remove_member(member_id, requester_id)
            >>> print("Member removed")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR のみが削除を実行可能
            - PROJECT_MODERATOR は PROJECT_MANAGER メンバーを削除できません
            - 自分自身は削除できません（プロジェクト退出を使用）
            - 最後の PROJECT_MANAGER は削除できません
        """
        logger.info(
            "メンバー削除開始",
            member_id=str(member_id),
            requester_id=str(requester_id),
            action="remove_member",
        )

        try:
            # メンバーの存在確認
            member = await self.repository.get(member_id)
            if not member:
                logger.warning("メンバーが見つかりません", member_id=str(member_id))
                raise NotFoundError(
                    "メンバーが見つかりません",
                    details={"member_id": str(member_id)},
                )

            # リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            requester_role = await self.auth_checker.get_requester_role(
                member.project_id, requester_id
            )
            await self.auth_checker.check_can_manage_members(requester_role)

            # PROJECT_MODERATOR制限チェック（PROJECT_MANAGERメンバーは削除できない）
            await self.auth_checker.check_moderator_limitations(
                requester_role=requester_role,
                target_role=member.role,
                operation="delete",
            )

            # 自分自身の削除禁止
            if member.user_id == requester_id:
                logger.warning(
                    "自分自身は削除できません",
                    member_id=str(member_id),
                    requester_id=str(requester_id),
                )
                raise ValidationError(
                    "自分自身を削除することはできません。プロジェクト退出を使用してください。",
                    details={"member_id": str(member_id)},
                )

            # 最後のPROJECT_MANAGERの削除禁止
            await self.auth_checker.check_last_manager_protection(
                member.project_id, member
            )

            # メンバーを削除
            await self.repository.delete(member_id)

            await self.db.flush()

            logger.info(
                "メンバーを正常に削除しました",
                member_id=str(member_id),
                project_id=str(member.project_id),
                user_id=str(member.user_id),
                requester_id=str(requester_id),
            )

        except (NotFoundError, AuthorizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "メンバー削除中に予期しないエラーが発生しました",
                member_id=str(member_id),
                requester_id=str(requester_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    @transactional
    async def leave_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトから退出します。

        このメソッドは以下の処理を実行します：
        1. メンバーシップの存在確認
        2. 最後のPROJECT_MANAGER保護（auth_checkerに委譲）
        3. メンバーシップ削除

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Raises:
            NotFoundError: メンバーシップが見つからない場合
            ValidationError: 最後のPROJECT_MANAGERが退出しようとした場合

        Example:
            >>> await remover.leave_project(project_id, user_id)
            >>> print("Left project")

        Note:
            - 誰でも自分自身を退出させることができます
            - 最後の PROJECT_MANAGER は退出できません
            - 他のメンバーを退出させる場合は remove_member を使用してください
        """
        logger.info(
            "プロジェクト退出開始",
            project_id=str(project_id),
            user_id=str(user_id),
            action="leave_project",
        )

        try:
            # メンバーシップの存在確認
            member = await self.repository.get_by_project_and_user(project_id, user_id)
            if not member:
                logger.warning(
                    "メンバーシップが見つかりません",
                    project_id=str(project_id),
                    user_id=str(user_id),
                )
                raise NotFoundError(
                    "プロジェクトのメンバーではありません",
                    details={"project_id": str(project_id), "user_id": str(user_id)},
                )

            # 最後のPROJECT_MANAGERの退出禁止
            await self.auth_checker.check_last_manager_protection(project_id, member)

            # メンバーシップを削除
            await self.repository.delete(member.id)

            await self.db.flush()

            logger.info(
                "プロジェクトから正常に退出しました",
                project_id=str(project_id),
                user_id=str(user_id),
            )

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "プロジェクト退出中に予期しないエラーが発生しました",
                project_id=str(project_id),
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            raise
