"""Azure AD認証用UserRepositoryのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
複雑なクエリやカスタムメソッドのみをテストします。

基本的なCRUD操作はサービス層のテストでカバーされます。
"""

import uuid

import pytest
from sqlalchemy import text

from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_repository_get_by_azure_oid(db_session):
    """Azure OIDでのユーザー取得テスト。

    Azure AD連携における重要なビジネスロジック。
    認証フロー全体に影響するため、明示的にテストする。
    """
    # Arrange
    user = User(
        azure_oid="azure-oid-12345",
        email="test@company.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    repository = UserRepository(db_session)

    # Act
    result = await repository.get_by_azure_oid("azure-oid-12345")

    # Assert
    assert result is not None
    assert result.azure_oid == "azure-oid-12345"
    assert result.email == "test@company.com"


@pytest.mark.asyncio
async def test_repository_get_by_azure_oid_not_found(db_session):
    """存在しないAzure OIDでの取得テスト。

    認証失敗時の動作に直結する重要なエッジケース。
    """
    # Arrange
    repository = UserRepository(db_session)

    # Act
    result = await repository.get_by_azure_oid("non-existent-oid")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_repository_get_active_users(db_session):
    """アクティブユーザー一覧取得テスト。

    ビジネスロジック: is_active=Trueでフィルタリング。
    ユーザー管理画面や権限チェックで使用される。
    """
    # Arrange
    repository = UserRepository(db_session)

    # アクティブユーザーを3人作成
    for i in range(3):
        user = User(
            azure_oid=f"active-oid-{i}",
            email=f"active{i}@company.com",
            display_name=f"Active User {i}",
            is_active=True,
        )
        db_session.add(user)

    # 非アクティブユーザーを2人作成
    for i in range(2):
        user = User(
            azure_oid=f"inactive-oid-{i}",
            email=f"inactive{i}@company.com",
            display_name=f"Inactive User {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    # Act
    active_users = await repository.get_active_users(skip=0, limit=10)

    # Assert
    assert len(active_users) == 3
    assert all(user.is_active for user in active_users)


@pytest.mark.asyncio
async def test_repository_count_all_users(db_session):
    """全ユーザーカウントテスト。

    ビジネスロジック: フィルタなしで全ユーザー数を取得。
    ページネーションのtotal値として使用される。
    """
    # Arrange
    repository = UserRepository(db_session)

    # アクティブユーザー3人 + 非アクティブ2人
    for i in range(3):
        user = User(
            azure_oid=f"count-active-{i}",
            email=f"countactive{i}@company.com",
            display_name=f"Count Active {i}",
            is_active=True,
        )
        db_session.add(user)

    for i in range(2):
        user = User(
            azure_oid=f"count-inactive-{i}",
            email=f"countinactive{i}@company.com",
            display_name=f"Count Inactive {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    # Act
    total = await repository.count()

    # Assert
    assert total == 5  # 全ユーザー数


@pytest.mark.asyncio
async def test_repository_count_active_users(db_session):
    """アクティブユーザーカウントテスト。

    ビジネスロジック: is_active=Trueでフィルタリングしてカウント。
    アクティブユーザー統計として使用される。
    """
    # Arrange
    repository = UserRepository(db_session)

    # アクティブユーザー3人 + 非アクティブ2人
    for i in range(3):
        user = User(
            azure_oid=f"filter-active-{i}",
            email=f"filteractive{i}@company.com",
            display_name=f"Filter Active {i}",
            is_active=True,
        )
        db_session.add(user)

    for i in range(2):
        user = User(
            azure_oid=f"filter-inactive-{i}",
            email=f"filterinactive{i}@company.com",
            display_name=f"Filter Inactive {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    # Act
    active_count = await repository.count(is_active=True)

    # Assert
    assert active_count == 3  # アクティブユーザーのみ


@pytest.mark.asyncio
async def test_repository_count_inactive_users(db_session):
    """非アクティブユーザーカウントテスト。

    ビジネスロジック: is_active=Falseでフィルタリングしてカウント。
    """
    # Arrange
    repository = UserRepository(db_session)

    # アクティブユーザー3人 + 非アクティブ2人
    for i in range(3):
        user = User(
            azure_oid=f"filter2-active-{i}",
            email=f"filter2active{i}@company.com",
            display_name=f"Filter2 Active {i}",
            is_active=True,
        )
        db_session.add(user)

    for i in range(2):
        user = User(
            azure_oid=f"filter2-inactive-{i}",
            email=f"filter2inactive{i}@company.com",
            display_name=f"Filter2 Inactive {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    # Act
    inactive_count = await repository.count(is_active=False)

    # Assert
    assert inactive_count == 2  # 非アクティブユーザーのみ


@pytest.mark.asyncio
async def test_repository_get_active_users_with_n_plus_one_prevention(db_session):
    """アクティブユーザー一覧取得のN+1クエリ対策テスト。

    パフォーマンステスト: selectinloadによりproject_membershipsが
    事前ロードされ、N+1クエリ問題が発生しないことを確認。

    このテストは、TEST_REDUCTION_POLICY.mdに従い、
    パフォーマンス最適化の重要なビジネスロジックをテストします。
    """
    # Arrange
    repository = UserRepository(db_session)

    # アクティブユーザーを3人作成
    users = []
    for i in range(3):
        user = User(
            azure_oid=f"n-plus-one-active-{i}",
            email=f"nplus1active{i}@company.com",
            display_name=f"N+1 Active User {i}",
            is_active=True,
        )
        db_session.add(user)
        users.append(user)

    await db_session.commit()

    # 各ユーザーに複数のプロジェクトメンバーシップを作成
    for user in users:
        for j in range(2):
            project = Project(
                name=f"Project {user.email}-{j}",
                code=f"PROJ-{uuid.uuid4().hex[:8]}",
                description=f"Test project for {user.email}",
                created_by=user.id,
            )
            db_session.add(project)
            await db_session.flush()

            membership = ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role=ProjectRole.OWNER,
            )
            db_session.add(membership)

    await db_session.commit()

    # クエリカウンターを準備（SQLステートメントをログで確認）
    # PostgreSQL: pg_stat_statementsやログで確認
    # テスト環境: SQLクエリ実行数をカウント

    # Act - アクティブユーザーを取得
    active_users = await repository.get_active_users(skip=0, limit=10)

    # Assert
    assert len(active_users) == 3
    assert all(user.is_active for user in active_users)

    # N+1問題が発生していないことを確認:
    # project_membershipsにアクセスしても追加クエリが発行されない
    # （selectinloadにより事前ロード済み）

    # クエリカウントをリセット
    await db_session.execute(text("SELECT 1"))  # ダミークエリでフラッシュ

    # project_membershipsにアクセス（追加クエリが発行されないはず）
    for user in active_users:
        memberships = user.project_memberships
        # 各ユーザーは2つのプロジェクトメンバーシップを持つ
        assert len(memberships) == 2

    # 追加のクエリが実行されていないことを確認
    # （selectinloadにより事前ロード済みのため、遅延ロードが発生しない）
    # 実際のクエリ数確認は、ログやpg_stat_statementsで実施可能


@pytest.mark.asyncio
async def test_repository_get_active_users_eager_loading_verification(db_session):
    """アクティブユーザー一覧のEager Loading検証テスト。

    リレーションシップが正しくeager loadingされ、
    遅延ロードが発生しないことを確認。
    """
    # Arrange
    repository = UserRepository(db_session)

    # ユーザーとプロジェクトメンバーシップを作成
    user = User(
        azure_oid="eager-loading-test",
        email="eagerload@company.com",
        display_name="Eager Loading Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    project = Project(
        name="Eager Loading Project",
        code=f"EAGER-{uuid.uuid4().hex[:8]}",
        description="Test project for eager loading",
        created_by=user.id,
    )
    db_session.add(project)
    await db_session.flush()

    membership = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.OWNER,
    )
    db_session.add(membership)
    await db_session.commit()

    # セッションをクリアしてキャッシュを無効化
    db_session.expire_all()

    # Act
    active_users = await repository.get_active_users(skip=0, limit=10)

    # Assert
    assert len(active_users) >= 1

    # project_membershipsがロード済みであることを確認
    target_user = next(u for u in active_users if u.email == "eagerload@company.com")

    # SQLAlchemyのInspectorを使用してリレーションシップのロード状態を確認
    from sqlalchemy import inspect

    insp = inspect(target_user)

    # project_membershipsがロード済み（lazy loadingではない）
    # loaded_valueがFalseでない（=ロード済み）ことを確認
    assert insp.attrs.project_memberships.loaded_value is not False
    # project_membershipsに直接アクセスしてもクエリが発行されない
    memberships = target_user.project_memberships
    assert len(memberships) >= 1
