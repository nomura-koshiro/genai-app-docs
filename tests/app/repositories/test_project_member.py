"""ProjectMemberRepositoryのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
複雑なクエリやカスタムメソッドのみをテストします。

基本的なCRUD操作はサービス層のテストでカバーされます。
"""

import pytest

from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.repositories.project_member import ProjectMemberRepository

@pytest.fixture
async def test_users(db_session):
    """テスト用ユーザーを作成。"""
    users = [
        User(
            azure_oid=f"test-oid-{i}",
            email=f"user{i}@company.com",
            display_name=f"User {i}",
        )
        for i in range(5)
    ]
    for user in users:
        db_session.add(user)
    await db_session.commit()
    for user in users:
        await db_session.refresh(user)
    return users


@pytest.fixture
async def test_project(db_session):
    """テスト用プロジェクトを作成。"""
    project = Project(
        name="Test Project",
        code="TEST-REPO-001",
        description="Test project for repository tests",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_get_by_project_and_user(db_session, test_project, test_users):
    """プロジェクト+ユーザーでメンバー検索のテスト。

    カスタムクエリ: 複合キー（project_id + user_id）での検索。
    メンバーシップの存在確認や権限チェックで使用される。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)
    member = ProjectMember(
        project_id=test_project.id,
        user_id=test_users[0].id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(member)
    await db_session.commit()

    # Act
    found_member = await repo.get_by_project_and_user(test_project.id, test_users[0].id)

    # Assert
    assert found_member is not None
    assert found_member.project_id == test_project.id
    assert found_member.user_id == test_users[0].id
    assert found_member.role == ProjectRole.PROJECT_MANAGER


@pytest.mark.asyncio
async def test_list_by_project(db_session, test_project, test_users):
    """プロジェクトメンバー一覧取得のテスト。

    カスタムクエリ: プロジェクト別メンバー一覧 + joined_at降順ソート。
    メンバー管理画面で使用される。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)

    # 複数のメンバーを追加
    for i, user in enumerate(test_users[:3]):
        member = ProjectMember(
            project_id=test_project.id,
            user_id=user.id,
            role=ProjectRole.PROJECT_MANAGER if i == 0 else ProjectRole.MEMBER,
        )
        db_session.add(member)
    await db_session.commit()

    # Act
    members = await repo.list_by_project(test_project.id)

    # Assert
    assert len(members) == 3
    assert all(m.project_id == test_project.id for m in members)
    # joined_at降順でソートされているか確認
    for i in range(len(members) - 1):
        assert members[i].joined_at >= members[i + 1].joined_at


@pytest.mark.asyncio
async def test_list_by_user(db_session, test_project, test_users):
    """ユーザーのプロジェクト一覧取得のテスト。

    カスタムクエリ: ユーザー別のプロジェクトメンバーシップ一覧。
    ユーザーがアクセス可能なプロジェクトの取得に使用される。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)

    # 複数のプロジェクトを作成
    projects = []
    for i in range(3):
        project = Project(
            name=f"Project {i}",
            code=f"USER-PROJ-{i}",
        )
        db_session.add(project)
        await db_session.flush()
        projects.append(project)

    # test_users[0]を全プロジェクトに追加
    for project in projects:
        member = ProjectMember(
            project_id=project.id,
            user_id=test_users[0].id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
    await db_session.commit()

    # Act
    memberships = await repo.list_by_user(test_users[0].id)

    # Assert
    assert len(memberships) == 3
    assert all(m.user_id == test_users[0].id for m in memberships)


@pytest.mark.asyncio
async def test_count_by_project(db_session, test_project, test_users):
    """プロジェクトメンバー数カウントのテスト。

    カスタムクエリ: プロジェクト別メンバー数のCOUNT集計。
    プロジェクト情報表示やダッシュボードで使用される。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)

    # 3人のメンバーを追加
    for user in test_users[:3]:
        member = ProjectMember(
            project_id=test_project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
    await db_session.commit()

    # Act
    count = await repo.count_by_project(test_project.id)

    # Assert
    assert count == 3


@pytest.mark.asyncio
async def test_count_by_role(db_session, test_project, test_users):
    """特定ロールのメンバー数カウントのテスト。

    カスタムクエリ: ロール別メンバー数のCOUNT集計。
    プロジェクトのオーナー数確認など、権限管理で使用される。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)

    # 1人のOWNER、2人のMEMBERを追加
    member1 = ProjectMember(
        project_id=test_project.id,
        user_id=test_users[0].id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    member2 = ProjectMember(
        project_id=test_project.id,
        user_id=test_users[1].id,
        role=ProjectRole.MEMBER,
    )
    member3 = ProjectMember(
        project_id=test_project.id,
        user_id=test_users[2].id,
        role=ProjectRole.MEMBER,
    )
    db_session.add_all([member1, member2, member3])
    await db_session.commit()

    # Act
    owner_count = await repo.count_by_role(test_project.id, ProjectRole.PROJECT_MANAGER)
    member_count = await repo.count_by_role(test_project.id, ProjectRole.MEMBER)

    # Assert
    assert owner_count == 1
    assert member_count == 2


@pytest.mark.asyncio
async def test_get_user_role(db_session, test_project, test_users):
    """ユーザーロール取得のテスト。

    ビジネスロジック: ユーザーのプロジェクト内権限を取得。
    アクセス制御や操作権限チェックで使用される重要な機能。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)
    member = ProjectMember(
        project_id=test_project.id,
        user_id=test_users[0].id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(member)
    await db_session.commit()

    # Act
    role = await repo.get_user_role(test_project.id, test_users[0].id)

    # Assert
    assert role == ProjectRole.PROJECT_MANAGER


@pytest.mark.asyncio
async def test_get_user_role_not_member(db_session, test_project, test_users):
    """メンバーでないユーザーのロール取得テスト。

    ビジネスロジック: メンバーでない場合はNoneを返す。
    アクセス拒否の判定に使用される重要なエッジケース。
    """
    # Arrange
    repo = ProjectMemberRepository(db_session)

    # Act
    role = await repo.get_user_role(test_project.id, test_users[0].id)

    # Assert
    assert role is None
