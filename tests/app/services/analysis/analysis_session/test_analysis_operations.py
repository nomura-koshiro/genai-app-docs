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


@pytest.mark.asyncio
async def test_get_session_result_session_not_found(db_session: AsyncSession):
    """[test_analysis_operations-002] セッションが見つからない場合のエラー。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    with patch.object(
        service.session_repository,
        "get",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_session_result(project_id, session_id)

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


@pytest.mark.asyncio
async def test_restore_snapshot_session_not_found(db_session: AsyncSession):
    """[test_analysis_operations-004] スナップショット復元時にセッションが見つからない場合。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    session_id = uuid.uuid4()

    with patch.object(
        service.session_repository,
        "get_with_relations",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.restore_snapshot(session_id, 0)

        assert "Session not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_restore_snapshot_snapshot_not_found(db_session: AsyncSession):
    """[test_analysis_operations-005] スナップショット復元時にスナップショットが見つからない場合。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    session_id = uuid.uuid4()

    mock_session = MagicMock()

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
            return_value=None,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.restore_snapshot(session_id, 999)

        assert "Snapshot not found" in str(exc_info.value)


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
async def test_get_chat_messages_session_not_found(db_session: AsyncSession):
    """[test_analysis_operations-007] チャットメッセージ取得時にセッションが見つからない場合。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    with patch.object(
        service.session_repository,
        "get",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_chat_messages(project_id, session_id)

        assert "Session not found" in str(exc_info.value)


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
async def test_delete_chat_message_session_not_found(db_session: AsyncSession):
    """[test_analysis_operations-009] チャット削除時にセッションが見つからない場合。"""
    # Arrange
    service = AnalysisSessionAnalysisService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    chat_id = uuid.uuid4()

    with patch.object(
        service.session_repository,
        "get",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_chat_message(project_id, session_id, chat_id)

        assert "Session not found" in str(exc_info.value)


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
