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


@pytest.mark.asyncio
async def test_list_sessions_success(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-001] セッション一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    service = AnalysisSessionService(db_session)

    # Act
    sessions = await service.list_sessions(project_id=project.id)

    # Assert
    assert len(sessions) == 1
    assert sessions[0].project_id == project.id


@pytest.mark.asyncio
async def test_list_sessions_empty(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-002] セッションがない場合は空リストを返す。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act
    sessions = await service.list_sessions(project_id=project.id)

    # Assert
    assert len(sessions) == 0


@pytest.mark.asyncio
async def test_list_sessions_with_pagination(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-003] ページネーション付きセッション一覧取得。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    validation = await test_data_seeder.create_validation_master()
    issue = await test_data_seeder.create_issue_master(validation=validation)

    # 複数セッションを作成
    for _ in range(5):
        session = await test_data_seeder.create_analysis_session(project=project, creator=owner, issue=issue)
        await test_data_seeder.create_analysis_snapshot(session=session)

    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act
    sessions = await service.list_sessions(project_id=project.id, skip=0, limit=3)

    # Assert
    assert len(sessions) == 3


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


@pytest.mark.asyncio
async def test_get_session_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-006] 存在しないセッションの取得でNotFoundError。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_session(project_id=project.id, session_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_get_session_wrong_project(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-007] 異なるプロジェクトIDでのセッション取得でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    session = data["session"]
    other_project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_session(project_id=other_project.id, session_id=session.id)


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


@pytest.mark.asyncio
async def test_delete_session_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-009] 存在しないセッションの削除でNotFoundError。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.delete_session(project_id=project.id, session_id=uuid.uuid4())


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


@pytest.mark.asyncio
async def test_list_session_files_session_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-011] 存在しないセッションでのファイル一覧取得でNotFoundError。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    service = AnalysisSessionService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.list_session_files(project_id=project.id, session_id=uuid.uuid4())


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
async def test_upload_session_file_session_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-013] 存在しないセッションへのファイルアップロードでNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    await test_data_seeder.db.commit()

    service = AnalysisSessionService(db_session)
    file_create = AnalysisFileCreate(project_file_id=project_file.id)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.upload_session_file(project_id=project.id, session_id=uuid.uuid4(), file_create=file_create)


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
async def test_update_file_config_file_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_analysis_session-015] 存在しないファイルの設定更新でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    session = data["session"]
    service = AnalysisSessionService(db_session)
    config_data = AnalysisFileUpdate(sheet_name="UpdatedSheet")

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_file_config(
            project_id=project.id,
            session_id=session.id,
            file_id=uuid.uuid4(),
            config_data=config_data,
        )


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
