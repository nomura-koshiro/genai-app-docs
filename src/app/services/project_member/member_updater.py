"""プロジェクトメンバーロール更新のビジネスロジックサービス。

このモジュールは、プロジェクトメンバーのロール更新に関するビジネスロジックを提供します。
権限チェックは ProjectMemberAuthorizationChecker に委譲し、コードの重複を削減します。

主な機能:
    - メンバーのロール更新（単一・一括）
    - 権限チェック（PROJECT_MANAGER/PROJECT_MODERATOR）
    - 最後のPROJECT_MANAGERの保護
    - PROJECT_MODERATOR制限の適用

使用例:
    >>> from app.services.project_member.member_updater import ProjectMemberUpdater
    >>>
    >>> async with get_db() as db:
    ...     updater = ProjectMemberUpdater(db)
    ...     updated = await updater.update_member_role(
    ...         member_id, ProjectRole.MEMBER, requester_id
    ...     )
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.project_member import ProjectMember, ProjectRole
from app.repositories.project_member import ProjectMemberRepository
from app.schemas.project_member import (
    ProjectMemberBulkUpdateError,
    ProjectMemberRoleUpdate,
)
from app.services.project_member.authorization_checker import (
    ProjectMemberAuthorizationChecker,
)

logger = get_logger(__name__)


class ProjectMemberUpdater:
    """プロジェクトメンバーロール更新のビジネスロジックを提供するサービスクラス。

    このサービスは、プロジェクトメンバーのロール更新操作を提供します。
    権限チェックは ProjectMemberAuthorizationChecker に委譲し、
    コードの重複を削減します。

    Attributes:
        db (AsyncSession): データベースセッション
        repository (ProjectMemberRepository): メンバーリポジトリ
        auth_checker (ProjectMemberAuthorizationChecker): 権限チェッカー

    Example:
        >>> async with get_db() as db:
        ...     updater = ProjectMemberUpdater(db)
        ...     updated = await updater.update_member_role(member_id, new_role, requester_id)
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバー更新サービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.repository = ProjectMemberRepository(db)
        self.auth_checker = ProjectMemberAuthorizationChecker(db)

        logger.debug("プロジェクトメンバー更新サービスを初期化しました")

    @measure_performance
    @transactional
    async def update_member_role(
        self,
        member_id: uuid.UUID,
        new_role: ProjectRole,
        requester_id: uuid.UUID,
    ) -> ProjectMember:
        """メンバーのロールを更新します。

        このメソッドは以下の処理を実行します：
        1. メンバーの存在確認
        2. リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR、auth_checkerに委譲）
        3. PROJECT_MODERATOR制限チェック（auth_checkerに委譲）
        4. 最後のPROJECT_MANAGER保護（auth_checkerに委譲）
        5. ロール更新

        Args:
            member_id (uuid.UUID): メンバーシップのUUID
            new_role (ProjectRole): 新しいロール
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            ProjectMember: 更新されたメンバーインスタンス

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合
            ValidationError: 最後のPROJECT_MANAGERを降格しようとした場合

        Example:
            >>> updated = await updater.update_member_role(
            ...     member_id, ProjectRole.MEMBER, requester_id
            ... )
            >>> print(f"Updated role to: {updated.role}")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR のみがロール更新を実行可能
            - PROJECT_MANAGER ロールの変更は PROJECT_MANAGER のみが実行可能
            - PROJECT_MODERATOR は VIEWER/MEMBER/PROJECT_MODERATOR のみ更新可能
            - 最後の PROJECT_MANAGER は降格できません
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
            requester_role = await self.auth_checker.get_requester_role(
                member.project_id, requester_id
            )
            await self.auth_checker.check_can_manage_members(requester_role)

            # PROJECT_MODERATOR制限チェック（現在のロールと新しいロール両方）
            # 現在のロールがPROJECT_MANAGERの場合
            if member.role == ProjectRole.PROJECT_MANAGER:
                await self.auth_checker.check_moderator_limitations(
                    requester_role=requester_role,
                    target_role=member.role,
                    operation="update",
                )

            # 新しいロールがPROJECT_MANAGERの場合
            if new_role == ProjectRole.PROJECT_MANAGER:
                await self.auth_checker.check_moderator_limitations(
                    requester_role=requester_role,
                    target_role=new_role,
                    operation="update",
                )

            # 最後のPROJECT_MANAGERの降格禁止（新しいロールがPROJECT_MANAGER以外の場合のみチェック）
            if new_role != ProjectRole.PROJECT_MANAGER:
                await self.auth_checker.check_last_manager_protection(
                    member.project_id, member
                )

            # ロールを更新
            updated_member = await self.repository.update_role(member_id, new_role)
            if not updated_member:
                raise NotFoundError(
                    "メンバーが見つかりません", details={"member_id": str(member_id)}
                )

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

    @measure_performance
    @transactional
    async def update_members_bulk(
        self,
        project_id: uuid.UUID,
        updates_data: list[ProjectMemberRoleUpdate],
        requester_id: uuid.UUID,
    ) -> tuple[list[ProjectMember], list[ProjectMemberBulkUpdateError]]:
        """プロジェクトの複数メンバーのロールを一括更新します。

        このメソッドは複数のメンバーのロールを一括で更新し、成功と失敗を分けて返します。
        一部失敗しても成功したメンバーは更新されます。

        処理フロー：
        1. プロジェクトの存在確認（auth_checkerに委譲）
        2. リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR、auth_checkerに委譲）
        3. 各メンバーについて：
           a. メンバーの存在確認
           b. プロジェクトIDの確認
           c. PROJECT_MODERATOR制限チェック
           d. 最後のPROJECT_MANAGER保護チェック
           e. ロール更新（失敗は記録して継続）

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            updates_data (list[ProjectMemberRoleUpdate]): 更新するメンバーのリスト
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            tuple[list[ProjectMember], list[ProjectMemberBulkUpdateError]]:
                (更新に成功したメンバーリスト, 失敗情報リスト)

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合

        Example:
            >>> updates = [
            ...     ProjectMemberRoleUpdate(member_id=member1_id, role=ProjectRole.MEMBER),
            ...     ProjectMemberRoleUpdate(member_id=member2_id, role=ProjectRole.VIEWER)
            ... ]
            >>> updated, failed = await updater.update_members_bulk(
            ...     project_id, updates, requester_id
            ... )
            >>> print(f"Updated: {len(updated)}, Failed: {len(failed)}")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR の権限が必要
            - PROJECT_MANAGER ロールの変更は PROJECT_MANAGER のみが実行可能
            - PROJECT_MODERATOR は VIEWER/MEMBER/PROJECT_MODERATOR のみ更新可能
            - 最後の PROJECT_MANAGER は降格できません
            - 一部失敗しても成功したメンバーは更新されます
        """
        logger.info(
            "プロジェクトメンバー一括更新開始",
            project_id=str(project_id),
            update_count=len(updates_data),
            requester_id=str(requester_id),
            action="update_members_bulk",
        )

        updated_members: list[ProjectMember] = []
        failed_updates: list[ProjectMemberBulkUpdateError] = []

        try:
            # プロジェクトの存在確認
            await self.auth_checker.check_project_exists(project_id)

            # リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            requester_role = await self.auth_checker.get_requester_role(
                project_id, requester_id
            )
            await self.auth_checker.check_can_manage_members(requester_role)

            # 各メンバーを更新
            for update_data in updates_data:
                try:
                    # メンバーの存在確認
                    member = await self.repository.get(update_data.member_id)
                    if not member:
                        failed_updates.append(
                            ProjectMemberBulkUpdateError(
                                member_id=update_data.member_id,
                                role=update_data.role,
                                error="メンバーが見つかりません",
                            )
                        )
                        logger.debug(
                            "メンバーが見つかりません",
                            member_id=str(update_data.member_id),
                        )
                        continue

                    # プロジェクトIDの確認（異なるプロジェクトのメンバーは更新できない）
                    if member.project_id != project_id:
                        failed_updates.append(
                            ProjectMemberBulkUpdateError(
                                member_id=update_data.member_id,
                                role=update_data.role,
                                error="このメンバーは別のプロジェクトに所属しています",
                            )
                        )
                        logger.debug(
                            "メンバーが異なるプロジェクトに所属しています",
                            member_id=str(update_data.member_id),
                            expected_project_id=str(project_id),
                            actual_project_id=str(member.project_id),
                        )
                        continue

                    # PROJECT_MODERATOR制限チェック（現在のロールと新しいロール両方）
                    try:
                        # 現在のロールがPROJECT_MANAGERの場合
                        if member.role == ProjectRole.PROJECT_MANAGER:
                            await self.auth_checker.check_moderator_limitations(
                                requester_role=requester_role,
                                target_role=member.role,
                                operation="update",
                            )

                        # 新しいロールがPROJECT_MANAGERの場合
                        if update_data.role == ProjectRole.PROJECT_MANAGER:
                            await self.auth_checker.check_moderator_limitations(
                                requester_role=requester_role,
                                target_role=update_data.role,
                                operation="update",
                            )
                    except AuthorizationError as e:
                        failed_updates.append(
                            ProjectMemberBulkUpdateError(
                                member_id=update_data.member_id,
                                role=update_data.role,
                                error=str(e),
                            )
                        )
                        logger.debug(
                            "PROJECT_MODERATOR制限により更新できません",
                            member_id=str(update_data.member_id),
                            current_role=member.role.value,
                            requested_role=update_data.role.value,
                        )
                        continue

                    # 最後のPROJECT_MANAGERの降格禁止（新しいロールがPROJECT_MANAGER以外の場合のみチェック）
                    if update_data.role != ProjectRole.PROJECT_MANAGER:
                        try:
                            await self.auth_checker.check_last_manager_protection(
                                project_id, member
                            )
                        except ValidationError:
                            failed_updates.append(
                                ProjectMemberBulkUpdateError(
                                    member_id=update_data.member_id,
                                    role=update_data.role,
                                    error="プロジェクトには最低1人のPROJECT_MANAGERが必要です",
                                )
                            )
                            logger.debug(
                                "最後のPROJECT_MANAGERは降格できません",
                                member_id=str(update_data.member_id),
                            )
                            continue

                    # ロールを更新
                    updated_member = await self.repository.update_role(
                        update_data.member_id, update_data.role
                    )
                    if not updated_member:
                        failed_updates.append(
                            ProjectMemberBulkUpdateError(
                                member_id=update_data.member_id,
                                role=update_data.role,
                                error="メンバーの更新に失敗しました",
                            )
                        )
                        continue

                    await self.db.flush()
                    await self.db.refresh(updated_member)

                    updated_members.append(updated_member)

                    logger.debug(
                        "メンバーロールを更新しました",
                        member_id=str(update_data.member_id),
                        old_role=member.role.value,
                        new_role=update_data.role.value,
                    )

                except Exception as e:
                    # 個別のメンバー更新で予期しないエラーが発生した場合
                    failed_updates.append(
                        ProjectMemberBulkUpdateError(
                            member_id=update_data.member_id,
                            role=update_data.role,
                            error=f"予期しないエラーが発生しました: {str(e)}",
                        )
                    )
                    logger.error(
                        "メンバー更新中にエラーが発生しました",
                        member_id=str(update_data.member_id),
                        error=str(e),
                        exc_info=True,
                    )

            logger.info(
                "プロジェクトメンバー一括更新完了",
                project_id=str(project_id),
                total_requested=len(updates_data),
                total_updated=len(updated_members),
                total_failed=len(failed_updates),
                requester_id=str(requester_id),
            )

            return updated_members, failed_updates

        except (NotFoundError, AuthorizationError):
            raise
        except Exception as e:
            logger.error(
                "メンバー一括更新中に予期しないエラーが発生しました",
                project_id=str(project_id),
                update_count=len(updates_data),
                requester_id=str(requester_id),
                error=str(e),
                exc_info=True,
            )
            raise
