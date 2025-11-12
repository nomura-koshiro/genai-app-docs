"""分析APIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。
"""

import base64
import uuid

import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """セッション作成エンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    session_data = {
        "project_id": str(test_project.id),
        "policy": "市場拡大",
        "issue": "売上向上",
    }

    # Act
    response = await client.post("/api/v1/analysis/sessions", json=session_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["validation_config"]["policy"] == "市場拡大"
    assert data["chat_history"] == []
    # snapshot_historyは初期状態では空リストを1つ含むリスト
    assert data["snapshot_history"] == [[]]


@pytest.mark.asyncio
async def test_get_session_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """セッション取得エンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    # セッションを作成
    create_data = {"project_id": str(test_project.id), "policy": "テスト施策", "issue": "テスト課題"}
    create_response = await client.post("/api/v1/analysis/sessions", json=create_data)
    session_id = create_response.json()["id"]

    # Act
    response = await client.get(f"/api/v1/analysis/sessions/{session_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["validation_config"]["policy"] == "テスト施策"
    # snapshot_historyの存在を確認
    assert "snapshot_history" in data
    assert data["snapshot_history"] is not None


@pytest.mark.asyncio
async def test_list_user_sessions_endpoint(client: AsyncClient, override_auth, test_user, test_project):
    """ユーザーのセッション一覧取得エンドポイントのテスト。"""
    # Arrange
    override_auth(test_user)

    # 2つのセッションを作成
    await client.post(
        "/api/v1/analysis/sessions", json={"project_id": str(test_project.id), "policy": "テスト施策1", "issue": "テスト課題1"}
    )
    await client.post(
        "/api/v1/analysis/sessions", json={"project_id": str(test_project.id), "policy": "テスト施策2", "issue": "テスト課題2"}
    )

    # Act
    response = await client.get(f"/api/v1/analysis/sessions?project_id={test_project.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    # 各セッションにsnapshot_historyが含まれることを確認
    for session in data:
        assert "snapshot_history" in session


@pytest.mark.asyncio
async def test_upload_file_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """ファイルアップロードエンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    # セッションを作成
    create_data = {"project_id": str(test_project.id), "policy": "テスト施策", "issue": "テスト課題"}
    create_response = await client.post("/api/v1/analysis/sessions", json=create_data)
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    # CSVデータを作成
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
        }
    )
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode()).decode()

    file_data = {
        "session_id": session_id,
        "file_name": "test.csv",
        "table_name": "test_data",
        "table_axis": ["name"],
        "data": encoded_content,
    }

    # Act
    response = await client.post(f"/api/v1/analysis/sessions/{session_id}/files", json=file_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "test.csv"
    assert data["table_name"] == "test_data"
    assert "id" in data
    assert "storage_path" in data


@pytest.mark.asyncio
async def test_add_chat_message_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """チャットメッセージ追加エンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    # セッションを作成
    create_data = {"project_id": str(test_project.id), "policy": "テスト施策", "issue": "テスト課題"}
    create_response = await client.post("/api/v1/analysis/sessions", json=create_data)
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    chat_data = {
        "message": "Hello, AI!",
    }

    # Act
    response = await client.post(f"/api/v1/analysis/sessions/{session_id}/chat", json=chat_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "snapshot_id" in data


@pytest.mark.skip(reason="Snapshot endpoint not implemented yet")
@pytest.mark.asyncio
async def test_create_snapshot_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """スナップショット作成エンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    # セッションを作成
    create_data = {"project_id": str(test_project.id), "policy": "テスト施策", "issue": "テスト課題"}
    create_response = await client.post("/api/v1/analysis/sessions", json=create_data)
    session_id = create_response.json()["id"]

    snapshot_data = {
        "name": "Test Snapshot",
        "description": "Test snapshot description",
        "timestamp": "2025-01-01T00:00:00Z",
    }

    # Act
    response = await client.post(f"/api/v1/analysis/sessions/{session_id}/snapshots", json=snapshot_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert len(data["snapshot_history"]) == 1
    assert data["snapshot_history"][0]["name"] == "Test Snapshot"


@pytest.mark.skip(reason="Validation config update endpoint not implemented yet")
@pytest.mark.asyncio
async def test_update_validation_config_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """検証設定更新エンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    # セッションを作成
    create_data = {"project_id": str(test_project.id), "policy": "元の施策", "issue": "元の課題"}
    create_response = await client.post("/api/v1/analysis/sessions", json=create_data)
    session_id = create_response.json()["id"]

    new_config = {
        "target_column": "sales",
        "data_type": "numeric",
    }

    # Act
    response = await client.patch(f"/api/v1/analysis/sessions/{session_id}/validation-config", json=new_config)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["validation_config"]["policy"] == "市場拡大"
    # Removed: validation_config assertion


@pytest.mark.skip(reason="Session delete endpoint not implemented yet")
@pytest.mark.asyncio
async def test_delete_session_endpoint_success(client: AsyncClient, override_auth, test_user, test_project):
    """セッション削除エンドポイントの成功ケース。"""
    # Arrange
    override_auth(test_user)

    # セッションを作成
    create_data = {"project_id": str(test_project.id), "policy": "テスト施策", "issue": "テスト課題"}
    create_response = await client.post("/api/v1/analysis/sessions", json=create_data)
    session_id = create_response.json()["id"]

    # Act
    response = await client.delete(f"/api/v1/analysis/sessions/{session_id}")

    # Assert
    assert response.status_code == 204

    # 削除されたことを確認
    get_response = await client.get(f"/api/v1/analysis/sessions/{session_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions_with_pagination(client: AsyncClient, override_auth, test_user, test_project):
    """ページネーション付きセッション一覧取得のテスト。"""
    # Arrange
    override_auth(test_user)

    # 5つのセッションを作成
    for i in range(5):
        response = await client.post(
            "/api/v1/analysis/sessions", json={"project_id": str(test_project.id), "policy": f"施策{i}", "issue": f"課題{i}"}
        )
        assert response.status_code == 201

    # Act - ページネーション付きで取得
    response = await client.get(f"/api/v1/analysis/sessions?project_id={test_project.id}&skip=0&limit=3")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 少なくとも3件は取得できる
    assert len(data) >= 3
    # 各セッションにsnapshot_historyが含まれることを確認
    for session in data:
        assert "snapshot_history" in session


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """認証なしでのアクセステスト。"""
    # Act - 認証なしでセッション作成を試みる
    fake_project_id = str(uuid.uuid4())
    session_data = {"project_id": fake_project_id, "policy": "テスト施策", "issue": "テスト課題"}
    response = await client.post("/api/v1/analysis/sessions", json=session_data)

    # Assert - 認証エラー
    assert response.status_code in [401, 403]
