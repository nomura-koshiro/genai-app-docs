"""分析ステップ操作サービスのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.analysis.analysis_session.step_operations import (
    AnalysisSessionStepService,
)


@pytest.mark.asyncio
async def test_update_step_not_found(db_session: AsyncSession):
    """[test_step_operations-001] 存在しないステップの更新時のエラー。"""
    # Arrange
    service = AnalysisSessionStepService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 0
    mock_session.snapshots = [MagicMock()]
    mock_session.snapshots[0].steps = []  # 空のステップリスト

    with patch.object(
        service,
        "_get_session_with_full_relations",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_step(project_id, session_id, step_id, step_name="updated")

        assert "ステップが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_step_not_found(db_session: AsyncSession):
    """[test_step_operations-002] 存在しないステップの削除時のエラー。"""
    # Arrange
    service = AnalysisSessionStepService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 0
    mock_session.snapshots = [MagicMock()]
    mock_session.snapshots[0].steps = []  # 空のステップリスト

    with patch.object(
        service,
        "_get_session_with_full_relations",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_step(project_id, session_id, step_id)

        assert "ステップが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_step_wrong_snapshot(db_session: AsyncSession):
    """[test_step_operations-003] 現在のスナップショット以外のステップ削除時のエラー。"""
    # Arrange
    service = AnalysisSessionStepService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()

    mock_step = MagicMock()
    mock_step.id = step_id
    mock_step.step_order = 0

    mock_session = MagicMock()
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 1  # 現在は1番目
    mock_session.snapshots = [MagicMock(), MagicMock()]
    mock_session.snapshots[0].steps = [mock_step]  # ステップは0番目のスナップショット
    mock_session.snapshots[1].steps = []

    with patch.object(
        service,
        "_get_session_with_full_relations",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.delete_step(project_id, session_id, step_id)

        assert "現在のスナップショットのステップのみ削除できます" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_step_not_last(db_session: AsyncSession):
    """[test_step_operations-004] 最後のステップ以外を削除しようとした時のエラー。"""
    # Arrange
    service = AnalysisSessionStepService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()

    mock_step1 = MagicMock()
    mock_step1.id = step_id
    mock_step1.step_order = 0

    mock_step2 = MagicMock()
    mock_step2.id = uuid.uuid4()
    mock_step2.step_order = 1

    mock_session = MagicMock()
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 0
    mock_session.snapshots = [MagicMock()]
    mock_session.snapshots[0].steps = [mock_step1, mock_step2]  # 2つのステップ

    with patch.object(
        service,
        "_get_session_with_full_relations",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.delete_step(project_id, session_id, step_id)

        assert "最後のステップのみ削除できます" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_step_invalid_type(db_session: AsyncSession):
    """[test_step_operations-005] 無効なステップタイプでの更新時のエラー。"""
    # Arrange
    service = AnalysisSessionStepService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()

    mock_step = MagicMock()
    mock_step.id = step_id
    mock_step.step_order = 0
    mock_step.name = "test"
    mock_step.type = "filter"
    mock_step.input = "original"
    mock_step.config = {}

    mock_session = MagicMock()
    mock_session.current_snapshot = MagicMock()
    mock_session.current_snapshot.snapshot_order = 0
    mock_session.snapshots = [MagicMock()]
    mock_session.snapshots[0].steps = [mock_step]

    mock_state = MagicMock()
    mock_state.all_steps = [{"name": "test", "type": "filter", "data_source": "original", "config": {}}]

    with (
        patch.object(
            service,
            "_get_session_with_full_relations",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service,
            "_build_state",
            return_value=mock_state,
        ),
    ):
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.update_step(project_id, session_id, step_id, step_type="invalid_type")

        assert "無効なステップタイプです" in str(exc_info.value)
