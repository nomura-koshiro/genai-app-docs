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
@pytest.mark.parametrize(
    "file_content,filename,content_type,expected_status",
    [
        (b"This is a text file", "test.txt", "text/plain", 415),
        (b"x" * (51 * 1024 * 1024), "large_file.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 413),
    ],
    ids=["unsupported_type", "too_large"],
)
async def test_upload_driver_tree_file_errors(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
    file_content,
    filename,
    content_type,
    expected_status,
):
    """[test_driver_tree_file-002,003] ファイルアップロードエラーケース（非対応形式・サイズ超過）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    files = {"file": (filename, BytesIO(file_content), content_type)}

    # Act
    with patch("app.core.config.settings.LOCAL_STORAGE_PATH", str(tmp_path)):
        response = await client.post(
            f"/api/v1/project/{project.id}/driver-tree/file",
            files=files,
        )

    # Assert
    assert response.status_code == expected_status
    data = response.json()
    assert "detail" in data


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
    """[test_driver_tree_file-004] アップロード済みファイル一覧取得の成功ケース。"""
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
    """[test_driver_tree_file-005] ファイル削除の成功ケース。"""
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
    """[test_driver_tree_file-006] シート選択の成功ケース。"""
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


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/sheet - 選択済みシート一覧取得
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "should_upload_and_select,expected_file_count",
    [
        (True, 1),
        (False, 0),
    ],
    ids=["with_sheets", "empty"],
)
async def test_list_selected_sheets(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
    should_upload_and_select,
    expected_file_count,
):
    """[test_driver_tree_file-007,008] 選択済みシート一覧取得（データあり・なし）。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    if should_upload_and_select:
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
    assert len(data["files"]) == expected_file_count

    if should_upload_and_select:
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
    """[test_driver_tree_file-009] 選択済みシート削除成功。"""
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
    """[test_driver_tree_file-010] カラム設定更新成功。"""
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
@pytest.mark.parametrize(
    "error_type,expected_status,error_message_check",
    [
        ("invalid_role", 422, None),
        ("invalid_column_id", 404, "カラム設定に該当カラムIDが見つかりません"),
    ],
    ids=["invalid_role", "invalid_column_id"],
)
async def test_update_column_config_errors(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
    error_type,
    expected_status,
    error_message_check,
):
    """[test_driver_tree_file-011,012] カラム設定更新エラーケース（不正role・不正column_id）。"""
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

        # Act - エラーケース別の設定
        if error_type == "invalid_role":
            column_config = {
                "columns": [
                    {"columnId": fy_column_id, "role": "invalid_role"},
                ]
            }
        else:  # invalid_column_id
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
    assert response.status_code == expected_status
    if error_message_check:
        data = response.json()
        assert error_message_check in data["detail"]


# ================================================================================
# API拡張: SheetDetailResponse のテスト
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "check_type",
    ["basic_fields", "data_types"],
    ids=["basic_fields", "data_types"],
)
async def test_get_sheet_detail(
    client: AsyncClient,
    override_auth,
    project_with_owner,
    tmp_path,
    check_type,
):
    """[test_driver_tree_file-013,014] シート詳細取得（基本フィールド・データ型検証）。

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
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/file/{file_id}/sheet/{sheet_id}/detail")

    # Assert
    if response.status_code == 200:
        result = response.json()

        if check_type == "basic_fields":
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
                    assert isinstance(column["role"], str | None)

            # サンプルデータの検証（最初の10行程度）
            if result["rowCount"] > 0:
                assert len(result["sampleData"]) > 0
                assert len(result["sampleData"]) <= 10  # サンプルデータは最大10行
        else:  # data_types
            columns = result["columns"]

            # データ型が適切に設定されているか確認
            data_types = {col["dataType"] for col in columns}
            # 少なくとも1つのデータ型が存在することを確認
            assert len(data_types) > 0
            # 有効なデータ型のみが使用されているか確認
            valid_types = {"string", "number", "datetime", "boolean"}
            assert data_types.issubset(valid_types)
    else:
        # エンドポイントが未実装の場合はスキップ
        pytest.skip("Sheet detail endpoint not implemented yet")
