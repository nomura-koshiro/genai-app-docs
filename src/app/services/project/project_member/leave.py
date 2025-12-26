"""プロジェクト退出サービス。

このモジュールは、プロジェクトからの退出操作を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.services.project.project_member.base import ProjectMemberServiceBase

logger = get_logger(__name__)


class ProjectMemberLeaveService(ProjectMemberServiceBase):
    """プロジェクト退出操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクト退出サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @measure_performance
    @transactional
    async def leave_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトから退出します。

        Args:
            project_id: プロジェクトのUUID
            user_id: ユーザーのUUID

        Raises:
            NotFoundError: メンバーシップが見つからない場合
            ValidationError: 最後のPROJECT_MANAGERが退出しようとした場合
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
            await self._check_last_manager_protection(project_id, member)

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
