"""プロジェクトサービス共通ベース。

このモジュールは、プロジェクトサービスの共通機能を提供します。
"""

import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.models import Project, ProjectMember, ProjectRole
from app.repositories import ProjectFileRepository, ProjectMemberRepository, ProjectRepository

logger = get_logger(__name__)


class ProjectServiceBase:
    """プロジェクトサービスの共通ベースクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = ProjectRepository(db)
        self.member_repository = ProjectMemberRepository(db)
        self.file_repository = ProjectFileRepository(db)

    async def _check_user_role(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        required_roles: list[ProjectRole],
    ) -> ProjectMember:
        """ユーザーのプロジェクトロールをチェックします。

        Args:
            project_id: プロジェクトのUUID
            user_id: ユーザーのUUID
            required_roles: 必要なロールのリスト

        Returns:
            ProjectMember: ユーザーのメンバーシップ情報

        Raises:
            AuthorizationError: ユーザーが必要なロールを持っていない場合
        """
        # ユーザーのメンバーシップを取得（リポジトリを使用）
        member = await self.member_repository.get_by_project_and_user(project_id, user_id)

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

    async def _delete_physical_files(self, project: Project) -> None:
        """プロジェクトに関連する物理ファイルを削除します。

        Args:
            project: プロジェクトモデルインスタンス

        Note:
            - ファイル削除失敗時もエラーログを記録して処理を継続します
            - データベースからの削除は別途CASCADEで実行されます
        """
        # プロジェクトに関連するファイルを取得（リポジトリを使用）
        project_files = await self.file_repository.list_by_project(
            project_id=project.id,
            skip=0,
            limit=10000,  # 大量ファイル対応
        )

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
