"""ProjectMemberモデルのテスト。

このテストファイルは MODEL_TEST_POLICY.md に従い、
データ整合性に関わる制約テストのみを実施します。

基本的なCRUD操作はリポジトリ層・サービス層のテストでカバーされます。
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User


@pytest.mark.asyncio
async def test_project_member_unique_constraint(db_session):
    """(project_id, user_id)の複合一意性制約を確認。

    同一プロジェクト内で同じユーザーを複数回メンバーに追加することを防ぎます。
    これはデータ整合性に直結する制約です。
    """
    # Arrange
    user = User(
        azure_oid="unique-member-oid",
        email="unique@company.com",
        display_name="Unique User",
    )
    project = Project(
        name="Unique Project",
        code="UNIQUE-002",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # 最初のメンバーを追加
    member1 = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member1)
    await db_session.commit()

    # Act & Assert - 同じproject_id, user_idで作成しようとするとエラー
    member2 = ProjectMember(
        project_id=project.id,
        user_id=user.id,  # 同じユーザー
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(member2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_member_cascade_delete_project(db_session):
    """プロジェクト削除時にメンバーもカスケード削除されることを確認。

    プロジェクトが削除される際、そのプロジェクトに属するすべてのメンバーも
    自動的に削除されることでデータ整合性を保証します。
    """
    # Arrange
    user = User(
        azure_oid="cascade-oid",
        email="cascade@company.com",
        display_name="Cascade User",
    )
    project = Project(
        name="Cascade Project",
        code="CASCADE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # メンバーを追加
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member)
    await db_session.commit()
    member_id = member.id

    # Act - プロジェクトを削除
    await db_session.delete(project)
    await db_session.commit()

    # Assert - メンバーも削除されているはず（CASCADE）
    result = await db_session.execute(select(ProjectMember).where(ProjectMember.id == member_id))
    deleted_member = result.scalar_one_or_none()
    assert deleted_member is None


@pytest.mark.asyncio
async def test_project_member_cascade_delete_user(db_session):
    """ユーザー削除時にメンバーもカスケード削除されることを確認。

    ユーザーが削除される際、そのユーザーに関連するすべてのメンバーシップも
    自動的に削除されることでデータ整合性を保証します。
    """
    # Arrange
    user = User(
        azure_oid="user-cascade-oid",
        email="user-cascade@company.com",
        display_name="User Cascade User",
    )
    project = Project(
        name="User Cascade Project",
        code="USER-CASCADE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # メンバーを追加
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member)
    await db_session.commit()
    member_id = member.id

    # Act - ユーザーを削除
    await db_session.delete(user)
    await db_session.commit()

    # Assert - メンバーも削除されているはず（CASCADE）
    result = await db_session.execute(select(ProjectMember).where(ProjectMember.id == member_id))
    deleted_member = result.scalar_one_or_none()
    assert deleted_member is None


@pytest.mark.asyncio
async def test_project_member_added_by(db_session):
    """added_byフィールド設定の確認。

    メンバー追加時に追加者のユーザーIDを記録することで、
    監査ログとしての機能を提供します。
    """
    # Arrange
    owner = User(
        azure_oid="owner-oid",
        email="owner@company.com",
        display_name="Owner User",
    )
    member_user = User(
        azure_oid="added-member-oid",
        email="added-member@company.com",
        display_name="Added Member User",
    )
    project = Project(
        name="Added By Project",
        code="ADDED-BY-001",
    )
    db_session.add(owner)
    db_session.add(member_user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(member_user)
    await db_session.refresh(project)

    # Act - ownerがmember_userを追加
    member = ProjectMember(
        project_id=project.id,
        user_id=member_user.id,
        role=ProjectRole.MEMBER,
        added_by=owner.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    # Assert
    assert member.added_by == owner.id


@pytest.mark.asyncio
async def test_project_member_added_by_set_null(db_session):
    """追加者削除時にadded_byがNULLになることを確認。

    メンバー追加者が削除されても、メンバーレコード自体は保持し、
    added_byのみNULLにすることで、メンバーシップを維持しながら
    追加者情報を適切に処理します。
    """
    # Arrange
    admin = User(
        azure_oid="admin-oid",
        email="admin@company.com",
        display_name="Admin User",
    )
    member_user = User(
        azure_oid="member-oid",
        email="member2@company.com",
        display_name="Member User",
    )
    project = Project(
        name="Set Null Project",
        code="SET-NULL-001",
    )
    db_session.add(admin)
    db_session.add(member_user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(member_user)
    await db_session.refresh(project)

    # adminがmember_userを追加
    member = ProjectMember(
        project_id=project.id,
        user_id=member_user.id,
        role=ProjectRole.MEMBER,
        added_by=admin.id,
    )
    db_session.add(member)
    await db_session.commit()
    member_id = member.id

    # Act - adminを削除
    await db_session.delete(admin)
    await db_session.commit()

    # Assert - memberのadded_byがNULLになっているはず（SET NULL）
    # 最新の状態を取得するため、セッションをリフレッシュ
    db_session.expire_all()
    result = await db_session.execute(select(ProjectMember).where(ProjectMember.id == member_id))
    updated_member = result.scalar_one_or_none()
    assert updated_member is not None
    assert updated_member.added_by is None
