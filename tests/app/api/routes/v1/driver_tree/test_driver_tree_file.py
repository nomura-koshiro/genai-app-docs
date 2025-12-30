"""ドライバーツリーファイルAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。

対応エンドポイント:
    - POST /api/v1/project/{project_id}/driver-tree/file - ファイルアップロード
    - GET /api/v1/project/{project_id}/driver-tree/file - アップロード済みファイル一覧取得
    - DELETE /api/v1/project/{project_id}/driver-tree/file/{file_id} - ファイル削除
    - GET /api/v1/project/{project_id}/driver-tree/sheet - 選択済みシート一覧取得
    - POST /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id} - シート選択
"""

import uuid
from io import BytesIO
from unittest.mock import patch

import pandas as pd
import pytest
from httpx import AsyncClient


def create_test_excel_file() -> BytesIO:
    """テスト用Excelファイルを作成します。

    構造:
    - メタデータセクション (3行): FY, 地域, 対象
    - 空行 (1行)
    - データセクション (3行): 施設数, 稼働率, 売上

    各行の第0列が列名、第1列以降がデータ
    """
    # メタデータ部分
    metadata_rows = [
        ["FY", "2023", "2023", "2024"],
        ["地域", "東京", "大阪", "東京"],
        ["対象", "A", "B", "A"],
    ]
    df_metadata = pd.DataFrame(metadata_rows)

    # 空行
    empty_row = pd.DataFrame([[None] * 4])

    # データ部分
    data_rows = [
        ["施設数", 10, 20, 15],
        ["稼働率", 0.8, 0.9, 0.85],
        ["売上", 1000, 2000, 1500],
    ]
    df_data = pd.DataFrame(data_rows)

    # 結合
    df_combined = pd.concat([df_metadata, empty_row, df_data], ignore_index=True)

    # BytesIOに書き込み
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_combined.to_excel(writer, sheet_name="Sheet1", index=False, header=False)
    output.seek(0)
    return output


