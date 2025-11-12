"""Projectモデルのテスト。

このテストファイルは MODEL_TEST_POLICY.md に従い、
データ整合性に関わる制約テストのみを実施します。

基本的なCRUD操作はリポジトリ層・サービス層のテストでカバーされます。
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.project.file import ProjectFile
from app.models.project.member import ProjectMember, ProjectRole
from app.models.project.project import Project
from app.models.user.user import User


@pytest.mark.asyncio
async def test_project_unique_code(db_session):
    """プロジェクトコードの一意性制約テスト。

    同じコードを持つプロジェクトを複数作成できないことを確認します。
    これはプロジェクト識別の整合性に関わる重要な制約です。
    """
    # Arrange
    project1 = Project(
        name="Project 1",
        code="UNIQUE-001",
        description="First project",
    )
    db_session.add(project1)
    await db_session.commit()

    # Act & Assert - 同じコードで作成しようとするとエラー
    project2 = Project(
        name="Project 2",
        code="UNIQUE-001",  # 同じコード
        description="Second project",
    )
    db_session.add(project2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_member_unique_constraint(db_session):
    """プロジェクトメンバーの一意性制約テスト（同じユーザーを2回追加不可）。

    同じユーザーを同じプロジェクトに複数回追加できないことを確認します。
    これはメンバーシップの整合性に関わる重要な制約です。
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

    # 1回目の追加
    member1 = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
        joined_at=datetime.now(UTC),
    )
    db_session.add(member1)
    await db_session.commit()

    # Act & Assert - 同じユーザーを再度追加しようとするとエラー
    member2 = ProjectMember(
        project_id=project.id,
        user_id=user.id,  # 同じユーザー
        role=ProjectRole.PROJECT_MANAGER,
        joined_at=datetime.now(UTC),
    )
    db_session.add(member2)

    with pytest.raises(IntegrityError):  # UNIQUE constraint
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_cascade_delete_members(db_session):
    """プロジェクト削除時のメンバー連鎖削除テスト。

    プロジェクトが削除されたとき、関連するメンバーも自動削除されることを確認します。
    これはCASCADE制約の動作確認であり、孤立レコードを防ぐ重要なテストです。
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

    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER,
        joined_at=datetime.now(UTC),
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    member_id = member.id

    # Act - プロジェクトを削除
    await db_session.delete(project)
    await db_session.commit()

    # Assert - メンバーも削除される（CASCADE）
    result = await db_session.execute(select(ProjectMember).where(ProjectMember.id == member_id))
    deleted_member = result.scalar_one_or_none()
    assert deleted_member is None


@pytest.mark.asyncio
async def test_project_cascade_delete_files(db_session):
    """プロジェクト削除時のファイル連鎖削除テスト。

    プロジェクトが削除されたとき、関連するファイルも自動削除されることを確認します。
    これはCASCADE制約の動作確認であり、孤立レコードを防ぐ重要なテストです。
    """
    # Arrange
    user = User(
        azure_oid="file-cascade-oid",
        email="filecascade@company.com",
        display_name="File Cascade User",
    )
    project = Project(
        name="File Cascade Project",
        code="FILECASCADE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    file = ProjectFile(
        project_id=project.id,
        filename="test.pdf",
        original_filename="test.pdf",
        file_path="projects/test.pdf",
        file_size=1000,
        mime_type="application/pdf",
        uploaded_by=user.id,
        uploaded_at=datetime.now(UTC),
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)

    file_id = file.id

    # Act - プロジェクトを削除
    await db_session.delete(project)
    await db_session.commit()

    # Assert - ファイルも削除される（CASCADE）
    result = await db_session.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    deleted_file = result.scalar_one_or_none()
    assert deleted_file is None
