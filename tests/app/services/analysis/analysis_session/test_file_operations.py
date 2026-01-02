"""ファイル操作サービスのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.schemas.analysis import AnalysisFileUpdate
from app.services.analysis.analysis_session.file_operations import (
    AnalysisSessionFileService,
)


@pytest.mark.asyncio
async def test_list_session_files_success(db_session: AsyncSession):
    """[test_file_operations-001] ファイル一覧取得の成功ケース。"""
    # Arrange
    service = AnalysisSessionFileService(db_session)
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
            service.file_repository,
            "list_by_session",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        # Act
        result = await service.list_session_files(project_id, session_id)

        # Assert
        assert result == []


@pytest.mark.parametrize(
    "scenario,session_return",
    [
        ("session_not_found", None),
        ("project_mismatch", "mismatch"),
    ],
    ids=["session_not_found", "project_mismatch"],
)
@pytest.mark.asyncio
async def test_list_session_files_errors(
    db_session: AsyncSession, scenario: str, session_return
):
    """[test_file_operations-002/003] ファイル一覧取得時のエラーケース。"""
    # Arrange
    service = AnalysisSessionFileService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    if session_return == "mismatch":
        mock_session = MagicMock()
        mock_session.project_id = uuid.uuid4()  # 異なるプロジェクトID
        session_return_value = mock_session
    else:
        session_return_value = None

    with patch.object(
        service.session_repository,
        "get",
        new_callable=AsyncMock,
        return_value=session_return_value,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.list_session_files(project_id, session_id)

        assert "Session not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_file_config_session_not_found(db_session: AsyncSession):
    """[test_file_operations-004] ファイル設定更新時にセッションが見つからない場合。"""
    # Arrange
    service = AnalysisSessionFileService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    file_id = uuid.uuid4()
    config_data = AnalysisFileUpdate(sheet_name="Sheet1", axis_config={"x": "年度"})

    with patch.object(
        service.session_repository,
        "get",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_file_config(project_id, session_id, file_id, config_data)

        assert "Session not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_file_config_file_not_found(db_session: AsyncSession):
    """[test_file_operations-005] ファイル設定更新時にファイルが見つからない場合。"""
    # Arrange
    service = AnalysisSessionFileService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    file_id = uuid.uuid4()
    config_data = AnalysisFileUpdate(sheet_name="Sheet1", axis_config={"x": "年度"})

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
            service.file_repository,
            "get_with_project_file",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_file_config(project_id, session_id, file_id, config_data)

        assert "File not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_select_input_file_session_not_found(db_session: AsyncSession):
    """[test_file_operations-006] 入力ファイル選択時にセッションが見つからない場合。"""
    # Arrange
    service = AnalysisSessionFileService(db_session)
    session_id = uuid.uuid4()
    file_id = uuid.uuid4()

    with patch.object(
        service.session_repository,
        "get_with_relations",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.select_input_file(session_id, file_id)

        assert "Session not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_select_input_file_file_not_found(db_session: AsyncSession):
    """[test_file_operations-007] 入力ファイル選択時にファイルが見つからない場合。"""
    # Arrange
    service = AnalysisSessionFileService(db_session)
    session_id = uuid.uuid4()
    file_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.input_file_id = None

    with (
        patch.object(
            service.session_repository,
            "get_with_relations",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch.object(
            service.file_repository,
            "get",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.select_input_file(session_id, file_id)

        assert "File not found" in str(exc_info.value)
