"""プロジェクトメンバーCRUDサービス。

このモジュールは、プロジェクトメンバーのCRUD操作を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import ProjectMember, ProjectRole
from app.schemas import ProjectMemberBulkError, ProjectMemberCreate
from app.services.project.project_member.base import ProjectMemberServiceBase

logger = get_logger(__name__)


class ProjectMemberCrudService(ProjectMemberServiceBase):
    """プロジェクトメンバーのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバーCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    # ================================================================================
    # Member Addition
    # ================================================================================

    @measure_performance
    @transactional
    async def add_member(
        self,
        project_id: uuid.UUID,
        member_data: ProjectMemberCreate,
        added_by: uuid.UUID,
    ) -> ProjectMember:
        """プロジェクトに新しいメンバーを追加します。

        Args:
            project_id: プロジェクトのUUID
            member_data: メンバー追加データ
            added_by: 追加者のユーザーUUID

        Returns:
            ProjectMember: 追加されたメンバーインスタンス

        Raises:
            NotFoundError: プロジェクトまたはユーザーが見つからない場合
            AuthorizationError: 追加者の権限が不足している場合
            ValidationError: メンバーが既に存在する場合
        """
        logger.info(
            "プロジェクトメンバー追加開始",
            project_id=str(project_id),
            user_id=str(member_data.user_id),
            role=member_data.role.value,
            added_by=str(added_by),
            action="add_member",
        )

        try:
            # プロジェクトの存在確認
            await self._check_project_exists(project_id)

            # ユーザーの存在確認
            await self._check_user_exists(member_data.user_id)

            # 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            adder_role = await self._get_requester_role(project_id, added_by)
            await self._check_can_manage_members(adder_role)

            # PROJECT_MODERATOR制限チェック
            await self._check_moderator_limitations(
                requester_role=adder_role,
                target_role=member_data.role,
                operation="add",
            )

            # 重複チェック
            existing_member = await self.repository.get_by_project_and_user(project_id, member_data.user_id)
            if existing_member:
                logger.warning(
                    "メンバーは既に存在します",
                    project_id=str(project_id),
                    user_id=str(member_data.user_id),
                    existing_role=existing_member.role.value,
                )
                raise ValidationError(
                    "ユーザーは既にプロジェクトのメンバーです",
                    details={
                        "user_id": str(member_data.user_id),
                        "current_role": existing_member.role.value,
                    },
                )

            # メンバーを追加
            member = await self.repository.create(
                project_id=project_id,
                user_id=member_data.user_id,
                role=member_data.role,
                added_by=added_by,
            )

            await self.db.flush()
            await self.db.refresh(member)

            logger.info(
                "プロジェクトメンバーを正常に追加しました",
                member_id=str(member.id),
                project_id=str(project_id),
                user_id=str(member_data.user_id),
                role=member_data.role.value,
                added_by=str(added_by),
            )

            return member

        except (NotFoundError, AuthorizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "メンバー追加中に予期しないエラーが発生しました",
                project_id=str(project_id),
                user_id=str(member_data.user_id),
                added_by=str(added_by),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    @transactional
    async def add_members_bulk(
        self,
        project_id: uuid.UUID,
        members_data: list[ProjectMemberCreate],
        added_by: uuid.UUID,
    ) -> tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
        """プロジェクトに複数のメンバーを一括追加します。

        Args:
            project_id: プロジェクトのUUID
            members_data: 追加するメンバーのリスト
            added_by: 追加者のユーザーUUID

        Returns:
            tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
                追加に成功したメンバーリスト、失敗情報リスト
        """
        logger.info(
            "プロジェクトメンバー一括追加開始",
            project_id=str(project_id),
            member_count=len(members_data),
            added_by=str(added_by),
            action="add_members_bulk",
        )

        added_members: list[ProjectMember] = []
        failed_members: list[ProjectMemberBulkError] = []

        try:
            # プロジェクトの存在確認
            await self._check_project_exists(project_id)

            # 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            adder_role = await self._get_requester_role(project_id, added_by)
            await self._check_can_manage_members(adder_role)

            # 各メンバーを追加
            for member_data in members_data:
                try:
                    # PROJECT_MODERATOR制限チェック
                    try:
                        await self._check_moderator_limitations(
                            requester_role=adder_role,
                            target_role=member_data.role,
                            operation="add",
                        )
                    except AuthorizationError as e:
                        failed_members.append(
                            ProjectMemberBulkError(
                                user_id=member_data.user_id,
                                role=member_data.role,
                                error=str(e),
                            )
                        )
                        logger.debug(
                            "PROJECT_MODERATOR制限により追加できません",
                            user_id=str(member_data.user_id),
                            requested_role=member_data.role.value,
                        )
                        continue

                    # ユーザーの存在確認
                    try:
                        await self._check_user_exists(member_data.user_id)
                    except NotFoundError:
                        failed_members.append(
                            ProjectMemberBulkError(
                                user_id=member_data.user_id,
                                role=member_data.role,
                                error="ユーザーが見つかりません",
                            )
                        )
                        logger.debug(
                            "ユーザーが見つかりません",
                            user_id=str(member_data.user_id),
                        )
                        continue

                    # 重複チェック
                    existing_member = await self.repository.get_by_project_and_user(project_id, member_data.user_id)
                    if existing_member:
                        failed_members.append(
                            ProjectMemberBulkError(
                                user_id=member_data.user_id,
                                role=member_data.role,
                                error=f"ユーザーは既にプロジェクトのメンバーです（現在のロール: {existing_member.role.value}）",
                            )
                        )
                        logger.debug(
                            "メンバーは既に存在します",
                            user_id=str(member_data.user_id),
                            existing_role=existing_member.role.value,
                        )
                        continue

                    # メンバーを追加
                    member = await self.repository.create(
                        project_id=project_id,
                        user_id=member_data.user_id,
                        role=member_data.role,
                        added_by=added_by,
                    )

                    await self.db.flush()
                    await self.db.refresh(member)

                    added_members.append(member)

                    logger.debug(
                        "メンバーを追加しました",
                        member_id=str(member.id),
                        user_id=str(member_data.user_id),
                        role=member_data.role.value,
                    )

                except Exception as e:
                    # 個別のメンバー追加で予期しないエラーが発生した場合
                    failed_members.append(
                        ProjectMemberBulkError(
                            user_id=member_data.user_id,
                            role=member_data.role,
                            error=f"予期しないエラーが発生しました: {str(e)}",
                        )
                    )
                    logger.error(
                        "メンバー追加中にエラーが発生しました",
                        user_id=str(member_data.user_id),
                        error=str(e),
                        exc_info=True,
                    )

            logger.info(
                "プロジェクトメンバー一括追加完了",
                project_id=str(project_id),
                total_requested=len(members_data),
                total_added=len(added_members),
                total_failed=len(failed_members),
                added_by=str(added_by),
            )

            return added_members, failed_members

        except (NotFoundError, AuthorizationError):
            raise
        except Exception as e:
            logger.error(
                "メンバー一括追加中に予期しないエラーが発生しました",
                project_id=str(project_id),
                member_count=len(members_data),
                added_by=str(added_by),
                error=str(e),
                exc_info=True,
            )
            raise

    # ================================================================================
    # Member Retrieval
    # ================================================================================

    @measure_performance
    async def get_project_members(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ProjectMember], int]:
        """プロジェクトのメンバー一覧を取得します。

        Args:
            project_id: プロジェクトのUUID
            requester_id: リクエスタのユーザーUUID
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            tuple[list[ProjectMember], int]: メンバーリスト、総件数
        """
        logger.info(
            "プロジェクトメンバー一覧取得開始",
            project_id=str(project_id),
            requester_id=str(requester_id),
            skip=skip,
            limit=limit,
            action="get_project_members",
        )

        try:
            # プロジェクトの存在確認
            await self._check_project_exists(project_id)

            # リクエスタがプロジェクトメンバーであることを確認
            await self._get_requester_role(project_id, requester_id)

            # メンバー一覧をDBレベルでページネーション（パフォーマンス最適化）
            members = await self.repository.list_by_project(project_id, skip, limit)

            # 総数を別途取得（正確なtotalを返すため）
            total = await self.repository.count_by_project(project_id)

            logger.info(
                "プロジェクトメンバー一覧取得完了",
                project_id=str(project_id),
                member_count=len(members),
                total=total,
            )

            return members, total

        except Exception as e:
            logger.error(
                "プロジェクトメンバー一覧取得失敗",
                project_id=str(project_id),
                requester_id=str(requester_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_user_role(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectRole | None:
        """指定したユーザーのプロジェクトロールを取得します。

        Args:
            project_id: プロジェクトのUUID
            user_id: ユーザーのUUID

        Returns:
            ProjectRole | None: ユーザーのロール（メンバーでない場合はNone）
        """
        logger.debug(
            "ユーザーロール取得",
            project_id=str(project_id),
            user_id=str(user_id),
            action="get_user_role",
        )

        role = await self.repository.get_user_role(project_id, user_id)

        logger.debug(
            "ユーザーロール取得完了",
            project_id=str(project_id),
            user_id=str(user_id),
            role=role.value if role else None,
        )

        return role

    # ================================================================================
    # Member Update
    # ================================================================================

    @measure_performance
    @transactional
    async def update_member_role(
        self,
        member_id: uuid.UUID,
        new_role: ProjectRole,
        requester_id: uuid.UUID,
    ) -> ProjectMember:
        """メンバーのロールを更新します。

        Args:
            member_id: メンバーシップのUUID
            new_role: 新しいロール
            requester_id: リクエスタのユーザーUUID

        Returns:
            ProjectMember: 更新されたメンバーインスタンス

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合
            ValidationError: 最後のPROJECT_MANAGERを降格しようとした場合
        """
        logger.info(
            "メンバーロール更新開始",
            member_id=str(member_id),
            new_role=new_role.value,
            requester_id=str(requester_id),
            action="update_member_role",
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
            requester_role = await self._get_requester_role(member.project_id, requester_id)
            await self._check_can_manage_members(requester_role)

            # PROJECT_MODERATOR制限チェック（現在のロールと新しいロール両方）
            # 現在のロールがPROJECT_MANAGERの場合
            if member.role == ProjectRole.PROJECT_MANAGER:
                await self._check_moderator_limitations(
                    requester_role=requester_role,
                    target_role=member.role,
                    operation="update",
                )

            # 新しいロールがPROJECT_MANAGERの場合
            if new_role == ProjectRole.PROJECT_MANAGER:
                await self._check_moderator_limitations(
                    requester_role=requester_role,
                    target_role=new_role,
                    operation="update",
                )

            # 最後のPROJECT_MANAGERの降格禁止（新しいロールがPROJECT_MANAGER以外の場合のみチェック）
            if new_role != ProjectRole.PROJECT_MANAGER:
                await self._check_last_manager_protection(member.project_id, member)

            # ロールを更新
            updated_member = await self.repository.update_role(member_id, new_role)
            if not updated_member:
                raise NotFoundError("メンバーが見つかりません", details={"member_id": str(member_id)})

            await self.db.flush()
            await self.db.refresh(updated_member)

            logger.info(
                "メンバーロールを正常に更新しました",
                member_id=str(member_id),
                old_role=member.role.value,
                new_role=new_role.value,
                requester_id=str(requester_id),
            )

            return updated_member

        except (NotFoundError, AuthorizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ロール更新中に予期しないエラーが発生しました",
                member_id=str(member_id),
                new_role=new_role.value,
                requester_id=str(requester_id),
                error=str(e),
                exc_info=True,
            )
            raise

    # ================================================================================
    # Member Removal
    # ================================================================================

    @measure_performance
    @transactional
    async def remove_member(self, member_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        """プロジェクトからメンバーを削除します。

        Args:
            member_id: メンバーシップのUUID
            requester_id: リクエスタのユーザーUUID

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合
            ValidationError: 自分自身を削除または最後のPROJECT_MANAGERを削除しようとした場合
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
            requester_role = await self._get_requester_role(member.project_id, requester_id)
            await self._check_can_manage_members(requester_role)

            # PROJECT_MODERATOR制限チェック（PROJECT_MANAGERメンバーは削除できない）
            await self._check_moderator_limitations(
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
            await self._check_last_manager_protection(member.project_id, member)

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
