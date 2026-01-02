"""分析セッションサービスのテスト。

このテストファイルは、AnalysisSessionServiceの各メソッドをテストします。

対応メソッド:
    - list_sessions: セッション一覧取得
    - create_session: セッション作成
    - get_session: セッション詳細取得
    - delete_session: セッション削除
    - list_session_files: ファイル一覧取得
    - upload_session_file: ファイルアップロード
    - update_file_config: ファイル設定更新
    - select_input_file: 入力ファイル選択
    - get_session_result: 分析結果取得
    - restore_snapshot: スナップショット復元
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.schemas.analysis import (
    AnalysisFileCreate,
    AnalysisFileUpdate,
    AnalysisSessionCreate,
)
from app.services.analysis import AnalysisSessionService
from tests.fixtures.excel_helper import create_test_excel_bytes

# ================================================================================
# セッション CRUD
# ================================================================================


@pytest.mark.parametrize(
    "setup_type,skip,limit,expected_count",
    [
        ("with_session", 0, 100, 1),
        ("empty", 0, 100, 0),
        ("multiple_sessions", 0, 3, 3),
    ],
    ids=["success", "empty", "pagination"],
)
@pytest.mark.asyncio
async def test_list_sessions(
    db_session: AsyncSession,
    test_data_seeder,
    setup_type: str,
    skip: int,
    limit: int,
    expected_count: int,
):
    """[test_analysis_session-001] セッション一覧取得のテスト。"""
    # Arrange
    if setup_type == "with_session":
        data = await test_data_seeder.seed_analysis_session_dataset()
        project = data["project"]
    elif setup_type == "empty":
        project, _ = await test_data_seeder.create_project_with_owner()
        await test_data_seeder.db.commit()
    else:  # multiple_sessions
        project, owner = await test_data_seeder.create_project_with_owner()
        validation = await test_data_seeder.create_validation_master()
        issue = await test_data_seeder.create_issue_master(validation=validation)
        for _ in range(5):
            session = await test_data_seeder.create_analysis_session(project=project, creator=owner, issue=issue)
            await test_data_seeder.create_analysis_snapshot(session=session)
        await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)

    # Act
    sessions = await service.list_sessions(project_id=project.id, skip=skip, limit=limit)

    # Assert
    assert len(sessions) == expected_count
    if expected_count > 0:
        assert sessions[0].project_id == project.id


@pytest.mark.asyncio
async def test_create_session_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-004] セッション作成の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    validation = await test_data_seeder.create_validation_master()
    issue = await test_data_seeder.create_issue_master(validation=validation)
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)
    session_create = AnalysisSessionCreate(
        project_id=project.id,
        issue_id=issue.id,
    )

    # Act
    result = await service.create_session(
        project_id=project.id,
        creator_id=owner.id,
        session_create=session_create,
    )
    await db_session.commit()

    # Assert
    assert result.id is not None
    assert result.project_id == project.id
    assert result.issue_id == issue.id
    assert result.creator_id == owner.id
    assert result.current_snapshot == 0
    # 初期スナップショットが作成されていること
    assert len(result.snapshot_list) == 1
    assert result.snapshot_list[0].snapshot_order == 0


@pytest.mark.asyncio
async def test_get_session_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-005] セッション詳細取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    session = data["session"]
    service = AnalysisSessionService(db_session)

    # Act
    result = await service.get_session(project_id=project.id, session_id=session.id)

    # Assert
    assert result.id == session.id
    assert result.project_id == project.id


@pytest.mark.parametrize(
    "method_name,setup_type",
    [
        ("get_session", "empty_project"),
        ("get_session", "wrong_project"),
        ("delete_session", "empty_project"),
    ],
    ids=["get_not_found", "get_wrong_project", "delete_not_found"],
)
@pytest.mark.asyncio
async def test_session_not_found_error(
    db_session: AsyncSession,
    test_data_seeder,
    method_name: str,
    setup_type: str,
):
    """[test_analysis_session-006] セッションNotFoundエラーケース。"""
    # Arrange
    if setup_type == "empty_project":
        project, _ = await test_data_seeder.create_project_with_owner()
        session_id = uuid.uuid4()
    else:  # wrong_project
        data = await test_data_seeder.seed_analysis_session_dataset()
        session_id = data["session"].id
        project, _ = await test_data_seeder.create_project_with_owner()

    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        method = getattr(service, method_name)
        await method(project_id=project.id, session_id=session_id)


@pytest.mark.asyncio
async def test_delete_session_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-008] セッション削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    session = data["session"]
    session_id = session.id
    service = AnalysisSessionService(db_session)

    # Act
    await service.delete_session(project_id=project.id, session_id=session_id)
    await db_session.commit()

    # Assert - 削除されたことを確認
    with pytest.raises(NotFoundError):
        await service.get_session(project_id=project.id, session_id=session_id)


# ================================================================================
# ファイル管理
# ================================================================================


@pytest.mark.asyncio
async def test_list_session_files_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-010] ファイル一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    # プロジェクトファイルと分析ファイルを作成
    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    await test_data_seeder.create_analysis_file(session=session, project_file=project_file, sheet_name="TestSheet")
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)

    # Act
    files = await service.list_session_files(project_id=project.id, session_id=session.id)

    # Assert
    assert len(files) == 1
    assert files[0].sheet_name == "TestSheet"


@pytest.mark.parametrize(
    "method_name,needs_file_id",
    [
        ("list_session_files", False),
        ("upload_session_file", False),
        ("update_file_config", True),
    ],
    ids=["list_files_not_found", "upload_session_not_found", "update_file_not_found"],
)
@pytest.mark.asyncio
async def test_file_operation_not_found_error(
    db_session: AsyncSession,
    test_data_seeder,
    method_name: str,
    needs_file_id: bool,
):
    """[test_analysis_session-011] ファイル操作のNotFoundエラー。"""
    # Arrange
    if needs_file_id:
        # update_file_configの場合
        data = await test_data_seeder.seed_analysis_session_dataset()
        project = data["project"]
        session = data["session"]
        file_id = uuid.uuid4()
    else:
        # list_session_filesやupload_session_fileの場合
        project, owner = await test_data_seeder.create_project_with_owner()
        if method_name == "upload_session_file":
            project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
        session_id = uuid.uuid4()

    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        method = getattr(service, method_name)
        if needs_file_id:
            from app.schemas.analysis import AnalysisFileUpdate
            await method(
                project_id=project.id,
                session_id=session.id,
                file_id=file_id,
                config_data=AnalysisFileUpdate(sheet_name="UpdatedSheet"),
            )
        elif method_name == "upload_session_file":
            from app.schemas.analysis import AnalysisFileCreate
            await method(
                project_id=project.id,
                session_id=session_id,
                file_create=AnalysisFileCreate(project_file_id=project_file.id),
            )
        else:
            await method(project_id=project.id, session_id=session_id)


@pytest.mark.asyncio
async def test_upload_session_file_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-012] ファイルアップロードの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)
    file_create = AnalysisFileCreate(project_file_id=project_file.id)

    # Act - ストレージサービスをモックしてテスト用Excelを返す
    mock_storage = AsyncMock()
    mock_storage.download = AsyncMock(return_value=create_test_excel_bytes())
    with patch.object(service._file_service, "storage", mock_storage):
        result = await service.upload_session_file(project_id=project.id, session_id=session.id, file_create=file_create)
    await db_session.commit()

    # Assert
    assert result.id is not None
    assert isinstance(result.config_list, list)


@pytest.mark.asyncio
async def test_update_file_config_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-014] ファイル設定更新の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    analysis_file = await test_data_seeder.create_analysis_file(session=session, project_file=project_file)
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)
    # テスト用Excelファイルのシート名は "Sheet1"、軸名は "年度", "部門"
    config_data = AnalysisFileUpdate(
        sheet_name="Sheet1",
        axis_config={"axis1": "年度", "axis2": "部門"},
    )

    # Act - ストレージサービスをモックしてテスト用Excelを返す
    mock_storage = AsyncMock()
    mock_storage.download = AsyncMock(return_value=create_test_excel_bytes())
    with patch.object(service._file_service, "storage", mock_storage):
        result = await service.update_file_config(
            project_id=project.id,
            session_id=session.id,
            file_id=analysis_file.id,
            config_data=config_data,
        )
    await db_session.commit()

    # Assert
    assert result.sheet_name == "Sheet1"
    assert result.axis_config == {"axis1": "年度", "axis2": "部門"}


@pytest.mark.asyncio
async def test_select_input_file_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-016] 入力ファイル選択の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    # _build_stateで必要なdataを設定（list[dict]形式）
    test_data = [{"年度": "2023", "部門": "営業", "科目": "売上", "値": 1000}]
    analysis_file = await test_data_seeder.create_analysis_file(session=session, project_file=project_file, data=test_data)
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)

    # Act
    result = await service.select_input_file(session_id=session.id, file_id=analysis_file.id)
    await db_session.commit()

    # Assert
    assert result.input_file_id == analysis_file.id


@pytest.mark.asyncio
async def test_select_input_file_clear(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-017] 入力ファイル選択解除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    session = data["session"]
    service = AnalysisSessionService(db_session)

    # Act - Noneを指定して選択解除
    result = await service.select_input_file(session_id=session.id, file_id=None)
    await db_session.commit()

    # Assert
    assert result.input_file_id is None


@pytest.mark.asyncio
async def test_select_input_file_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-018] 存在しないファイルの選択でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    session = data["session"]
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.select_input_file(session_id=session.id, file_id=uuid.uuid4())


# ================================================================================
# 分析結果・スナップショット
# ================================================================================


@pytest.mark.asyncio
async def test_get_session_result_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-019] 分析結果取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    session = data["session"]
    snapshot = data["snapshot"]

    # summaryステップを作成
    await test_data_seeder.create_analysis_step(
        snapshot=snapshot,
        name="Summary Step",
        step_type="summary",
        config={
            "result_formula": [{"name": "Total", "value": "100"}],
            "result_chart": {"data": []},
        },
    )
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)

    # Act
    result = await service.get_session_result(project_id=project.id, session_id=session.id)

    # Assert
    assert result.total >= 0


@pytest.mark.asyncio
async def test_get_session_result_empty(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-020] 結果がない場合は空リストを返す。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    session = data["session"]
    service = AnalysisSessionService(db_session)

    # Act
    result = await service.get_session_result(project_id=project.id, session_id=session.id)

    # Assert
    assert result.total == 0
    assert result.results == []


@pytest.mark.asyncio
async def test_get_session_result_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-021] 存在しないセッションの結果取得でNotFoundError。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_session_result(project_id=project.id, session_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_restore_snapshot_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-022] スナップショット復元の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    session = data["session"]

    # 追加のスナップショットを作成
    await test_data_seeder.create_analysis_snapshot(session=session, snapshot_order=1)
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)

    # Act
    result = await service.restore_snapshot(session_id=session.id, snapshot_order=0)
    await db_session.commit()

    # Assert
    assert result.current_snapshot == 0


@pytest.mark.asyncio
async def test_restore_snapshot_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-023] 存在しないスナップショットの復元でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    session = data["session"]
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.restore_snapshot(session_id=session.id, snapshot_order=999)
