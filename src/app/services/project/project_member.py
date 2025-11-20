"""プロジェクトメンバー管理サービス。

このモジュールは、プロジェクトメンバーの管理に関する全てのビジネスロジックを提供します。

主な機能:
    - メンバーの追加（単一・一括）
    - メンバーのロール更新
    - メンバーの削除・退出
    - 権限チェック
    - メンバー一覧取得

使用例:
    >>> from app.services.project.project_member import ProjectMemberService
    >>> from app.schemas.project.member import ProjectMemberCreate
    >>>
    >>> async with get_db() as db:
    ...     member_service = ProjectMemberService(db)
    ...     member = await member_service.add_member(
    ...         project_id, member_data, added_by=manager_id
    ...     )
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import Project, ProjectMember, ProjectRole, UserAccount
from app.repositories import ProjectMemberRepository, ProjectRepository, UserAccountRepository
from app.schemas import (
    ProjectMemberBulkError,
    ProjectMemberCreate,
)

logger = get_logger(__name__)


class ProjectMemberService:
    """プロジェクトメンバー管理サービス。

    このクラスは、プロジェクトメンバーの追加、更新、削除、および権限チェックを行います。

    Attributes:
        db (AsyncSession): データベースセッション
        repository (ProjectMemberRepository): メンバーリポジトリ
        project_repository (ProjectRepository): プロジェクトリポジトリ
        user_repository (UserAccountRepository): ユーザーリポジトリ

    Example:
        >>> async with get_db() as db:
        ...     member_service = ProjectMemberService(db)
        ...     members, total = await member_service.get_project_members(
        ...         project_id, requester_id
        ...     )
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバーサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.repository = ProjectMemberRepository(db)
        self.project_repository = ProjectRepository(db)
        self.user_repository = UserAccountRepository(db)

        logger.info("プロジェクトメンバーサービスを初期化しました")

    # ================================================================================
    # Public API - Member Addition
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
            project_id (uuid.UUID): プロジェクトのUUID
            member_data (ProjectMemberCreate): メンバー追加データ
            added_by (uuid.UUID): 追加者のユーザーUUID

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
            project_id (uuid.UUID): プロジェクトのUUID
            members_data (list[ProjectMemberCreate]): 追加するメンバーのリスト
            added_by (uuid.UUID): 追加者のユーザーUUID

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
    # Public API - Member Retrieval
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
            project_id (uuid.UUID): プロジェクトのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID
            skip (int): スキップするレコード数
            limit (int): 取得する最大レコード数

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

            # メンバー一覧を取得
            all_members = await self.repository.list_by_project(project_id)

            # ページネーション適用
            total = len(all_members)
            members = all_members[skip : skip + limit]

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
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

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
    # Public API - Member Update
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
            member_id (uuid.UUID): メンバーシップのUUID
            new_role (ProjectRole): 新しいロール
            requester_id (uuid.UUID): リクエスタのユーザーUUID

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
    # Public API - Member Removal
    # ================================================================================

    @measure_performance
    @transactional
    async def remove_member(self, member_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        """プロジェクトからメンバーを削除します。

        Args:
            member_id (uuid.UUID): メンバーシップのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

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

    @measure_performance
    @transactional
    async def leave_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトから退出します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

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

    # ================================================================================
    # Private Helper Methods
    # ================================================================================

    async def _check_project_exists(self, project_id: uuid.UUID) -> Project:
        """プロジェクトの存在を確認します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID

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
            user_id (uuid.UUID): ユーザーのUUID

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
            project_id (uuid.UUID): プロジェクトのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

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
            requester_role (ProjectRole): リクエスタのロール

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
            requester_role (ProjectRole): リクエスタのロール
            target_role (ProjectRole): 対象ユーザーのロール
            operation (str): 操作タイプ（"add", "update", "delete"）

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
            project_id (uuid.UUID): プロジェクトのUUID
            member (ProjectMember): 対象メンバー

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
