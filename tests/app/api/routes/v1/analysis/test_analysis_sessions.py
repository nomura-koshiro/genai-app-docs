"""分析セッションAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/project/{project_id}/analysis/session - セッション一覧取得
    - POST /api/v1/project/{project_id}/analysis/session - セッション作成
    - GET /api/v1/project/{project_id}/analysis/session/{session_id} - セッション詳細取得
    - GET /api/v1/project/{project_id}/analysis/{session_id}/result - 分析結果取得
    - PUT /api/v1/project/{project_id}/analysis/{session_id} - セッション更新
    - DELETE /api/v1/project/{project_id}/analysis/session/{session_id} - セッション削除
    - GET /api/v1/project/{project_id}/analysis/session/{session_id}/file - ファイル一覧取得
    - POST /api/v1/project/{project_id}/analysis/session/{session_id}/file - ファイルアップロード
    - PATCH /api/v1/project/{project_id}/analysis/session/{session_id}/file/{file_id} - ファイル設定更新
"""


import pytest
from httpx import AsyncClient

from tests.fixtures import create_invalid_format_excel_bytes

# ================================================================================
# GET /api/v1/project/{project_id}/analysis/session - セッション一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_sessions_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-001] セッション一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/session")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "sessions" in result
    assert "total" in result
    assert len(result["sessions"]) == 1


@pytest.mark.asyncio
async def test_list_sessions_with_pagination(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-002] ページネーション付きセッション一覧取得。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    validation = await test_data_seeder.create_validation_master()
    issue = await test_data_seeder.create_issue_master(validation=validation)

    for _ in range(5):
        session = await test_data_seeder.create_analysis_session(project=project, creator=owner, issue=issue)
        await test_data_seeder.create_analysis_snapshot(session=session)

    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/session?skip=0&limit=3")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["skip"] == 0
    assert result["limit"] == 3


# ================================================================================
# POST /api/v1/project/{project_id}/analysis/session - セッション作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_session_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-003] セッション作成の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    validation = await test_data_seeder.create_validation_master()
    issue = await test_data_seeder.create_issue_master(validation=validation)
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "project_id": str(project.id),
        "issue_id": str(issue.id),
    }

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/analysis/session", json=request_body)

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert result["projectId"] == str(project.id)
    assert result["currentSnapshot"] == 0


# ================================================================================
# GET /api/v1/project/{project_id}/analysis/session/{session_id} - セッション詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_session_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-004] セッション詳細取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/session/{session.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(session.id)
    assert result["projectId"] == str(project.id)


# ================================================================================
# GET /api/v1/project/{project_id}/analysis/{session_id}/result - 分析結果取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_session_result_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-005] 分析結果取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/session/{session.id}/result")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "results" in result
    assert "total" in result


# ================================================================================
# PUT /api/v1/project/{project_id}/analysis/{session_id} - セッション更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_session_select_input_file(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-006] 入力ファイル選択の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    analysis_file = await test_data_seeder.create_analysis_file(
        session=session,
        project_file=project_file,
        data=[{"科目": "売上", "値": 100}],
    )
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {"input_file_id": str(analysis_file.id)}

    # Act
    response = await client.put(f"/api/v1/project/{project.id}/analysis/session/{session.id}", json=request_body)

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["inputFileId"] == str(analysis_file.id)


@pytest.mark.asyncio
async def test_update_session_restore_snapshot(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-007] スナップショット復元の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    # 追加スナップショットを作成
    await test_data_seeder.create_analysis_snapshot(session=session, snapshot_order=1)
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {"current_snapshot": 0}

    # Act
    response = await client.put(f"/api/v1/project/{project.id}/analysis/session/{session.id}", json=request_body)

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["currentSnapshot"] == 0


# ================================================================================
# DELETE /api/v1/project/{project_id}/analysis/session/{session_id} - セッション削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_session_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-008] セッション削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/analysis/session/{session.id}")

    # Assert
    assert response.status_code == 204


# ================================================================================
# GET /api/v1/project/{project_id}/analysis/session/{session_id}/file - ファイル一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_session_files_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-009] ファイル一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    await test_data_seeder.create_analysis_file(session=session, project_file=project_file)
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/session/{session.id}/file")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "files" in result
    assert "total" in result
    assert len(result["files"]) == 1


# ================================================================================
# POST /api/v1/project/{project_id}/analysis/session/{session_id}/file - ファイルアップロード
# ================================================================================


@pytest.mark.asyncio
async def test_upload_session_file_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-010] ファイルアップロードの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {"project_file_id": str(project_file.id)}

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/analysis/session/{session.id}/file",
        json=request_body,
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert "configList" in result


