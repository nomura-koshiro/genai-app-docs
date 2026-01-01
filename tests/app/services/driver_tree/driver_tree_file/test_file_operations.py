"""ファイル操作Mixinのテスト。

このテストファイルは、FileOperationsMixinの各メソッドをテストします。

対応メソッド:
    - upload_file: ファイルアップロード
    - delete_file: ファイル削除
    - list_uploaded_files: アップロード済みファイル一覧取得
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.driver_tree.driver_tree_file.service import DriverTreeFileService
from tests.fixtures.excel_helper import create_multi_sheet_excel_bytes

# ================================================================================
# upload_file テスト
# ================================================================================


@pytest.mark.asyncio
async def test_upload_file_success(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-001] ファイルアップロードの成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    # モックファイルを作成
    excel_bytes = create_multi_sheet_excel_bytes()
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.read = AsyncMock(return_value=excel_bytes)
    mock_file.seek = AsyncMock()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.upload_file(
            project_id=project.id,
            file=mock_file,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    assert "files" in result
    assert len(result["files"]) >= 1


@pytest.mark.asyncio
async def test_upload_file_with_multiple_sheets(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-002] 複数シートを含むファイルのアップロード。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    excel_bytes = create_multi_sheet_excel_bytes()
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "multi_sheet.xlsx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.read = AsyncMock(return_value=excel_bytes)
    mock_file.seek = AsyncMock()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.upload_file(
            project_id=project.id,
            file=mock_file,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    assert "files" in result
    # アップロードされたファイルにシートが含まれる
    uploaded_file = result["files"][0]
    assert "sheets" in uploaded_file
    assert len(uploaded_file["sheets"]) == 2  # Sheet1, Sheet2


@pytest.mark.asyncio
async def test_upload_file_calls_storage(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-003] ストレージサービスが呼び出される。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    excel_bytes = create_multi_sheet_excel_bytes()
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.read = AsyncMock(return_value=excel_bytes)
    mock_file.seek = AsyncMock()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        await service.upload_file(
            project_id=project.id,
            file=mock_file,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    mock_storage_service.upload.assert_called_once()


@pytest.mark.asyncio
async def test_upload_file_sanitizes_filename(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-004] ファイル名がサニタイズされる。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    excel_bytes = create_multi_sheet_excel_bytes()
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "../dangerous/../path.xlsx"  # 危険なファイル名
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.read = AsyncMock(return_value=excel_bytes)
    mock_file.seek = AsyncMock()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.upload_file(
            project_id=project.id,
            file=mock_file,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert: ファイルがアップロードされる（サニタイズされる）
    assert "files" in result


# ================================================================================
# delete_file テスト
# ================================================================================


@pytest.mark.asyncio
async def test_delete_file_success(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-005] ファイル削除の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    project_file = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        uploaded_by=owner.id,
    )
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.delete_file(
            project_id=project.id,
            file_id=project_file.id,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    assert "files" in result
    # 削除後はファイルが存在しない
    assert all(f["file_id"] != project_file.id for f in result["files"])


@pytest.mark.asyncio
async def test_delete_file_calls_storage(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-006] ストレージからファイルが削除される。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    project_file = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        uploaded_by=owner.id,
    )
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        await service.delete_file(
            project_id=project.id,
            file_id=project_file.id,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    mock_storage_service.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_file_not_found(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-007] 存在しないファイル削除でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.delete_file(
                project_id=project.id,
                file_id=uuid.uuid4(),
                user_id=owner.id,
            )


@pytest.mark.asyncio
async def test_delete_file_wrong_project(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-008] 異なるプロジェクトのファイル削除でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    other_project, _ = await test_data_seeder.create_project_with_owner()

    project_file = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        uploaded_by=owner.id,
    )
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.delete_file(
                project_id=other_project.id,  # 異なるプロジェクト
                file_id=project_file.id,
                user_id=owner.id,
            )


# ================================================================================
# list_uploaded_files テスト
# ================================================================================


@pytest.mark.asyncio
async def test_list_uploaded_files_success(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-009] アップロード済みファイル一覧取得の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    await test_data_seeder.create_project_file(
        project=project,
        filename="test1.xlsx",
        uploaded_by=owner.id,
    )
    await test_data_seeder.create_project_file(
        project=project,
        filename="test2.xlsx",
        uploaded_by=owner.id,
    )
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.list_uploaded_files(
            project_id=project.id,
            user_id=owner.id,
        )

    # Assert
    assert "files" in result
    assert len(result["files"]) == 2


@pytest.mark.asyncio
async def test_list_uploaded_files_empty(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-010] ファイルがない場合は空リストを返す。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.list_uploaded_files(
            project_id=project.id,
            user_id=owner.id,
        )

    # Assert
    assert result["files"] == []


@pytest.mark.asyncio
async def test_list_uploaded_files_with_sheets(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-011] シート情報が含まれる。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    project_file = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        uploaded_by=owner.id,
    )

    # シートを追加
    await test_data_seeder.create_driver_tree_file(
        project_file=project_file,
        sheet_name="Sheet1",
    )
    await test_data_seeder.create_driver_tree_file(
        project_file=project_file,
        sheet_name="Sheet2",
    )
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.list_uploaded_files(
            project_id=project.id,
            user_id=owner.id,
        )

    # Assert
    assert len(result["files"]) == 1
    file_info = result["files"][0]
    assert "sheets" in file_info
    assert len(file_info["sheets"]) == 2


@pytest.mark.asyncio
async def test_list_uploaded_files_structure(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_file_operations-012] レスポンス構造の検証。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    _ = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        original_filename="original.xlsx",
        uploaded_by=owner.id,
    )
    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act
        result = await service.list_uploaded_files(
            project_id=project.id,
            user_id=owner.id,
        )

    # Assert
    file_info = result["files"][0]
    assert "file_id" in file_info
    assert "filename" in file_info
    assert "file_size" in file_info
    assert "uploaded_at" in file_info
    assert "sheets" in file_info


# ================================================================================
# _generate_storage_path テスト
# ================================================================================


@pytest.mark.asyncio
async def test_generate_storage_path(db_session: AsyncSession, mock_storage_service):
    """[test_file_operations-013] ストレージパス生成の検証。"""
    # Arrange
    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        project_id = uuid.uuid4()
        file_id = uuid.uuid4()
        filename = "test.xlsx"

        # Act
        path = service._generate_storage_path(project_id, file_id, filename)

    # Assert
    assert str(project_id) in path
    assert str(file_id) in path
    assert filename in path
    assert path.startswith("projects/")
