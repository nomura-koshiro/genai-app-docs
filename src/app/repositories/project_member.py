"""プロジェクトメンバーモデル用のデータアクセスリポジトリ。

このモジュールは、ProjectMemberモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、プロジェクトメンバー固有のクエリメソッド
（プロジェクト別メンバー一覧、ユーザー別プロジェクト一覧、ロール更新など）を追加しています。

主な機能:
    - プロジェクトメンバーの追加・削除
    - プロジェクト+ユーザーでの検索
    - プロジェクト別メンバー一覧
    - ユーザー別プロジェクト一覧
    - ロール更新
    - ユーザーロール取得
    - メンバー数カウント

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.project_member import ProjectMemberRepository
    >>>
    >>> async with get_db() as db:
    ...     member_repo = ProjectMemberRepository(db)
    ...     member = await member_repo.get_by_project_and_user(project_id, user_id)
    ...     if member:
    ...         print(f"User role: {member.role}")
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.project_member import ProjectMember, ProjectRole
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ProjectMemberRepository(BaseRepository[ProjectMember, uuid.UUID]):
    """ProjectMemberモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    プロジェクトメンバーシップ管理に特化したクエリメソッドを提供します。

    メンバー管理機能:
        - get_by_project_and_user(): プロジェクト+ユーザーでメンバー検索
        - list_by_project(): プロジェクトメンバー一覧（ユーザー情報付き）
        - list_by_user(): ユーザーのプロジェクト一覧
        - update_role(): メンバーロール更新
        - delete_member(): メンバー削除
        - count_by_project(): プロジェクトメンバー数カウント
        - get_user_role(): ユーザーのロール取得

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるメンバー取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規メンバー追加
        - update(): メンバー情報更新
        - delete(): メンバー削除
        - count(): メンバー数カウント

    Example:
        >>> async with get_db() as db:
        ...     member_repo = ProjectMemberRepository(db)
        ...
        ...     # プロジェクト+ユーザーでメンバー検索
        ...     member = await member_repo.get_by_project_and_user(
        ...         project_id, user_id
        ...     )
        ...
        ...     # プロジェクトメンバー一覧（ユーザー情報付き）
        ...     members = await member_repo.list_by_project(
        ...         project_id, skip=0, limit=50
        ...     )
        ...
        ...     # ロール更新
        ...     updated = await member_repo.update_role(
        ...         member_id, ProjectRole.ADMIN
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - メンバー削除時、CASCADE設定により関連データも削除されます
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバーリポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
                - DIコンテナから自動的に注入されます
                - トランザクションスコープはリクエスト単位で管理されます

        Note:
            - 親クラス（BaseRepository）の__init__を呼び出し、
              ProjectMemberモデルとセッションを設定します
            - このコンストラクタは通常、FastAPIの依存性注入システムにより
              自動的に呼び出されます
        """
        super().__init__(ProjectMember, db)

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        """プロジェクトのメンバー数を取得します。

        ページネーションのtotal値として使用されます。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID

        Returns:
            int: プロジェクトのメンバー総数

        Example:
            >>> total = await member_repo.count_by_project(project_id)
            >>> print(f"Project members: {total}")
        """
        result = await self.db.execute(
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project_id)
        )
        return result.scalar_one()

    async def count_by_role(
        self,
        project_id: uuid.UUID,
        role: ProjectRole,
    ) -> int:
        """プロジェクトの特定ロールのメンバー数を取得します。

        最後のOWNER保護などのビジネスルールチェックに使用されます。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            role (ProjectRole): カウント対象のロール

        Returns:
            int: 指定されたロールのメンバー数

        Example:
            >>> owner_count = await member_repo.count_by_role(
            ...     project_id, ProjectRole.OWNER
            ... )
            >>> if owner_count <= 1:
            ...     raise ValidationError("Cannot remove last owner")
        """
        result = await self.db.execute(
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.role == role)
        )
        return result.scalar_one()

    async def get(self, id: uuid.UUID) -> ProjectMember | None:
        """UUIDによってプロジェクトメンバーを取得します。

        BaseRepositoryのget()メソッドをオーバーライドして、
        UUID型のIDに対応します。

        Args:
            id (uuid.UUID): メンバーシップのUUID

        Returns:
            ProjectMember | None: 該当するメンバーインスタンス、見つからない場合はNone

        Example:
            >>> member = await member_repo.get(member_id)
            >>> if member:
            ...     print(f"Found: {member.role}")
            ... else:
            ...     print("Member not found")
        """
        return await self.db.get(self.model, id)

    async def get_by_project_and_user(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectMember | None:
        """プロジェクトIDとユーザーIDでメンバーを検索します。

        このメソッドは、特定のユーザーが特定のプロジェクトのメンバーかどうかを
        確認する際に使用されます。(project_id, user_id)の組み合わせはUNIQUE制約により
        最大1件のみが返されます。

        クエリの最適化:
            - (project_id, user_id)にユニーク制約とインデックスが設定されているため高速です
            - scalar_one_or_none()により、0件または1件のみを保証

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Returns:
            ProjectMember | None: 該当するメンバーインスタンス、見つからない場合はNone
                - ProjectMember: プロジェクトとユーザーの組み合わせに一致するメンバー
                - None: 該当するメンバーが存在しない

        Example:
            >>> member = await member_repo.get_by_project_and_user(
            ...     project_id, user_id
            ... )
            >>> if member:
            ...     print(f"User role: {member.role}")
            ... else:
            ...     print("User is not a member")

        Note:
            - (project_id, user_id)はUNIQUE制約により重複しません
            - インデックスが設定されているため、検索は高速です
        """
        result = await self.db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_role(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectRole | None:
        """ユーザーのプロジェクトロールを取得します。

        権限チェックに使用されます。

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Returns:
            ProjectRole | None: ユーザーのロール、メンバーでない場合はNone

        Example:
            >>> role = await member_repo.get_user_role(project_id, user_id)
            >>> if role == ProjectRole.OWNER:
            ...     print("User is owner")
            >>> elif role is None:
            ...     print("User is not a member")
        """
        member = await self.get_by_project_and_user(project_id, user_id)
        return member.role if member else None

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProjectMember]:
        """プロジェクトのメンバー一覧を取得します（ユーザー情報付き）。

        このメソッドは、指定されたプロジェクトに所属するメンバー一覧を
        ユーザー情報と共に取得します。N+1クエリ問題を回避するため、
        selectinloadでユーザー情報を事前ロードします。

        クエリの最適化:
            - selectinload(ProjectMember.user)によりN+1クエリ問題を回避
            - project_idにインデックスが設定されているため高速

        Args:
            project_id (uuid.UUID): プロジェクトのUUID
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100

        Returns:
            list[ProjectMember]: メンバーのリスト（ユーザー情報付き）
                - joined_at降順でソートされます
                - 0件の場合は空のリストを返します
                - member.user でユーザー情報にアクセス可能

        Example:
            >>> members = await member_repo.list_by_project(
            ...     project_id, skip=0, limit=10
            ... )
            >>> for member in members:
            ...     print(f"{member.user.email}: {member.role}")

        Note:
            - selectinloadによりユーザー情報が事前ロードされます
            - N+1クエリ問題を回避するため、必ずこのメソッドを使用してください
        """
        query = (
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.joined_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProjectMember]:
        """ユーザーが所属するプロジェクトメンバーシップ一覧を取得します。

        このメソッドは、指定されたユーザーが所属するすべてのプロジェクトの
        メンバーシップ情報を取得します。

        Args:
            user_id (uuid.UUID): ユーザーのUUID
            skip (int): スキップするレコード数（オフセット）
                デフォルト: 0
            limit (int): 返す最大レコード数（ページサイズ）
                デフォルト: 100

        Returns:
            list[ProjectMember]: メンバーシップのリスト
                - joined_at降順でソートされます
                - 0件の場合は空のリストを返します

        Example:
            >>> memberships = await member_repo.list_by_user(
            ...     user_id, skip=0, limit=10
            ... )
            >>> print(f"User's projects: {len(memberships)}")

        Note:
            - user_idにインデックスが設定されているため検索は高速です
        """
        query = (
            select(ProjectMember)
            .where(ProjectMember.user_id == user_id)
            .order_by(ProjectMember.joined_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_role(
        self,
        member_id: uuid.UUID,
        role: ProjectRole,
    ) -> ProjectMember | None:
        """メンバーのロールを更新します。

        このメソッドは、指定されたメンバーのロールを更新します。
        ビジネスロジック（最後のOWNER保護など）は、Service層で実装されます。

        Args:
            member_id (uuid.UUID): メンバーシップのUUID
            role (ProjectRole): 新しいロール

        Returns:
            ProjectMember | None: 更新されたメンバーインスタンス、見つからない場合はNone

        Example:
            >>> updated = await member_repo.update_role(
            ...     member_id, ProjectRole.ADMIN
            ... )
            >>> if updated:
            ...     await db.commit()
            ...     print(f"Updated role to: {updated.role}")

        Note:
            - flush()のみ実行し、commit()は呼び出し側の責任です
            - ビジネスルール（最後のOWNER保護）はService層で実装
        """
        member = await self.get(member_id)
        if not member:
            return None

        member.role = role
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def delete(self, id: uuid.UUID) -> bool:
        """プロジェクトメンバーを削除します。

        BaseRepositoryのdelete()メソッドをオーバーライドして、
        UUID型のIDに対応します。

        Args:
            id (uuid.UUID): 削除するメンバーシップのUUID

        Returns:
            bool: 削除が成功した場合はTrue、レコードが見つからない場合はFalse

        Example:
            >>> success = await member_repo.delete(member_id)
            >>> if success:
            ...     await db.commit()
            ...     print("Member deleted")
            ... else:
            ...     print("Member not found")

        Note:
            - flush()のみ実行し、commit()は呼び出し側の責任です
        """
        member = await self.get(id)
        if member:
            await self.db.delete(member)
            await self.db.flush()
            return True
        return False