@pytest.mark.asyncio
async def test_upload_session_file_no_valid_sheets(client: AsyncClient, override_auth, test_data_seeder, mock_storage_service):
    """[test_analysis_sessions-011] 有効なシートがないExcelファイルのアップロードでエラー。

    Excelファイル内の全シートがparse_hierarchical_excelで処理できない場合、
    ValidationError(422)が返される。
    """
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    await test_data_seeder.db.commit()
    override_auth(owner)

    # モックのダウンロードを無効なExcelファイルに変更
    mock_storage_service.download.return_value = create_invalid_format_excel_bytes()

    request_body = {"project_file_id": str(project_file.id)}

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/analysis/session/{session.id}/file",
        json=request_body,
    )

    # Assert
    assert response.status_code == 422
    result = response.json()
    assert "No valid sheets" in result.get("detail", "")


# ================================================================================
# PATCH /api/v1/project/{project_id}/analysis/session/{session_id}/file/{file_id}
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_body,expected_status,check_fields",
    [
        (
            {"sheet_name": "Sheet1", "axis_config": {"axis1": "年度"}},
            200,
            {"sheetName": "Sheet1", "axisConfig": {"axis1": "年度"}},
        ),
        (
            {"sheet_name": "NonExistentSheet", "axis_config": {"axis1": "年度"}},
            422,
            {"available_sheets": True},
        ),
        (
            {"sheet_name": "Sheet1", "axis_config": {"axis1": "存在しない軸"}},
            422,
            {"invalid_axis": True, "available_axis": True},
        ),
    ],
    ids=["success", "invalid_sheet_name", "invalid_axis_config"],
)
async def test_update_file_config(
    client: AsyncClient,
    override_auth,
    test_data_seeder,
    request_body,
    expected_status,
    check_fields,
):
    """[test_analysis_sessions-012-014] ファイル設定更新のテストケース。

    モックExcelファイルには "Sheet1", "Sheet2" が存在し、
    軸として "年度", "部門" が利用可能。
    """
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    analysis_file = await test_data_seeder.create_analysis_file(session=session, project_file=project_file)
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/analysis/session/{session.id}/file/{analysis_file.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == expected_status
    result = response.json()
    for field, value in check_fields.items():
        if value is True:
            assert field in result
        else:
            assert result[field] == value


# ================================================================================
# POST /api/v1/project/{project_id}/analysis/session/{session_id}/step - ステップ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_step_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-015] 分析ステップ作成の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    # 入力ファイルを設定
    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    analysis_file = await test_data_seeder.create_analysis_file(
        session=session,
        project_file=project_file,
        data=[{"col1": 1, "col2": 2}, {"col1": 3, "col2": 4}],
    )
    session.input_file_id = analysis_file.id
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "name": "Test Filter Step",
        "type": "filter",
        "input": "original",
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/analysis/session/{session.id}/step",
        json=request_body,
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert result["name"] == "Test Filter Step"
    assert result["type"] == "filter"
    assert result["input"] == "original"


# ================================================================================
# PUT /api/v1/project/{project_id}/analysis/session/{session_id}/step/{step_id} - ステップ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_step_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-016] 分析ステップ更新の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]
    snapshot = data["snapshot"]

    # 入力ファイルを設定
    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    analysis_file = await test_data_seeder.create_analysis_file(
        session=session,
        project_file=project_file,
        data=[{"col1": 1, "col2": 2}, {"col1": 3, "col2": 4}],
    )
    session.input_file_id = analysis_file.id

    # ステップを作成
    step = await test_data_seeder.create_analysis_step(
        snapshot=snapshot,
        name="Original Step",
        step_order=0,
        step_type="filter",
        input_ref="original",
        config={"table_filter": {}, "numeric_filter": {}, "category_filter": {}},
    )
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "name": "Updated Step",
        "type": "filter",
        "input": "original",
        "config": {"table_filter": {}, "numeric_filter": {}, "category_filter": {}},
    }

    # Act
    response = await client.put(
        f"/api/v1/project/{project.id}/analysis/session/{session.id}/step/{step.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Updated Step"


# ================================================================================
# DELETE /api/v1/project/{project_id}/analysis/session/{session_id}/step/{step_id} - ステップ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_step_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_analysis_sessions-017] 分析ステップ削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]
    snapshot = data["snapshot"]

    # ステップを作成（最後のステップのみ削除可能）
    step = await test_data_seeder.create_analysis_step(
        snapshot=snapshot,
        name="Step to Delete",
        step_order=0,
        step_type="summary",
        input_ref="original",
        config={},
    )
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/analysis/session/{session.id}/step/{step.id}")

    # Assert
    assert response.status_code == 204


# ================================================================================
# POST /api/v1/project/{project_id}/analysis/{session_id}/chat - チャット実行
# ================================================================================


@pytest.mark.asyncio
async def test_execute_chat_success(client: AsyncClient, override_auth, test_data_seeder, mock_analysis_agent):
    """[test_analysis_sessions-018] チャット実行の成功ケース。

    メッセージ送信→エージェント応答→新スナップショット作成→チャット履歴保存を確認。
    """
    from unittest.mock import patch

    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    # 入力ファイルを設定
    project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
    analysis_file = await test_data_seeder.create_analysis_file(
        session=session,
        project_file=project_file,
        data=[{"年度": "2024", "部門": "営業", "科目": "売上", "値": 100}],
    )
    session.input_file_id = analysis_file.id
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {"role": "user", "message": "売上データを分析してください"}

    # モックの初期chat_historyをカスタマイズ
    mock_agent_class, mock_agent = mock_analysis_agent
    mock_agent.initial_chat_history = [
        ("system", "あなたは分析アシスタントです。ユーザの質問に答えてください。"),
    ]

    # Act
    with patch("app.services.analysis.analysis_session.base.AnalysisAgent", mock_agent_class):
        response = await client.post(
            f"/api/v1/project/{project.id}/analysis/session/{session.id}/chat",
            json=request_body,
        )

    # Assert
    assert response.status_code == 200
    result = response.json()
    # 新しいスナップショットが作成されている
    assert result["currentSnapshot"] == 1
    # スナップショット一覧に新しいスナップショットが含まれる
    assert len(result["snapshotList"]) == 2
    # 新しいスナップショットにチャット履歴が保存されている
    new_snapshot = result["snapshotList"][1]
    assert len(new_snapshot["chat"]) == 3
    assert new_snapshot["chat"][2]["role"] == "assistant"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup_input_file,message,expected_status",
    [
        (False, "売上データを分析してください", 404),
        (True, "", [400, 422]),
    ],
    ids=["input_file_not_selected", "empty_message"],
)
async def test_execute_chat_error_cases(
    client: AsyncClient,
    override_auth,
    test_data_seeder,
    setup_input_file,
    message,
    expected_status,
):
    """[test_analysis_sessions-019-020] チャット実行のエラーケース。"""
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]

    if setup_input_file:
        # 入力ファイルを設定
        project_file = await test_data_seeder.create_project_file(project=project, uploader=owner)
        analysis_file = await test_data_seeder.create_analysis_file(
            session=session,
            project_file=project_file,
            data=[{"年度": "2024", "部門": "営業", "科目": "売上", "値": 100}],
        )
        session.input_file_id = analysis_file.id
    else:
        # 入力ファイルを設定しない（input_file_id = None）
        session.input_file_id = None

    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {"role": "user", "message": message}

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/analysis/session/{session.id}/chat",
        json=request_body,
    )

    # Assert
    if isinstance(expected_status, list):
        assert response.status_code in expected_status
    else:
        assert response.status_code == expected_status


