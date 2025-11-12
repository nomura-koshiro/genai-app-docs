"""プロジェクトリポジトリのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
複雑なクエリやカスタムメソッドのみをテストします。

基本的なCRUD操作はサービス層のテストでカバーされます。
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProjectMember, ProjectRole, User
from app.repositories import ProjectRepository


@pytest.mark.asyncio
async def test_list_by_user(db_session: AsyncSession):
    """ユーザーのプロジェクト一覧取得。

    カスタムクエリ: ProjectMember経由でのJOIN取得。
    ユーザーがアクセス可能なプロジェクト一覧の表示に使用される。
    """
    # Arrange
    repo = ProjectRepository(db_session)
    user_id = uuid.uuid4()

    # ユーザーモデルを作成（ProjectMemberの外部キー制約のため）
    user = User(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"user-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # プロジェクトを作成
    project1 = await repo.create(
        name="User Project 1",
        code=f"UP1-{uuid.uuid4().hex[:6]}",
        description="User project 1",
        created_by=user_id,
    )
    project2 = await repo.create(
        name="User Project 2",
        code=f"UP2-{uuid.uuid4().hex[:6]}",
        description="User project 2",
        created_by=user_id,
    )

    # メンバーとして追加
    member1 = ProjectMember(
        project_id=project1.id,
        user_id=user_id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    member2 = ProjectMember(
        project_id=project2.id,
        user_id=user_id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member1)
    db_session.add(member2)
    await db_session.commit()

    # Act
    result = await repo.list_by_user(user_id)

    # Assert
    assert len(result) == 2
    project_codes = [p.code for p in result]
    assert project1.code in project_codes
    assert project2.code in project_codes


@pytest.mark.asyncio
async def test_list_by_user_with_active_filter(db_session: AsyncSession):
    """アクティブフィルタ付きでユーザーのプロジェクト一覧取得。

    ビジネスロジック: is_active=Trueでフィルタリング。
    アーカイブされたプロジェクトを除外する重要な機能。
    """
    # Arrange
    repo = ProjectRepository(db_session)
    user_id = uuid.uuid4()

    # ユーザーモデルを作成
    user = User(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"user-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # アクティブなプロジェクトを作成
    active_project = await repo.create(
        name="Active Project",
        code=f"ACTIVE-{uuid.uuid4().hex[:6]}",
        description="Active project",
        created_by=user_id,
        is_active=True,
    )

    # 非アクティブなプロジェクトを作成
    inactive_project = await repo.create(
        name="Inactive Project",
        code=f"INACTIVE-{uuid.uuid4().hex[:6]}",
        description="Inactive project",
        created_by=user_id,
        is_active=False,
    )

    # メンバーとして追加
    member1 = ProjectMember(
        project_id=active_project.id,
        user_id=user_id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    member2 = ProjectMember(
        project_id=inactive_project.id,
        user_id=user_id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(member1)
    db_session.add(member2)
    await db_session.commit()

    # Act - アクティブなプロジェクトのみ取得
    active_results = await repo.list_by_user(user_id, is_active=True)

    # Assert
    assert len(active_results) == 1
    assert active_results[0].code == active_project.code
    assert active_results[0].is_active is True


@pytest.mark.asyncio
async def test_get_active_projects(db_session: AsyncSession):
    """アクティブプロジェクト一覧取得。

    ビジネスロジック: is_active=Trueのプロジェクトのみ取得。
    管理画面やダッシュボードで使用される。
    """
    # Arrange
    repo = ProjectRepository(db_session)

    # アクティブなプロジェクトを作成
    await repo.create(
        name="Active",
        code=f"ACT-{uuid.uuid4().hex[:6]}",
        description="Active",
        created_by=uuid.uuid4(),
        is_active=True,
    )

    # 非アクティブなプロジェクトを作成
    await repo.create(
        name="Inactive",
        code=f"INA-{uuid.uuid4().hex[:6]}",
        description="Inactive",
        created_by=uuid.uuid4(),
        is_active=False,
    )
    await db_session.commit()

    # Act
    result = await repo.get_active_projects()

    # Assert
    assert len(result) >= 1
    assert all(p.is_active for p in result)


@pytest.mark.asyncio
async def test_count_by_user(db_session: AsyncSession):
    """ユーザーのプロジェクト数カウント。

    カスタムクエリ: ProjectMember経由でのCOUNT集計。
    ユーザーダッシュボードでの統計表示に使用される。
    """
    # Arrange
    repo = ProjectRepository(db_session)
    user_id = uuid.uuid4()

    # ユーザーモデルを作成
    user = User(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"user-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # プロジェクトを作成
    project1 = await repo.create(
        name="Count Project 1",
        code=f"CNT1-{uuid.uuid4().hex[:6]}",
        description="Count project 1",
        created_by=user_id,
    )
    project2 = await repo.create(
        name="Count Project 2",
        code=f"CNT2-{uuid.uuid4().hex[:6]}",
        description="Count project 2",
        created_by=user_id,
    )

    # メンバーとして追加
    member1 = ProjectMember(
        project_id=project1.id,
        user_id=user_id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    member2 = ProjectMember(
        project_id=project2.id,
        user_id=user_id,
        role=ProjectRole.MEMBER,
    )
    db_session.add(member1)
    db_session.add(member2)
    await db_session.commit()

    # Act
    count = await repo.count_by_user(user_id)

    # Assert
    assert count == 2
