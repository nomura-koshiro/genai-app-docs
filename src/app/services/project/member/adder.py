"""プロジェクトメンバー追加のビジネスロジックサービス。

このモジュールは、プロジェクトメンバーの追加に関するビジネスロジックを提供します。
権限チェックは ProjectMemberAuthorizationChecker に委譲し、コードの重複を削減します。

主な機能:
    - メンバーの追加（単一・一括）
    - 権限チェック（PROJECT_MANAGER/PROJECT_MODERATOR）
    - 重複チェック
    - PROJECT_MODERATOR制限の適用

使用例:
    >>> from app.services.project.member.adder import ProjectMemberAdder
    >>> from app.schemas.project.member import ProjectMemberCreate
    >>>
    >>> async with get_db() as db:
    ...     adder = ProjectMemberAdder(db)
    ...     member_data = ProjectMemberCreate(
    ...         user_id=user_id,
    ...         role=ProjectRole.MEMBER
    ...     )
    ...     member = await adder.add_member(
    ...         project_id, member_data, added_by=manager_id
    ...     )
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.project.member import ProjectMember
from app.repositories.project.member import ProjectMemberRepository
from app.repositories.user import UserRepository
from app.schemas.project.member import ProjectMemberBulkError, ProjectMemberCreate
from app.services.project.member.authorization import (
    ProjectMemberAuthorizationChecker,
)

logger = get_logger(__name__)


class ProjectMemberAdder:
    """プロジェクトメンバー追加のビジネスロジックを提供するサービスクラス。

    このサービスは、プロジェクトメンバーの追加操作を提供します。
    権限チェックは ProjectMemberAuthorizationChecker に委譲し、
    コードの重複を削減します。

    Attributes:
        db (AsyncSession): データベースセッション
        repository (ProjectMemberRepository): メンバーリポジトリ
        user_repository (UserRepository): ユーザーリポジトリ
        auth_checker (ProjectMemberAuthorizationChecker): 権限チェッカー

    Example:
        >>> async with get_db() as db:
        ...     adder = ProjectMemberAdder(db)
        ...     member = await adder.add_member(project_id, member_data, added_by)
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバー追加サービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.repository = ProjectMemberRepository(db)
        self.user_repository = UserRepository(db)
        self.auth_checker = ProjectMemberAuthorizationChecker(db)

        logger.debug("プロジェクトメンバー追加サービスを初期化しました")

    @measure_performance
    @transactional
    async def add_member(
        self,
        project_id: uuid.UUID,
        member_data: ProjectMemberCreate,
        added_by: uuid.UUID,
    ) -> ProjectMember:
        """プロジェクトに新しいメンバーを追加します。

        このメソッドは以下の処理を実行します：
        1. プロジェクトの存在確認（auth_checkerに委譲）
        2. 追加するユーザーの存在確認（auth_checkerに委譲）
        3. 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR、auth_checkerに委譲）
        4. PROJECT_MODERATOR制限チェック（auth_checkerに委譲）
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
            >>> member = await adder.add_member(
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
            await self.auth_checker.check_project_exists(project_id)

            # ユーザーの存在確認
            await self.auth_checker.check_user_exists(member_data.user_id)

            # 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            adder_role = await self.auth_checker.get_requester_role(project_id, added_by)
            await self.auth_checker.check_can_manage_members(adder_role)

            # PROJECT_MODERATOR制限チェック
            await self.auth_checker.check_moderator_limitations(
                requester_role=adder_role,
                target_role=member_data.role,
                operation="add",
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
        members_data: list[ProjectMemberCreate],
        added_by: uuid.UUID,
    ) -> tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
        """プロジェクトに複数のメンバーを一括追加します。

        このメソッドは複数のメンバーを一括で追加し、成功と失敗を分けて返します。
        一部失敗しても成功したメンバーは追加されます。

        処理フロー：
        1. プロジェクトの存在確認（auth_checkerに委譲）
        2. 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR、auth_checkerに委譲）
        3. 各メンバーについて：
           a. ユーザーの存在確認
           b. PROJECT_MODERATOR制限チェック
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
            >>> added, failed = await adder.add_members_bulk(
            ...     project_id, members_data, added_by=manager_id
            ... )
            >>> print(f"Added: {len(added)}, Failed: {len(failed)}")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR の権限が必要
            - PROJECT_MANAGER ロールの追加は PROJECT_MANAGER のみが実行可能
            - PROJECT_MODERATOR は VIEWER/MEMBER/PROJECT_MODERATOR のみ追加可能
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
            await self.auth_checker.check_project_exists(project_id)

            # 追加者の権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
            adder_role = await self.auth_checker.get_requester_role(project_id, added_by)
            await self.auth_checker.check_can_manage_members(adder_role)

            # 各メンバーを追加
            for member_data in members_data:
                try:
                    # PROJECT_MODERATOR制限チェック
                    try:
                        await self.auth_checker.check_moderator_limitations(
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
                        await self.auth_checker.check_user_exists(member_data.user_id)
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
