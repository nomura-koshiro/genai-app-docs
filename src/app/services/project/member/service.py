"""プロジェクトメンバー管理のファサードサービス。

このモジュールは、プロジェクトメンバー管理の統一インターフェースを提供します。
各機能は専門のサービスクラスに委譲されています。

元ファイル:
    C:/developments/genai-app-docs/src/app/services/project_member.py

リファクタリング後の構成:
    - ProjectMemberAuthorizationChecker: 権限チェック（authorization_checker.py）
    - ProjectMemberAdder: メンバー追加（member_adder.py）
    - ProjectMemberUpdater: ロール更新（member_updater.py）
    - ProjectMemberRemover: メンバー削除（member_remover.py）
    - ProjectMemberService: ファサード（このファイル）

主な機能:
    - メンバーの追加（権限チェック、重複チェック）
    - メンバーのロール更新（権限チェック、最後のPROJECT_MANAGER保護）
    - メンバーの削除（権限チェック、最後のPROJECT_MANAGER保護、自分自身の削除禁止）
    - プロジェクト退出（最後のPROJECT_MANAGER保護）
    - メンバー一覧取得
    - ユーザーロール取得

使用例:
    >>> from app.services.project.member import ProjectMemberService
    >>> from app.schemas.project.member import ProjectMemberCreate
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

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.models import ProjectMember, ProjectRole
from app.repositories import ProjectMemberRepository
from app.schemas import (
    ProjectMemberBulkError,
    ProjectMemberBulkUpdateError,
    ProjectMemberCreate,
    ProjectMemberRoleUpdate,
)

from .adder import ProjectMemberAdder
from .authorization import ProjectMemberAuthorizationChecker
from .remover import ProjectMemberRemover
from .updater import ProjectMemberUpdater

logger = get_logger(__name__)


class ProjectMemberService:
    """プロジェクトメンバー管理のビジネスロジックを提供するファサードクラス。

    このクラスは既存のAPIを維持しながら、各機能を専門のサービスクラスに委譲します。

    Attributes:
        db (AsyncSession): データベースセッション
        repository (ProjectMemberRepository): メンバーリポジトリ
        auth_checker (ProjectMemberAuthorizationChecker): 権限チェッカー
        adder (ProjectMemberAdder): メンバー追加サービス
        updater (ProjectMemberUpdater): ロール更新サービス
        remover (ProjectMemberRemover): メンバー削除サービス

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

        # 専門サービスの初期化
        self.auth_checker = ProjectMemberAuthorizationChecker(db)
        self.adder = ProjectMemberAdder(db)
        self.updater = ProjectMemberUpdater(db)
        self.remover = ProjectMemberRemover(db)

        logger.info("プロジェクトメンバーサービスファサードを初期化しました")

    # ===== Member Addition Methods (ProjectMemberAdder) =====

    async def add_member(
        self,
        project_id: uuid.UUID,
        member_data: ProjectMemberCreate,
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
        return await self.adder.add_member(project_id, member_data, added_by)

    async def add_members_bulk(
        self,
        project_id: uuid.UUID,
        members_data: list[ProjectMemberCreate],
        added_by: uuid.UUID,
    ) -> tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
        """プロジェクトに複数のメンバーを一括追加します。

        このメソッドはバルク操作として複数のメンバーを追加します。
        個別の失敗はエラーリストとして返され、成功したメンバーは通常通り追加されます。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            members_data (list[ProjectMemberCreate]): メンバー追加データのリスト
            added_by (uuid.UUID): 追加者のユーザーUUID

        Returns:
            tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
                - 成功したメンバーのリスト
                - 失敗したメンバーのエラーリスト

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: 追加者の権限が不足している場合

        Example:
            >>> members_data = [
            ...     ProjectMemberCreate(user_id=user1_id, role=ProjectRole.MEMBER),
            ...     ProjectMemberCreate(user_id=user2_id, role=ProjectRole.VIEWER)
            ... ]
            >>> members, errors = await member_service.add_members_bulk(
            ...     project_id, members_data, added_by=manager_id
            ... )
            >>> print(f"Added {len(members)} members, {len(errors)} errors")

        Note:
            - 個別の失敗でもトランザクション全体がロールバックされることはありません
            - 各メンバーの追加は独立して処理されます
        """
        return await self.adder.add_members_bulk(project_id, members_data, added_by)

    # ===== Member Retrieval Methods (ProjectMemberRepository) =====

    @measure_performance
    async def get_project_members(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ProjectMember], int]:
        """プロジェクトのメンバー一覧を取得します。

        このメソッドは以下の処理を実行します：
        1. プロジェクトの存在確認
        2. リクエスタがプロジェクトメンバーであることを確認
        3. メンバー一覧を取得

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            list[ProjectMember]: プロジェクトメンバーのリスト

        Raises:
            NotFoundError: プロジェクトが見つからない場合
            AuthorizationError: リクエスタがプロジェクトメンバーでない場合

        Example:
            >>> members = await member_service.get_project_members(
            ...     project_id, requester_id
            ... )
            >>> print(f"Found {len(members)} members")

        Note:
            - プロジェクトメンバーであれば誰でも一覧を取得できます
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
            await self.auth_checker.check_project_exists(project_id)

            # リクエスタがプロジェクトメンバーであることを確認
            await self.auth_checker.get_requester_role(project_id, requester_id)

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

        Example:
            >>> role = await member_service.get_user_role(project_id, user_id)
            >>> if role:
            ...     print(f"User role: {role.value}")
            ... else:
            ...     print("User is not a project member")

        Note:
            - ユーザーがプロジェクトメンバーでない場合はNoneを返します
            - 権限チェックは行いません（読み取り専用）
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

    # ===== Member Update Methods (ProjectMemberUpdater) =====

    async def update_member_role(
        self,
        member_id: uuid.UUID,
        new_role: ProjectRole,
        requester_id: uuid.UUID,
    ) -> ProjectMember:
        """メンバーのロールを更新します。

        このメソッドは以下の処理を実行します：
        1. メンバーの存在確認
        2. リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
        3. PROJECT_MANAGERロールへの更新の場合はリクエスタがPROJECT_MANAGERであることを確認
        4. 最後のPROJECT_MANAGERの保護
        5. ロールを更新

        Args:
            member_id (uuid.UUID): メンバーのUUID
            new_role (ProjectRole): 新しいロール
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            ProjectMember: 更新されたメンバーインスタンス

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合
            ValidationError: 最後のPROJECT_MANAGERのロール変更を試みた場合

        Example:
            >>> member = await member_service.update_member_role(
            ...     member_id, ProjectRole.PROJECT_MODERATOR, requester_id=manager_id
            ... )
            >>> print(f"Updated role: {member.role.value}")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR の権限が必要
            - PROJECT_MANAGER ロールへの更新は PROJECT_MANAGER のみが実行可能
            - PROJECT_MODERATOR は VIEWER/MEMBER/PROJECT_MODERATOR への更新のみ可能
            - 最後のPROJECT_MANAGERはロール変更できません
        """
        return await self.updater.update_member_role(member_id, new_role, requester_id)

    async def update_members_bulk(
        self,
        updates: list[ProjectMemberRoleUpdate],
        requester_id: uuid.UUID,
    ) -> tuple[list[ProjectMember], list[ProjectMemberBulkUpdateError]]:
        """複数のメンバーのロールを一括更新します。

        このメソッドはバルク操作として複数のメンバーのロールを更新します。
        個別の失敗はエラーリストとして返され、成功したメンバーは通常通り更新されます。

        Args:
            updates (list[ProjectMemberRoleUpdate]): ロール更新データのリスト
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            tuple[list[ProjectMember], list[ProjectMemberBulkUpdateError]]:
                - 成功したメンバーのリスト
                - 失敗したメンバーのエラーリスト

        Raises:
            なし（個別の失敗はエラーリストとして返される）

        Example:
            >>> updates = [
            ...     ProjectMemberRoleUpdate(
            ...         member_id=member1_id,
            ...         new_role=ProjectRole.PROJECT_MODERATOR
            ...     ),
            ...     ProjectMemberRoleUpdate(
            ...         member_id=member2_id,
            ...         new_role=ProjectRole.MEMBER
            ...     )
            ... ]
            >>> members, errors = await member_service.update_members_bulk(
            ...     updates, requester_id=manager_id
            ... )
            >>> print(f"Updated {len(members)} members, {len(errors)} errors")

        Note:
            - 個別の失敗でもトランザクション全体がロールバックされることはありません
            - 各メンバーの更新は独立して処理されます
        """
        return await self.updater.update_members_bulk(updates, requester_id)

    # ===== Member Removal Methods (ProjectMemberRemover) =====

    async def remove_member(self, member_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        """プロジェクトからメンバーを削除します。

        このメソッドは以下の処理を実行します：
        1. メンバーの存在確認
        2. リクエスタの権限確認（PROJECT_MANAGER/PROJECT_MODERATOR）
        3. PROJECT_MANAGERの削除の場合はリクエスタがPROJECT_MANAGERであることを確認
        4. 自分自身の削除禁止（leave_projectを使用すべき）
        5. 最後のPROJECT_MANAGERの保護
        6. メンバーを削除

        Args:
            member_id (uuid.UUID): メンバーのUUID
            requester_id (uuid.UUID): リクエスタのユーザーUUID

        Returns:
            None

        Raises:
            NotFoundError: メンバーが見つからない場合
            AuthorizationError: リクエスタの権限が不足している場合、または自分自身を削除しようとした場合
            ValidationError: 最後のPROJECT_MANAGERを削除しようとした場合

        Example:
            >>> await member_service.remove_member(member_id, requester_id=manager_id)
            >>> print("Member removed successfully")

        Note:
            - PROJECT_MANAGER/PROJECT_MODERATOR の権限が必要
            - PROJECT_MANAGER の削除は PROJECT_MANAGER のみが実行可能
            - PROJECT_MODERATOR は VIEWER/MEMBER/PROJECT_MODERATOR のみ削除可能
            - 自分自身は削除できません（leave_projectを使用）
            - 最後のPROJECT_MANAGERは削除できません
        """
        return await self.remover.remove_member(member_id, requester_id)

    async def leave_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """プロジェクトから退出します。

        このメソッドは以下の処理を実行します：
        1. プロジェクトの存在確認
        2. メンバーシップの存在確認
        3. 最後のPROJECT_MANAGERの保護
        4. メンバーを削除

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): 退出するユーザーのUUID

        Returns:
            None

        Raises:
            NotFoundError: プロジェクトまたはメンバーシップが見つからない場合
            ValidationError: 最後のPROJECT_MANAGERが退出しようとした場合

        Example:
            >>> await member_service.leave_project(project_id, user_id)
            >>> print("Left project successfully")

        Note:
            - 自分自身が退出する場合に使用します
            - 最後のPROJECT_MANAGERは退出できません
            - 権限チェックは不要（自分自身の操作のため）
        """
        return await self.remover.leave_project(project_id, user_id)
