"""分析セッションリポジトリのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
複雑なクエリやカスタムメソッドのみをテストします。

基本的なCRUD操作はサービス層のテストでカバーされます。
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalysisFile, AnalysisSession, AnalysisStep
from app.repositories import AnalysisSessionRepository


@pytest.mark.asyncio
async def test_get_with_relations(db_session: AsyncSession, test_user, test_project):
    """リレーション付きセッション取得のテスト。

    カスタムクエリ: selectinloadによる関連データの一括取得。
    N+1問題を防ぐために使用される。
    """
    # Arrange
    repo = AnalysisSessionRepository(db_session)
    user_id = test_user.id
    project_id = test_project.id

    # セッションを作成
    session = AnalysisSession(
        project_id=project_id,
        created_by=user_id,
        validation_config={"test": "config"},
        chat_history=[],
        snapshot_history=[],
    )
    db_session.add(session)
    await db_session.flush()

    # ステップを追加
    step1 = AnalysisStep(
        session_id=session.id,
        step_name="データプロファイリング",
        step_type="data_profiling",
        step_order=1,
        config={},
    )
    step2 = AnalysisStep(
        session_id=session.id,
        step_name="仮説生成",
        step_type="hypothesis_generation",
        step_order=2,
        config={},
    )
    db_session.add(step1)
    db_session.add(step2)

    # ファイルを追加
    file1 = AnalysisFile(
        session_id=session.id,
        file_name="test1.csv",
        storage_path="/test/path1",
        file_size=1024,
        content_type="text/csv",
        table_name="test_table1",
        table_axis=["col1"],
        uploaded_by=user_id,
    )
    file2 = AnalysisFile(
        session_id=session.id,
        file_name="test2.csv",
        storage_path="/test/path2",
        file_size=2048,
        content_type="text/csv",
        table_name="test_table2",
        table_axis=["col2"],
        uploaded_by=user_id,
    )
    db_session.add(file1)
    db_session.add(file2)
    await db_session.commit()

    # Act
    result = await repo.get_with_relations(session.id)

    # Assert
    assert result is not None
    assert result.id == session.id
    assert len(result.steps) == 2
    assert len(result.files) == 2

    # ステップがstep_orderでソートされていることを確認
    assert result.steps[0].step_order == 1
    assert result.steps[1].step_order == 2


@pytest.mark.asyncio
async def test_get_with_relations_not_found(db_session: AsyncSession):
    """存在しないセッションIDでの取得テスト。"""
    # Arrange
    repo = AnalysisSessionRepository(db_session)
    nonexistent_id = uuid.uuid4()

    # Act
    result = await repo.get_with_relations(nonexistent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_list_by_user(db_session: AsyncSession, test_user, test_project):
    """ユーザー別セッション一覧取得のテスト。

    カスタムクエリ: ユーザーIDでのフィルタリング。
    ユーザーの分析履歴表示に使用される。
    """
    # Arrange
    repo = AnalysisSessionRepository(db_session)
    user1_id = test_user.id
    project_id = test_project.id

    # ユーザー2を作成
    from app.models import User

    user2 = User(
        azure_oid="test-user2-oid",
        email="user2@example.com",
        display_name="Test User 2",
    )
    db_session.add(user2)
    await db_session.flush()
    user2_id = user2.id

    # ユーザー1のセッションを作成
    session1 = AnalysisSession(
        project_id=project_id,
        created_by=user1_id,
        validation_config={},
        chat_history=[],
        snapshot_history=[],
    )
    session2 = AnalysisSession(
        project_id=project_id,
        created_by=user1_id,
        validation_config={},
        chat_history=[],
        snapshot_history=[],
    )

    # ユーザー2のセッションを作成
    session3 = AnalysisSession(
        project_id=project_id,
        created_by=user2_id,
        validation_config={},
        chat_history=[],
        snapshot_history=[],
    )

    db_session.add(session1)
    db_session.add(session2)
    db_session.add(session3)
    await db_session.commit()

    # Act
    result = await repo.list_by_user(user1_id)

    # Assert
    assert len(result) == 2
    assert all(s.created_by == user1_id for s in result)


@pytest.mark.asyncio
async def test_list_by_user_with_pagination(db_session: AsyncSession, test_user, test_project):
    """ページネーション付きユーザー別セッション取得のテスト。

    ビジネスロジック: skip/limit によるページング。
    大量のセッションがある場合のパフォーマンス対策。
    """
    # Arrange
    repo = AnalysisSessionRepository(db_session)
    user_id = test_user.id
    project_id = test_project.id

    # 5つのセッションを作成
    for i in range(5):
        session = AnalysisSession(
            project_id=project_id,
            created_by=user_id,
            validation_config={"index": i},
            chat_history=[],
            snapshot_history=[],
        )
        db_session.add(session)

    await db_session.commit()

    # Act - 最初の2件を取得
    result = await repo.list_by_user(user_id, skip=0, limit=2)

    # Assert
    assert len(result) == 2


@pytest.mark.asyncio
async def test_delete_with_cascade(db_session: AsyncSession, test_user, test_project):
    """カスケード削除のテスト。

    ビジネスロジック: セッション削除時に関連するステップとファイルも削除。
    データ整合性を保つための重要な機能。
    """
    # Arrange
    repo = AnalysisSessionRepository(db_session)
    user_id = test_user.id
    project_id = test_project.id

    # セッションを作成
    session = AnalysisSession(
        project_id=project_id,
        created_by=user_id,
        validation_config={},
        chat_history=[],
        snapshot_history=[],
    )
    db_session.add(session)
    await db_session.flush()

    # ステップを追加
    step = AnalysisStep(
        session_id=session.id,
        step_name="データプロファイリング",
        step_type="data_profiling",
        step_order=1,
        config={},
    )
    db_session.add(step)

    # ファイルを追加
    file = AnalysisFile(
        session_id=session.id,
        file_name="test.csv",
        storage_path="/test/path",
        file_size=1024,
        content_type="text/csv",
        table_name="test_table",
        table_axis=["col1"],
        uploaded_by=user_id,
    )
    db_session.add(file)
    await db_session.commit()

    session_id = session.id

    # Act
    await repo.delete(session_id)
    await db_session.commit()

    # Assert
    deleted_session = await repo.get(session_id)
    assert deleted_session is None

    # 関連データも削除されていることを確認
    from sqlalchemy import select

    step_result = await db_session.execute(select(AnalysisStep).where(AnalysisStep.session_id == session_id))
    assert step_result.scalar_one_or_none() is None

    file_result = await db_session.execute(select(AnalysisFile).where(AnalysisFile.session_id == session_id))
    assert file_result.scalar_one_or_none() is None