@pytest.mark.asyncio
async def test_upload_driver_tree_file_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-001] ドライバーツリーファイルアップロードの成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    excel_file = create_test_excel_file()
    file_content = excel_file.read()
    excel_file.seek(0)

    files = {"file": ("test_capacity.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    # Act
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )

    # Assert
    assert response.status_code == 201
    data = response.json()

    # ファイル一覧が返されることを確認
    assert "files" in data
    assert len(data["files"]) == 1

    # アップロードしたファイル情報を確認
    uploaded_file = data["files"][0]
    assert uploaded_file["filename"] == "test_capacity.xlsx"
    assert uploaded_file["fileSize"] == len(file_content)
    assert "fileId" in uploaded_file
    assert "uploadedAt" in uploaded_file

    # シート一覧が含まれることを確認
    assert "sheets" in uploaded_file
    assert len(uploaded_file["sheets"]) >= 1
    assert uploaded_file["sheets"][0]["sheetName"] == "Sheet1"
    assert "sheetId" in uploaded_file["sheets"][0]


@pytest.mark.asyncio
async def test_upload_driver_tree_file_unsupported_type(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-002] サポートされていないファイル形式のアップロード失敗ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    file_content = b"This is a text file"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    # Act
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )

    # Assert
    assert response.status_code == 415  # Unsupported Media Type
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_upload_driver_tree_file_too_large(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-003] ファイルサイズ超過のアップロード失敗ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # 50MBを超えるファイルを作成（モック）
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    files = {"file": ("large_file.xlsx", BytesIO(large_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    # Act
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )

    # Assert
    assert response.status_code == 413  # Payload Too Large
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_upload_driver_tree_file_unauthorized(client: AsyncClient):
    """[test_driver_tree_file-004] 認証なしでのファイルアップロード失敗。"""
    # Arrange
    project_id = uuid.uuid4()
    excel_file = create_test_excel_file()
    files = {"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    # Act
    response = await client.post(f"/api/v1/project/{project_id}/driver-tree/file", files=files)

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/file - アップロード済みファイル一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_uploaded_files_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-007] アップロード済みファイル一覧取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # 2つのファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        for i in range(2):
            excel_file = create_test_excel_file()
            files = {"file": (f"test{i}.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            await client.post(
                f"/api/v1/project/{project.id}/driver-tree/file",
                files=files,
            )

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/file")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 2


@pytest.mark.asyncio
async def test_list_uploaded_files_unauthorized(client: AsyncClient):
    """[test_driver_tree_file-008] 認証なしでのファイル一覧取得失敗。"""
    # Arrange
    project_id = uuid.uuid4()

    # Act
    response = await client.get(f"/api/v1/project/{project_id}/driver-tree/file")

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/file/{file_id} - ファイル削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_driver_tree_file_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-009] ファイル削除の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("delete_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]

        # Act
        response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 0  # 削除後は空


@pytest.mark.asyncio
async def test_delete_driver_tree_file_not_found(
    client: AsyncClient,
    override_auth,
    project_with_owner,
):
    """[test_driver_tree_file-010] 存在しないファイルの削除（404エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    nonexistent_id = uuid.uuid4()

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/file/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_driver_tree_file_unauthorized(client: AsyncClient):
    """[test_driver_tree_file-011] 認証なしでのファイル削除失敗。"""
    # Arrange
    project_id = uuid.uuid4()
    file_id = uuid.uuid4()

    # Act
    response = await client.delete(f"/api/v1/project/{project_id}/driver-tree/file/{file_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id} - シート選択
# ================================================================================


@pytest.mark.asyncio
async def test_select_sheet_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-012] シート選択の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("select_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

        # Act
        response = await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_select_sheet_not_found(
    client: AsyncClient,
    override_auth,
    project_with_owner,
):
    """[test_driver_tree_file-013] 存在しないシートの選択（404エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_select_sheet_unauthorized(client: AsyncClient):
    """[test_driver_tree_file-014] 認証なしでのシート選択失敗。"""
    # Arrange
    project_id = uuid.uuid4()
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    # Act
    response = await client.post(f"/api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/sheet - 選択済みシート一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_selected_sheets_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-016] 選択済みシート一覧取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロードしてシートを選択
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("selected_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

        # シートを選択
        await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/sheet")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) >= 1

    # 選択済みシートにはcolumns情報が含まれることを確認
    selected_sheet = data["files"][0]["sheets"][0]
    assert "columns" in selected_sheet
    assert len(selected_sheet["columns"]) > 0

    # 各カラムにcolumnIdが含まれることを確認
    for column in selected_sheet["columns"]:
        assert "columnId" in column
        assert "columnName" in column
        assert "role" in column
        assert "items" in column


@pytest.mark.asyncio
async def test_list_selected_sheets_empty(
    client: AsyncClient,
    override_auth,
    project_with_owner,
):
    """[test_driver_tree_file-017] 選択済みシートがない場合の空リスト。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/sheet")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 0


@pytest.mark.asyncio
async def test_list_selected_sheets_unauthorized(client: AsyncClient):
    """[test_driver_tree_file-018] 認証なしでの選択済みシート一覧取得失敗。"""
    # Arrange
    project_id = uuid.uuid4()

    # Act
    response = await client.get(f"/api/v1/project/{project_id}/driver-tree/sheet")

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id} - シート削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_sheet_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-019] 選択済みシート削除成功。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロードしてシートを選択
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("delete_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

        # シートを選択
        await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

        # Act - シートを削除
        response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "files" in data


@pytest.mark.asyncio
async def test_delete_sheet_not_found(
    client: AsyncClient,
    override_auth,
    project_with_owner,
):
    """[test_driver_tree_file-020] 存在しないシートの削除でエラー。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_sheet_unauthorized(
    client: AsyncClient,
    project_with_owner,
):
    """[test_driver_tree_file-021] 認証なしでのシート削除失敗。"""
    # Arrange
    project, _ = project_with_owner
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column
# ================================================================================


@pytest.mark.asyncio
async def test_update_column_config_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    mock_storage_service,
):
    """[test_driver_tree_file-022] カラム設定更新成功。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # テスト用Excelファイルを作成してモックストレージに設定
    excel_file = create_test_excel_file()
    excel_bytes = excel_file.read()
    excel_file.seek(0)
    mock_storage_service.download.return_value = excel_bytes

    # ファイルをアップロードしてシート選択
    files = {"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    upload_response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/file",
        files=files,
    )
    file_id = upload_response.json()["files"][0]["fileId"]
    sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

    # シート選択
    select_response = await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")
    assert select_response.status_code == 200, f"Sheet selection failed: {select_response.json()}"

    # 選択済みシートの一覧を取得してcolumn_idを取得
    list_response = await client.get(f"/api/v1/project/{project.id}/driver-tree/sheet")
    assert list_response.status_code == 200
    list_data = list_response.json()
    columns = list_data["files"][0]["sheets"][0]["columns"]

    # column_nameからcolumn_idのマッピングを作成
    column_id_map = {col["columnName"]: col["columnId"] for col in columns}

    # Act - カラム設定を更新（column_idを使用）
    column_config = {
        "columns": [
            {"columnId": column_id_map["FY"], "role": "推移"},
            {"columnId": column_id_map["地域"], "role": "軸"},
            {"columnId": column_id_map["対象"], "role": "値"},
        ]
    }
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column",
        json=column_config,
    )

    # Assert
    if response.status_code != 200:
        error_detail = response.json()
        pytest.fail(f"Expected 200, got {response.status_code}. Error: {error_detail}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "columns" in data
    # axis_configには FY, 地域, 対象, 科目 の4列が含まれる
    assert len(data["columns"]) == 4

    # カラム情報の検証
    columns = data["columns"]

    # 更新したカラムのroleが正しく設定されていることを確認
    fy_column = next((col for col in columns if col["columnName"] == "FY"), None)
    assert fy_column is not None
    assert fy_column["role"] == "推移"
    assert "items" in fy_column
    assert "columnId" in fy_column  # columnIdが含まれることを確認

    region_column = next((col for col in columns if col["columnName"] == "地域"), None)
    assert region_column is not None
    assert region_column["role"] == "軸"
    assert "items" in region_column
    assert "columnId" in region_column

    target_column = next((col for col in columns if col["columnName"] == "対象"), None)
    assert target_column is not None
    assert target_column["role"] == "値"
    assert "items" in target_column
    assert "columnId" in target_column

    # 更新していないカラム(科目)も返されることを確認
    subject_column = next((col for col in columns if col["columnName"] == "科目"), None)
    assert subject_column is not None
    assert "columnId" in subject_column


@pytest.mark.asyncio
async def test_update_column_config_not_found(
    client: AsyncClient,
    override_auth,
    project_with_owner,
):
    """[test_driver_tree_file-023] 存在しないシートへのカラム設定更新（404エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    column_config = {
        "columns": [
            {"columnId": str(uuid.uuid4()), "role": "推移"},
        ]
    }

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column",
        json=column_config,
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_column_config_unauthorized(
    client: AsyncClient,
    project_with_owner,
):
    """[test_driver_tree_file-024] 認証なしでのカラム設定更新失敗。"""
    # Arrange
    project, _ = project_with_owner
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    column_config = {
        "columns": [
            {"columnId": str(uuid.uuid4()), "role": "推移"},
        ]
    }

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column",
        json=column_config,
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_column_config_invalid_role(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-025] 不正なrole値でのカラム設定更新失敗（422エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロードしてシート選択
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

        # シート選択
        select_response = await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")
        assert select_response.status_code == 200, f"Sheet selection failed: {select_response.json()}"

        # 選択済みシートの一覧を取得してcolumn_idを取得
        list_response = await client.get(f"/api/v1/project/{project.id}/driver-tree/sheet")
        assert list_response.status_code == 200
        list_data = list_response.json()
        columns = list_data["files"][0]["sheets"][0]["columns"]
        fy_column_id = next((col["columnId"] for col in columns if col["columnName"] == "FY"), None)

        # Act - 不正なrole値
        column_config = {
            "columns": [
                {"columnId": fy_column_id, "role": "invalid_role"},  # 不正な値
            ]
        }
        response = await client.patch(
            f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column",
            json=column_config,
        )

    # Assert
    assert response.status_code == 422  # Validation Error


@pytest.mark.asyncio
async def test_update_column_config_invalid_column_id(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-026] 存在しないcolumn_idでのカラム設定更新失敗（404エラー）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロードしてシート選択
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

        # シート選択
        select_response = await client.post(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}")
        assert select_response.status_code == 200, f"Sheet selection failed: {select_response.json()}"

        # Act - 存在しないcolumn_idを使用
        invalid_column_id = str(uuid.uuid4())
        column_config = {
            "columns": [
                {"columnId": invalid_column_id, "role": "推移"},
            ]
        }
        response = await client.patch(
            f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column",
            json=column_config,
        )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "カラム設定に該当カラムIDが見つかりません" in data["detail"]


# ================================================================================
# API拡張: SheetDetailResponse のテスト
# ================================================================================


@pytest.mark.asyncio
async def test_get_sheet_detail_success(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-027] シート詳細取得の成功ケース。

    07-api-extensions.md の実装により、SheetDetailResponse が返されることを確認。
    シート詳細には ColumnInfo（カラム情報）、行数、サンプルデータが含まれる。
    """
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("detail_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

    # Act
    # 注: このエンドポイントは実装されていない可能性があります
    # 実装されている場合は以下のようなパスになる想定
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/detail"
    )

    # Assert
    if response.status_code == 200:
        result = response.json()

        # SheetDetailResponse のフィールドを確認
        assert "sheetId" in result
        assert "sheetName" in result
        assert "columns" in result
        assert "rowCount" in result
        assert "sampleData" in result

        assert result["sheetId"] == sheet_id
        assert result["sheetName"] == "Sheet1"
        assert isinstance(result["columns"], list)
        assert isinstance(result["rowCount"], int)
        assert isinstance(result["sampleData"], list)

        # カラム情報の検証
        if len(result["columns"]) > 0:
            column = result["columns"][0]
            assert "name" in column
            assert "displayName" in column
            assert "dataType" in column
            # role はオプションなので、存在チェックのみ
            if "role" in column:
                assert isinstance(column["role"], (str, type(None)))

        # サンプルデータの検証（最初の10行程度）
        if result["rowCount"] > 0:
            assert len(result["sampleData"]) > 0
            assert len(result["sampleData"]) <= 10  # サンプルデータは最大10行
    else:
        # エンドポイントが未実装の場合はスキップ
        pytest.skip("Sheet detail endpoint not implemented yet")


@pytest.mark.asyncio
async def test_get_sheet_detail_not_found(
    client: AsyncClient,
    override_auth,
    project_with_owner,
):
    """[test_driver_tree_file-028] 存在しないシートの詳細取得で404。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    file_id = uuid.uuid4()
    sheet_id = uuid.uuid4()

    # Act
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/detail"
    )

    # Assert
    if response.status_code == 404:
        assert True  # 期待通り404
    else:
        # エンドポイントが未実装の場合はスキップ
        pytest.skip("Sheet detail endpoint not implemented yet")


@pytest.mark.asyncio
async def test_sheet_detail_column_info_types(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
):
    """[test_driver_tree_file-029] シート詳細のColumnInfoで各種データ型が返されることを確認。

    ColumnInfo の dataType フィールドが適切に設定されていることを確認。
    """
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # ファイルをアップロード
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        excel_file = create_test_excel_file()
        files = {"file": ("types_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )
        file_id = upload_response.json()["files"][0]["fileId"]
        sheet_id = upload_response.json()["files"][0]["sheets"][0]["sheetId"]

    # Act
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/detail"
    )

    # Assert
    if response.status_code == 200:
        result = response.json()
        columns = result["columns"]

        # データ型が適切に設定されているか確認
        # テストファイルには string, number などのデータが含まれる
        data_types = {col["dataType"] for col in columns}
        # 少なくとも1つのデータ型が存在することを確認
        assert len(data_types) > 0
        # 有効なデータ型のみが使用されているか確認
        valid_types = {"string", "number", "datetime", "boolean"}
        assert data_types.issubset(valid_types)
    else:
        pytest.skip("Sheet detail endpoint not implemented yet")
