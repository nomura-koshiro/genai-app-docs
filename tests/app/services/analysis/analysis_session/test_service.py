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


@pytest.mark.parametrize(
    "method_name,service_attr,method_to_call,call_args,call_kwargs,expected_args",
    [
        (
            "list_sessions",
            "_crud_service",
            "list_sessions",
            ["project_id"],
            {"skip": 0, "limit": 100},
            ["project_id", 0, 100, None],
        ),
        (
            "get_session",
            "_crud_service",
            "get_session",
            ["project_id", "session_id"],
            {},
            ["project_id", "session_id"],
        ),
        (
            "delete_session",
            "_crud_service",
            "delete_session",
            ["project_id", "session_id"],
            {},
            ["project_id", "session_id"],
        ),
        (
            "list_session_files",
            "_file_service",
            "list_session_files",
            ["project_id", "session_id"],
            {},
            ["project_id", "session_id"],
        ),
        (
            "get_session_result",
            "_analysis_service",
            "get_session_result",
            ["project_id", "session_id"],
            {},
            ["project_id", "session_id"],
        ),
        (
            "create_step",
            "_step_service",
            "create_step",
            ["project_id", "session_id", "step1", "filter", "original"],
            {},
            ["project_id", "session_id", "step1", "filter", "original", None],
        ),
    ],
    ids=["list_sessions", "get_session", "delete_session", "list_session_files", "get_session_result", "create_step"],
)
@pytest.mark.asyncio
async def test_service_delegation(
    db_session: AsyncSession,
    method_name: str,
    service_attr: str,
    method_to_call: str,
    call_args: list,
    call_kwargs: dict,
    expected_args: list,
):
    """[test_service-002] サービスメソッドが適切なサービスに委譲されること。"""
    # Arrange
    service = AnalysisSessionService(db_session)
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()

    # 引数を実際のIDに置き換え
    actual_call_args = []
    for arg in call_args:
        if arg == "project_id":
            actual_call_args.append(project_id)
        elif arg == "session_id":
            actual_call_args.append(session_id)
        else:
            actual_call_args.append(arg)

    actual_expected_args = []
    for arg in expected_args:
        if arg == "project_id":
            actual_expected_args.append(project_id)
        elif arg == "session_id":
            actual_expected_args.append(session_id)
        else:
            actual_expected_args.append(arg)

    expected_result = [] if method_name in ["list_sessions", "list_session_files"] else MagicMock()

    # 委譲先サービスのモック
    target_service = getattr(service, service_attr)
    with patch.object(
        target_service,
        method_to_call,
        new_callable=AsyncMock,
        return_value=expected_result,
    ) as mock_method:
        # Act
        method = getattr(service, method_name)
        result = await method(*actual_call_args, **call_kwargs)

        # Assert
        mock_method.assert_called_once_with(*actual_expected_args)
        if method_name not in ["delete_session"]:
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
