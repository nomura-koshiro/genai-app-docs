"""プロジェクトメンバー管理のビジネスロジックサービス。

このモジュールは、プロジェクトメンバーの追加、削除、ロール更新などのビジネスロジックを提供します。
すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

主な機能:
    - メンバーの追加（権限チェック、重複チェック）
    - メンバーのロール更新（権限チェック、最後のPROJECT_MANAGER保護）
    - メンバーの削除（権限チェック、最後のPROJECT_MANAGER保護、自分自身の削除禁止）
    - プロジェクト退出（最後のPROJECT_MANAGER保護）
    - メンバー一覧取得
    - ユーザーロール取得

使用例:
    >>> from app.services.project_member import ProjectMemberService
    >>> from app.schemas.project_member import ProjectMemberCreate
    >>>
    >>> async with get_db() as db:
    ...     member_service = ProjectMemberService(db)
    ...     member_data = ProjectMemberCreate(
    ...         user_id=user_id,
    ...         role=ProjectRole.MEMBER
    ...     )
    ...     member = await member_service.add_member(
    ...         project_id, member_data, added_by=manager_id
    ...     )
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.project_member import ProjectMember, ProjectRole
from app.repositories.project import ProjectRepository
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository
from app.schemas.project_member import (
    ProjectMemberBulkError,
    ProjectMemberBulkUpdateError,
    ProjectMemberCreate,
    ProjectMemberRoleUpdate,
)

logger = get_logger(__name__)


class ProjectMemberService:
    """プロジェクトメンバー管理のビジネスロジックを提供するサービスクラス。

    このサービスは、プロジェクトメンバーの追加、削除、ロール更新などの操作を提供します。
    すべての操作は非同期で実行され、適切なロギングとエラーハンドリングを含みます。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        repository: ProjectMemberRepositoryインスタンス（データベースアクセス用）
        project_repository: ProjectRepositoryインスタンス（プロジェクト情報取得用）
        user_repository: UserRepositoryインスタンス（ユーザー情報取得用）

    Example:
        >>> async with get_db() as db:
        ...     member_service = ProjectMemberService(db)
        ...     members = await member_service.get_project_members(
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
        self.user_repository = UserRepository(db)

    @measure_performance
    @transactional
    async def add_member(
        self,
        project_id: uuid.UUID,
        member_data: "ProjectMemberCreate",
        added_by: uuid.UUID,
    ) -> ProjectMember:
        """プロジェクトに新しいメンバーを追加します。

        このメソッドは以下の処理を実行します：
        1. プロジェクトの存在確認
        2. 追加するユーザーの存在確認
        3. 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
        4. PROJECT_MANAGERロール追加の場合は追加者がPROJECT_MANAGERであることを確認
        5. 重複チェック
        6. メンバーレコードの作成

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            member_data (ProjectMemberCreate): メンバー追加データ
                - user_id: 追加するユーザーのUUID
                - role: プロジェクトロール
            added_by (uuid.UUID): 追加者のユーザーUUID

        Returns:
            ProjectMember: 追加されたメンバーインスタンス

        Raises:
            NotFoundError: プロジェクトまたはユーザーが見つからない場合
            AuthorizationError: 追加者の権限が不足している場合
            ValidationError: メンバーが既に存在する場合

        Example:
            >>> member_data = ProjectMemberCreate(
            ...     user_id=user_id,
            ...     role=ProjectRole.MEMBER
            ... )
            >>> member = await member_service.add_member(
            ...     project_id, member_data, added_by=manager_id
            ... )
            >>> print(f"Added member: {member.user_id}")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR の権限が必要
            - PROJECT_MANAGER ロールの追加は PROJECT_MANAGER のみが実行可能
            - PROJECT_MODERATOR は VIEWER/MEMBER/PROJECT_MODERATOR のみ追加可能
            - 重複するメンバーは追加できません
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
            project = await self.project_repository.get(project_id)
            if not project:
                logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
                raise NotFoundError(
                    "プロジェクトが見つかりません",
                    details={"project_id": str(project_id)},
                )

            # ユーザーの存在確認
            user = await self.user_repository.get(member_data.user_id)
            if not user:
                logger.warning("ユーザーが見つかりません", user_id=str(member_data.user_id))
                raise NotFoundError(
                    "ユーザーが見つかりません",
                    details={"user_id": str(member_data.user_id)},
                )

            # 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            adder_role = await self.repository.get_user_role(project_id, added_by)
            if adder_role is None:
                logger.warning(
                    "追加者はプロジェクトのメンバーではありません",
                    project_id=str(project_id),
                    added_by=str(added_by),
                )
                raise AuthorizationError(
                    "このプロジェクトへのアクセス権限がありません",
                    details={"project_id": str(project_id)},
                )

            # PROJECT_MANAGERまたはPROJECT_MODERATORの権限が必要
            if adder_role not in [ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR]:
                logger.warning(
                    "メンバー追加の権限がありません",
                    project_id=str(project_id),
                    added_by=str(added_by),
                    adder_role=adder_role.value,
                )
                raise AuthorizationError(
                    "メンバーを追加する権限がありません",
                    details={
                        "required_role": "project_manager or project_moderator",
                        "current_role": adder_role.value,
                    },
                )

            # PROJECT_MODERATORはPROJECT_MANAGERロールを追加できない
            if adder_role == ProjectRole.PROJECT_MODERATOR and member_data.role == ProjectRole.PROJECT_MANAGER:
                logger.warning(
                    "PROJECT_MODERATORはPROJECT_MANAGERロールを追加できません",
                    project_id=str(project_id),
                    added_by=str(added_by),
                    requested_role=member_data.role.value,
                )
                raise AuthorizationError(
                    "PROJECT_MANAGERロールの追加にはPROJECT_MANAGER権限が必要です",
                    details={
                        "required_role": "project_manager",
                        "current_role": adder_role.value,
                    },
                )

            # 重複チェック
            existing_member = await self.repository.get_by_project_and_user(
                project_id, member_data.user_id
            )
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
        members_data: list["ProjectMemberCreate"],
        added_by: uuid.UUID,
    ) -> tuple[list[ProjectMember], list["ProjectMemberBulkError"]]:
        """プロジェクトに複数のメンバーを一括追加します。

        このメソッドは複数のメンバーを一括で追加し、成功と失敗を分けて返します。
        一部失敗しても成功したメンバーは追加されます。

        処理フロー：
        1. プロジェクトの存在確認
        2. 追加者の権限確認（ADMIN以上）
        3. 各メンバーについて：
           a. ユーザーの存在確認
           b. 権限チェック
           c. 重複チェック
           d. メンバー追加（失敗は記録して継続）

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            members_data (list[ProjectMemberCreate]): 追加するメンバーのリスト
            added_by (uuid.UUID): 追加者のユーザーUUID

        Returns:
            tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
                (追加に成功したメンバーリスト, 失敗情報リスト)

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: 追加者の権限が不足している場合

        Example:
            >>> members_data = [
            ...     ProjectMemberCreate(user_id=user1_id, role=ProjectRole.MEMBER),
            ...     ProjectMemberCreate(user_id=user2_id, role=ProjectRole.VIEWER)
            ... ]
            >>> added, failed = await member_service.add_members_bulk(
            ...     project_id, members_data, added_by=admin_id
            ... )
            >>> print(f"Added: {len(added)}, Failed: {len(failed)}")

        Note:
            - ADMIN 以上の権限が必要
            - OWNER ロールの追加は OWNER のみが実行可能
            - 一部失敗しても成功したメンバーは追加されます
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
            project = await self.project_repository.get(project_id)
            if not project:
                logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
                raise NotFoundError(
                    "プロジェクトが見つかりません",
                    details={"project_id": str(project_id)},
                )

            # 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            adder_role = await self.repository.get_user_role(project_id, added_by)
            if adder_role is None:
                logger.warning(
                    "追加者はプロジェクトのメンバーではありません",
                    project_id=str(project_id),
                    added_by=str(added_by),
                )
                raise AuthorizationError(
                    "このプロジェクトへのアクセス権限がありません",
                    details={"project_id": str(project_id)},
                )

            # PROJECT_MANAGERまたはPROJECT_MODERATORの権限が必要
            if adder_role not in [ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR]:
                logger.warning(
                    "メンバー追加の権限がありません",
                    project_id=str(project_id),
                    added_by=str(added_by),
                    adder_role=adder_role.value,
                )
                raise AuthorizationError(
                    "メンバーを追加する権限がありません",
                    details={
                        "required_role": "project_manager or project_moderator",
                        "current_role": adder_role.value,
                    },
                )

            # 各メンバーを追加
            for member_data in members_data:
                # PROJECT_MODERATORはPROJECT_MANAGERロールを追加できない
                if adder_role == ProjectRole.PROJECT_MODERATOR and member_data.role == ProjectRole.PROJECT_MANAGER:
                    failed_members.append(
                        ProjectMemberBulkError(
                            user_id=member_data.user_id,
                            role=member_data.role,
                            error="PROJECT_MODERATORはPROJECT_MANAGERロールを追加できません",
                        )
                    )
                    logger.debug(
                        "PROJECT_MODERATORはPROJECT_MANAGERロールを追加できません",
                        user_id=str(member_data.user_id),
                        requested_role=member_data.role.value,
                    )
                    continue

                try:
                    # ユーザーの存在確認
                    user = await self.user_repository.get(member_data.user_id)
                    if not user:
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
                    existing_member = await self.repository.get_by_project_and_user(
                        project_id, member_data.user_id
                    )
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

    @measure_performance
    async def get_project_members(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ProjectMember], int]:
        """プロジェクトのメンバー一覧を取得します。

        リクエスタがプロジェクトのメンバーであることを確認してから、
        メンバー一覧を返します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID
            skip (int): スキップするレコード数
                デフォルト: 0
            limit (int): 返す最大レコード数
                デフォルト: 100

        Returns:
            tuple[list[ProjectMember], int]: (メンバーリスト, 総件数)

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: リクエスタがメンバーでない場合

        Example:
            >>> members, total = await member_service.get_project_members(
            ...     project_id, requester_id, skip=0, limit=10
            ... )
            >>> print(f"Members: {len(members)} / {total}")
        """
        logger.debug(
            "プロジェクトメンバー一覧取得開始",
            project_id=str(project_id),
            requester_id=str(requester_id),
            skip=skip,
            limit=limit,
            action="get_project_members",
        )

        # プロジェクトの存在確認
        project = await self.project_repository.get(project_id)
        if not project:
            logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
            raise NotFoundError(
                "プロジェクトが見つかりません",
                details={"project_id": str(project_id)},
            )

        # リクエスタがメンバーであることを確認
        requester_member = await self.repository.get_by_project_and_user(
            project_id, requester_id
        )
        if not requester_member:
            logger.warning(
                "リクエスタはプロジェクトのメンバーではありません",
                project_id=str(project_id),
                requester_id=str(requester_id),
            )
            raise AuthorizationError(
                "このプロジェクトへのアクセス権限がありません",
                details={"project_id": str(project_id)},
            )

        # メンバー一覧を取得
        members = await self.repository.list_by_project(project_id, skip, limit)
        total = await self.repository.count_by_project(project_id)

        logger.debug(
            "プロジェクトメンバー一覧を正常に取得しました",
            project_id=str(project_id),
            count=len(members),
            total=total,
        )

        return members, total

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
        2. リクエスタの権限確認（OWNER/ADMIN）
        3. OWNERロール変更の場合はリクエスタがOWNERであることを確認
        4. 最後のOWNERの降格禁止
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
            ValidationError: 最後のOWNERを降格しようとした場合

        Example:
            >>> updated = await member_service.update_member_role(
            ...     member_id, requester_id
            ... )
            >>> print(f"Updated role to: {updated.role}")

        Note:
            - OWNER/ADMIN のみがロール更新を実行可能
            - OWNER ロールの変更は OWNER のみが実行可能
            - 最後の OWNER は降格できません
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
            requester_role = await self.repository.get_user_role(
                member.project_id, requester_id
            )
            if requester_role is None:
                logger.warning(
                    "リクエスタはプロジェクトのメンバーではありません",
                    project_id=str(member.project_id),
                    requester_id=str(requester_id),
                )
                raise AuthorizationError(
                    "このプロジェクトへのアクセス権限がありません",
                    details={"project_id": str(member.project_id)},
                )

            # PROJECT_MANAGERまたはPROJECT_MODERATORの権限が必要
            if requester_role not in [ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR]:
                logger.warning(
                    "ロール更新の権限がありません",
                    project_id=str(member.project_id),
                    requester_id=str(requester_id),
                    requester_role=requester_role.value,
                )
                raise AuthorizationError(
                    "ロールを更新する権限がありません",
                    details={
                        "required_role": "project_manager or project_moderator",
                        "current_role": requester_role.value,
                    },
                )

            # PROJECT_MODERATORはPROJECT_MANAGERロールへの変更・からの変更ができない
            if requester_role == ProjectRole.PROJECT_MODERATOR:
                if member.role == ProjectRole.PROJECT_MANAGER or new_role == ProjectRole.PROJECT_MANAGER:
                    logger.warning(
                        "PROJECT_MODERATORはPROJECT_MANAGERロールを変更できません",
                        project_id=str(member.project_id),
                        requester_id=str(requester_id),
                        current_role=member.role.value,
                        new_role=new_role.value,
                    )
                    raise AuthorizationError(
                        "PROJECT_MANAGERロールの変更にはPROJECT_MANAGER権限が必要です",
                        details={
                            "required_role": "project_manager",
                            "current_role": requester_role.value,
                        },
                    )

            # 最後のPROJECT_MANAGERの降格禁止
            if member.role == ProjectRole.PROJECT_MANAGER and new_role != ProjectRole.PROJECT_MANAGER:
                admin_count = await self.repository.count_by_role(
                    member.project_id, ProjectRole.PROJECT_MANAGER
                )
                if admin_count <= 1:
                    logger.warning(
                        "最後のPROJECT_MANAGERは降格できません",
                        project_id=str(member.project_id),
                        member_id=str(member_id),
                    )
                    raise ValidationError(
                        "プロジェクトには最低1人のPROJECT_MANAGERが必要です",
                        details={"project_id": str(member.project_id)},
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
        updates_data: list["ProjectMemberRoleUpdate"],
        requester_id: uuid.UUID,
    ) -> tuple[list[ProjectMember], list["ProjectMemberBulkUpdateError"]]:
        """プロジェクトの複数メンバーのロールを一括更新します。

        このメソッドは複数のメンバーのロールを一括で更新し、成功と失敗を分けて返します。
        一部失敗しても成功したメンバーは更新されます。

        処理フロー：
        1. プロジェクトの存在確認
        2. リクエスタの権限確認（OWNER/ADMIN）
        3. 各メンバーについて：
           a. メンバーの存在確認
           b. 権限チェック
           c. 最後のOWNER降格チェック
           d. ロール更新（失敗は記録して継続）

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
            ...     ProjectMemberRoleUpdate(member_id=member1_id, role=ProjectRole.ADMIN),
            ...     ProjectMemberRoleUpdate(member_id=member2_id, role=ProjectRole.MEMBER)
            ... ]
            >>> updated, failed = await member_service.update_members_bulk(
            ...     project_id, updates, requester_id
            ... )
            >>> print(f"Updated: {len(updated)}, Failed: {len(failed)}")

        Note:
            - OWNER/ADMIN の権限が必要
            - OWNER ロールの変更は OWNER のみが実行可能
            - 最後の OWNER は降格できません
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
            project = await self.project_repository.get(project_id)
            if not project:
                logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
                raise NotFoundError(
                    "プロジェクトが見つかりません",
                    details={"project_id": str(project_id)},
                )

            # リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            requester_role = await self.repository.get_user_role(project_id, requester_id)
            if requester_role is None:
                logger.warning(
                    "リクエスタはプロジェクトのメンバーではありません",
                    project_id=str(project_id),
                    requester_id=str(requester_id),
                )
                raise AuthorizationError(
                    "このプロジェクトへのアクセス権限がありません",
                    details={"project_id": str(project_id)},
                )

            # PROJECT_MANAGERまたはPROJECT_MODERATORの権限が必要
            if requester_role not in [ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR]:
                logger.warning(
                    "ロール更新の権限がありません",
                    project_id=str(project_id),
                    requester_id=str(requester_id),
                    requester_role=requester_role.value,
                )
                raise AuthorizationError(
                    "ロールを更新する権限がありません",
                    details={
                        "required_role": "project_manager or project_moderator",
                        "current_role": requester_role.value,
                    },
                )

            # 各メンバーを更新
            for update_data in updates_data:
                # PROJECT_MODERATORはPROJECT_MANAGERロールへの変更ができない
                if requester_role == ProjectRole.PROJECT_MODERATOR and update_data.role == ProjectRole.PROJECT_MANAGER:
                    failed_updates.append(
                        ProjectMemberBulkUpdateError(
                            member_id=update_data.member_id,
                            role=update_data.role,
                            error="PROJECT_MODERATORはPROJECT_MANAGERロールを設定できません",
                        )
                    )
                    logger.debug(
                        "PROJECT_MODERATORはPROJECT_MANAGERロールを設定できません",
                        member_id=str(update_data.member_id),
                        requested_role=update_data.role.value,
                    )
                    continue

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

                    # PROJECT_MODERATORはPROJECT_MANAGERメンバーを変更できない
                    if requester_role == ProjectRole.PROJECT_MODERATOR and member.role == ProjectRole.PROJECT_MANAGER:
                        failed_updates.append(
                            ProjectMemberBulkUpdateError(
                                member_id=update_data.member_id,
                                role=update_data.role,
                                error="PROJECT_MODERATORはPROJECT_MANAGERメンバーのロールを変更できません",
                            )
                        )
                        logger.debug(
                            "PROJECT_MODERATORはPROJECT_MANAGERメンバーを変更できません",
                            member_id=str(update_data.member_id),
                            current_role=member.role.value,
                        )
                        continue

                    # 最後のPROJECT_MANAGERの降格禁止
                    if member.role == ProjectRole.PROJECT_MANAGER and update_data.role != ProjectRole.PROJECT_MANAGER:
                        admin_count = await self.repository.count_by_role(
                            project_id, ProjectRole.PROJECT_MANAGER
                        )
                        if admin_count <= 1:
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
        2. リクエスタの権限確認（OWNER/ADMIN）
        3. 自分自身の削除禁止
        4. 最後のOWNERの削除禁止
        5. メンバー削除

        Args:
            member_id (uuid.UUID): メンバーシップのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合
            ValidationError:
                - 自分自身を削除しようとした場合
                - 最後のOWNERを削除しようとした場合

        Example:
            >>> await member_service.remove_member(member_id, requester_id)
            >>> print("Member removed")

        Note:
            - OWNER/ADMIN のみが削除を実行可能
            - 自分自身は削除できません（プロジェクト退出を使用）
            - 最後の OWNER は削除できません
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
            requester_role = await self.repository.get_user_role(
                member.project_id, requester_id
            )
            if requester_role is None:
                logger.warning(
                    "リクエスタはプロジェクトのメンバーではありません",
                    project_id=str(member.project_id),
                    requester_id=str(requester_id),
                )
                raise AuthorizationError(
                    "このプロジェクトへのアクセス権限がありません",
                    details={"project_id": str(member.project_id)},
                )

            # PROJECT_MANAGERまたはPROJECT_MODERATORの権限が必要
            if requester_role not in [ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR]:
                logger.warning(
                    "メンバー削除の権限がありません",
                    project_id=str(member.project_id),
                    requester_id=str(requester_id),
                    requester_role=requester_role.value,
                )
                raise AuthorizationError(
                    "メンバーを削除する権限がありません",
                    details={
                        "required_role": "project_manager or project_moderator",
                        "current_role": requester_role.value,
                    },
                )

            # PROJECT_MODERATORはPROJECT_MANAGERメンバーを削除できない
            if requester_role == ProjectRole.PROJECT_MODERATOR and member.role == ProjectRole.PROJECT_MANAGER:
                logger.warning(
                    "PROJECT_MODERATORはPROJECT_MANAGERメンバーを削除できません",
                    project_id=str(member.project_id),
                    requester_id=str(requester_id),
                    target_role=member.role.value,
                )
                raise AuthorizationError(
                    "PROJECT_MANAGERメンバーの削除にはPROJECT_MANAGER権限が必要です",
                    details={
                        "required_role": "project_manager",
                        "current_role": requester_role.value,
                    },
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
            if member.role == ProjectRole.PROJECT_MANAGER:
                admin_count = await self.repository.count_by_role(
                    member.project_id, ProjectRole.PROJECT_MANAGER
                )
                if admin_count <= 1:
                    logger.warning(
                        "最後のPROJECT_MANAGERは削除できません",
                        project_id=str(member.project_id),
                        member_id=str(member_id),
                    )
                    raise ValidationError(
                        "プロジェクトには最低1人のPROJECT_MANAGERが必要です",
                        details={"project_id": str(member.project_id)},
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
        2. 最後のOWNERの退出禁止
        3. メンバーシップ削除

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Raises:
            NotFoundError: メンバーシップが見つからない場合
            ValidationError: 最後のOWNERが退出しようとした場合

        Example:
            >>> await member_service.leave_project(project_id, user_id)
            >>> print("Left project")

        Note:
            - 最後の OWNER は退出できません
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
            if member.role == ProjectRole.PROJECT_MANAGER:
                admin_count = await self.repository.count_by_role(
                    project_id, ProjectRole.PROJECT_MANAGER
                )
                if admin_count <= 1:
                    logger.warning(
                        "最後のPROJECT_MANAGERは退出できません",
                        project_id=str(project_id),
                        user_id=str(user_id),
                    )
                    raise ValidationError(
                        "プロジェクトには最低1人のPROJECT_MANAGERが必要です。他のメンバーをPROJECT_MANAGERに昇格させてから退出してください。",
                        details={"project_id": str(project_id)},
                    )

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

    @measure_performance
    async def get_user_role(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ユーザーのプロジェクトロールを取得します。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Returns:
            dict: ロール情報
                - project_id: プロジェクトUUID
                - user_id: ユーザーUUID
                - role: プロジェクトロール
                - is_owner: OWNER ロールかどうか
                - is_admin: ADMIN 以上のロールかどうか

        Raises:
            NotFoundError:
                - プロジェクトが見つからない場合
                - ユーザーがメンバーでない場合

        Example:
            >>> role_info = await member_service.get_user_role(
            ...     project_id, user_id
            ... )
            >>> if role_info["is_owner"]:
            ...     print("User is owner")
        """
        logger.debug(
            "ユーザーロール取得開始",
            project_id=str(project_id),
            user_id=str(user_id),
            action="get_user_role",
        )

        # プロジェクトの存在確認
        project = await self.project_repository.get(project_id)
        if not project:
            logger.warning("プロジェクトが見つかりません", project_id=str(project_id))
            raise NotFoundError(
                "プロジェクトが見つかりません",
                details={"project_id": str(project_id)},
            )

        # ユーザーロールを取得
        member = await self.repository.get_by_project_and_user(project_id, user_id)
        if not member:
            logger.warning(
                "ユーザーはプロジェクトのメンバーではありません",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise NotFoundError(
                "プロジェクトのメンバーではありません",
                details={"project_id": str(project_id), "user_id": str(user_id)},
            )

        role_info = {
            "project_id": project_id,
            "user_id": user_id,
            "role": member.role,
            # 後方互換性のためのフィールド（非推奨）
            "is_owner": member.role == ProjectRole.PROJECT_MANAGER,
            "is_admin": member.role in [ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR],
        }

        logger.debug(
            "ユーザーロールを正常に取得しました",
            project_id=str(project_id),
            user_id=str(user_id),
            role=member.role.value,
        )

        return role_info