# ================================================================================
# API拡張: ValidationInfo を含むセッションレスポンスのテスト
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint_type,response_key",
    [
        ("list", "sessions"),
        ("detail", None),
    ],
    ids=["list_sessions", "session_detail"],
)
async def test_session_with_validation_info(
    client: AsyncClient,
    override_auth,
    test_data_seeder,
    endpoint_type,
    response_key,
):
    """[test_analysis_sessions-021-022] ValidationInfo を含むセッションレスポンス。

    07-api-extensions.md の実装により、セッションレスポンスに validation フィールドが追加されたことを確認。
    """
    # Arrange
    data = await test_data_seeder.seed_analysis_session_dataset()
    project = data["project"]
    owner = data["owner"]
    session = data["session"]
    validation = data.get("validation")
    override_auth(owner)

    # Act
    if endpoint_type == "list":
        response = await client.get(f"/api/v1/project/{project.id}/analysis/session")
    else:  # detail
        response = await client.get(f"/api/v1/project/{project.id}/analysis/session/{session.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()

    # データ取得
    if endpoint_type == "list":
        assert response_key in result
        assert len(result[response_key]) > 0
        session_data = result[response_key][0]
    else:
        assert result["id"] == str(session.id)
        session_data = result

    # ValidationInfoフィールドの存在を確認
    if validation:
        assert "validation" in session_data
        assert session_data["validation"] is not None
        assert "id" in session_data["validation"]
        assert "name" in session_data["validation"]
        assert session_data["validation"]["id"] == str(validation.id)
        if endpoint_type == "detail":
            assert session_data["validation"]["name"] == validation.name
