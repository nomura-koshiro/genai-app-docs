"""分析セッションサービスの統合テスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analysis.analysis_session.service import AnalysisSessionService


@pytest.mark.asyncio
async def test_init_service(db_session: AsyncSession):
    """[test_service-001] サービス初期化の成功ケース。"""
    # Act
    service = AnalysisSessionService(db_session)

    # Assert
    assert service is not None
    assert service.db == db_session
    assert service._crud_service is not None
    assert service._file_service is not None
    assert service._analysis_service is not None
    assert service._step_service is not None


@pytest.mark.asyncio
async def test_list_sessions_delegates_to_crud_service(db_session: AsyncSession):
    """[test_service-002] list_sessionsがcrud_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    expected_result = []

    with patch.object(
        service._crud_service,
        "list_sessions",
        new_callable=AsyncMock,
        return_value=expected_result,
    ) as mock_list:
        # Act
        result = await service.list_sessions(project_id, skip=0, limit=100)

        # Assert
        mock_list.assert_called_once_with(project_id, 0, 100, None)
        assert result == expected_result


@pytest.mark.asyncio
async def test_get_session_delegates_to_crud_service(db_session: AsyncSession):
    """[test_service-003] get_sessionがcrud_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    expected_result = MagicMock()

    with patch.object(
        service._crud_service,
        "get_session",
        new_callable=AsyncMock,
        return_value=expected_result,
    ) as mock_get:
        # Act
        result = await service.get_session(project_id, session_id)

        # Assert
        mock_get.assert_called_once_with(project_id, session_id)
        assert result == expected_result


@pytest.mark.asyncio
async def test_delete_session_delegates_to_crud_service(db_session: AsyncSession):
    """[test_service-004] delete_sessionがcrud_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    with patch.object(
        service._crud_service,
        "delete_session",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_delete:
        # Act
        await service.delete_session(project_id, session_id)

        # Assert
        mock_delete.assert_called_once_with(project_id, session_id)


@pytest.mark.asyncio
async def test_list_session_files_delegates_to_file_service(db_session: AsyncSession):
    """[test_service-005] list_session_filesがfile_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    expected_result = []

    with patch.object(
        service._file_service,
        "list_session_files",
        new_callable=AsyncMock,
        return_value=expected_result,
    ) as mock_list:
        # Act
        result = await service.list_session_files(project_id, session_id)

        # Assert
        mock_list.assert_called_once_with(project_id, session_id)
        assert result == expected_result


@pytest.mark.asyncio
async def test_get_session_result_delegates_to_analysis_service(db_session: AsyncSession):
    """[test_service-006] get_session_resultがanalysis_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    expected_result = MagicMock()

    with patch.object(
        service._analysis_service,
        "get_session_result",
        new_callable=AsyncMock,
        return_value=expected_result,
    ) as mock_get:
        # Act
        result = await service.get_session_result(project_id, session_id)

        # Assert
        mock_get.assert_called_once_with(project_id, session_id)
        assert result == expected_result


@pytest.mark.asyncio
async def test_create_step_delegates_to_step_service(db_session: AsyncSession):
    """[test_service-007] create_stepがstep_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    expected_result = MagicMock()

    with patch.object(
        service._step_service,
        "create_step",
        new_callable=AsyncMock,
        return_value=expected_result,
    ) as mock_create:
        # Act
        result = await service.create_step(project_id, session_id, "step1", "filter", "original")

        # Assert
        mock_create.assert_called_once_with(project_id, session_id, "step1", "filter", "original", None)
        assert result == expected_result


@pytest.mark.asyncio
async def test_delete_step_delegates_to_step_service(db_session: AsyncSession):
    """[test_service-008] delete_stepがstep_serviceに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()

    with patch.object(
        service._step_service,
        "delete_step",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_delete:
        # Act
        await service.delete_step(project_id, session_id, step_id)

        # Assert
        mock_delete.assert_called_once_with(project_id, session_id, step_id)
