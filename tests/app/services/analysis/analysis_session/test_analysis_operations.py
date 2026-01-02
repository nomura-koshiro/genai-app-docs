"""分析操作サービスのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.analysis.analysis_session.analysis_operations import (
    AnalysisSessionAnalysisService,
)


@pytest.mark.asyncio
async def test_get_session_result_success(db_session: AsyncSession):
    """[test_analysis_operations-001] 分析結果取得の成功ケース。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.project_id = project_id
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 0

    mock_snapshot = MagicMock()
    mock_snapshot.id = uuid.uuid4()

    with (
        patch.object(
            service.session_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.snapshot_repository,
            "get_by_order",
            new_callable=AsyncMock,
            return_value=mock_snapshot,
        ),
        patch.object(
            service.step_repository,
            "get_summary_steps",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        # Act
        result = await service.get_session_result(project_id, session_id)

        # Assert
        assert result is not None
        assert result.results == []
        assert result.total == 0


@pytest.mark.parametrize(
    "method_name,args,mock_setup",
    [
        (
            "get_session_result",
            ["project_id", "session_id"],
            [("session_repository", "get", None)],
        ),
        (
            "get_chat_messages",
            ["project_id", "session_id"],
            [("session_repository", "get", None)],
        ),
        (
            "delete_chat_message",
            ["project_id", "session_id", "chat_id"],
            [("session_repository", "get", None)],
        ),
    ],
    ids=["get_session_result", "get_chat_messages", "delete_chat_message"],
)
@pytest.mark.asyncio
async def test_session_not_found_error(
    db_session: AsyncSession,
    method_name: str,
    args: list,
    mock_setup: list,
):
    """[test_analysis_operations-002] セッションが見つからない場合のエラー。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    chat_id = uuid.uuid4()

    # 引数を実際のIDに置き換え
    actual_args = []
    for arg in args:
        if arg == "project_id":
            actual_args.append(project_id)
        elif arg == "session_id":
            actual_args.append(session_id)
        elif arg == "chat_id":
            actual_args.append(chat_id)

    # モックを設定
    patches = []
    for repo_name, method_to_mock, return_value in mock_setup:
        repository = getattr(service, repo_name)
        patches.append(
            patch.object(
                repository,
                method_to_mock,
                new_callable=AsyncMock,
                return_value=return_value,
            )
        )

    with patches[0]:
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            method = getattr(service, method_name)
            await method(*actual_args)

        assert "Session not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_session_result_no_snapshot(db_session: AsyncSession):
    """[test_analysis_operations-003] スナップショットがない場合は空の結果。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.project_id = project_id
    mock_session.current_snapshot = None

    with (
        patch.object(
            service.session_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.snapshot_repository,
            "get_by_order",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        # Act
        result = await service.get_session_result(project_id, session_id)

        # Assert
        assert result.results == []
        assert result.total == 0


@pytest.mark.parametrize(
    "mock_session,mock_snapshot,snapshot_order,expected_error",
    [
        (None, None, 0, "Session not found"),
        (MagicMock(), None, 999, "Snapshot not found"),
    ],
    ids=["session_not_found", "snapshot_not_found"],
)
@pytest.mark.asyncio
async def test_restore_snapshot_not_found_error(
    db_session: AsyncSession,
    mock_session,
    mock_snapshot,
    snapshot_order: int,
    expected_error: str,
):
    """[test_analysis_operations-004] スナップショット復元時のNotFoundエラー。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    session_id = uuid.uuid4()

    with (
        patch.object(
            service.session_repository,
            "get_with_relations",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.snapshot_repository,
            "get_by_order",
            new_callable=AsyncMock,
            return_value=mock_snapshot,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.restore_snapshot(session_id, snapshot_order)

        assert expected_error in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_chat_messages_success(db_session: AsyncSession):
    """[test_analysis_operations-006] チャットメッセージ取得の成功ケース。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.project_id = project_id
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 0

    mock_snapshot = MagicMock()
    mock_snapshot.id = uuid.uuid4()

    with (
        patch.object(
            service.session_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.snapshot_repository,
            "get_by_order",
            new_callable=AsyncMock,
            return_value=mock_snapshot,
        ),
        patch.object(
            service.chat_repository,
            "list_by_snapshot",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        # Act
        result = await service.get_chat_messages(project_id, session_id)

        # Assert
        assert result == []


@pytest.mark.asyncio
async def test_list_snapshots_success(db_session: AsyncSession):
    """[test_analysis_operations-008] スナップショット一覧取得の成功ケース。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.project_id = project_id

    with (
        patch.object(
            service.session_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.snapshot_repository,
            "list_by_session_with_relations",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        # Act
        result = await service.list_snapshots(project_id, session_id)

        # Assert
        assert result == []


@pytest.mark.asyncio
async def test_delete_chat_message_chat_not_found(db_session: AsyncSession):
    """[test_analysis_operations-010] チャット削除時にチャットが見つからない場合。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    chat_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.project_id = project_id

    with (
        patch.object(
            service.session_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.chat_repository,
            "get",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_chat_message(project_id, session_id, chat_id)

        assert "Chat message not found" in str(exc_info.value)
