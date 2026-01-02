"""カラム設定Mixinのテスト。

このテストファイルは、ColumnConfigMixinの各メソッドをテストします。

対応メソッド:
    - update_column_config: カラム設定更新
"""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import DriverTreeColumnRoleEnum
from app.schemas.driver_tree.driver_tree_file import DriverTreeColumnSetupItem
from app.services.driver_tree.driver_tree_file.service import DriverTreeFileService

# ================================================================================
# update_column_config テスト
# ================================================================================


@pytest.mark.asyncio
async def test_update_column_config_success(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_column_config-001] カラム設定更新の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # ProjectFileとDriverTreeFileを作成
    project_file = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        uploaded_by=owner.id,
    )

    column_id = str(uuid.uuid4())
    axis_config = {
        column_id: {
            "column_name": "年度",
            "role": "利用しない",
            "items": ["2023", "2024"],
        }
    }

    driver_tree_file = await test_data_seeder.create_driver_tree_file(
        project_file=project_file,
        sheet_name="Sheet1",
        axis_config=axis_config,
    )

    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # カラム設定
        columns = [
            DriverTreeColumnSetupItem(
                column_id=uuid.UUID(column_id),
                role=DriverTreeColumnRoleEnum.TRANSITION,
            )
        ]

        # Act
        result = await service.update_column_config(
            project_id=project.id,
            file_id=project_file.id,
            sheet_id=driver_tree_file.id,
            columns=columns,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    assert result["success"] is True
    assert "columns" in result
    assert len(result["columns"]) >= 1


@pytest.mark.asyncio
async def test_update_column_config_multiple_columns(db_session: AsyncSession, test_data_seeder, mock_storage_service):
    """[test_column_config-002] 複数カラムの設定更新。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    project_file = await test_data_seeder.create_project_file(
        project=project,
        filename="test.xlsx",
        uploaded_by=owner.id,
    )

    column_id1 = str(uuid.uuid4())
    column_id2 = str(uuid.uuid4())
    axis_config = {
        column_id1: {
            "column_name": "年度",
            "role": "利用しない",
            "items": ["2023", "2024"],
        },
        column_id2: {
            "column_name": "部門",
            "role": "利用しない",
            "items": ["営業", "開発"],
        },
    }

    driver_tree_file = await test_data_seeder.create_driver_tree_file(
        project_file=project_file,
        sheet_name="Sheet1",
        axis_config=axis_config,
    )

    await test_data_seeder.db.commit()

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        columns = [
            DriverTreeColumnSetupItem(
                column_id=uuid.UUID(column_id1),
                role=DriverTreeColumnRoleEnum.TRANSITION,
            ),
            DriverTreeColumnSetupItem(
                column_id=uuid.UUID(column_id2),
                role=DriverTreeColumnRoleEnum.AXIS,
            ),
        ]

        # Act
        result = await service.update_column_config(
            project_id=project.id,
            file_id=project_file.id,
            sheet_id=driver_tree_file.id,
            columns=columns,
            user_id=owner.id,
        )
        await db_session.commit()

    # Assert
    assert result["success"] is True
    assert len(result["columns"]) == 2


@pytest.mark.parametrize(
    "error_type",
    ["file_not_found", "sheet_not_found", "wrong_project"],
    ids=["file_not_found", "sheet_not_found", "wrong_project"],
)
@pytest.mark.asyncio
async def test_update_column_config_not_found_errors(
    db_session: AsyncSession, test_data_seeder, mock_storage_service, error_type: str
):
    """[test_column_config-003] update_column_configのNotFoundErrorケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    columns = [
        DriverTreeColumnSetupItem(
            column_id=uuid.uuid4(),
            role=DriverTreeColumnRoleEnum.TRANSITION,
        )
    ]

    if error_type == "file_not_found":
        await test_data_seeder.db.commit()
        file_id = uuid.uuid4()  # 存在しないファイル
        sheet_id = uuid.uuid4()
        expected_message = "ファイル"
    elif error_type == "sheet_not_found":
        project_file = await test_data_seeder.create_project_file(
            project=project,
            filename="test.xlsx",
            uploaded_by=owner.id,
        )
        await test_data_seeder.db.commit()
        file_id = project_file.id
        sheet_id = uuid.uuid4()  # 存在しないシート
        expected_message = "シート"
    else:  # wrong_project
        other_project, _ = await test_data_seeder.create_project_with_owner()
        project_file = await test_data_seeder.create_project_file(
            project=project,
            filename="test.xlsx",
            uploaded_by=owner.id,
        )
        column_id = str(uuid.uuid4())
        axis_config = {
            column_id: {
                "column_name": "年度",
                "role": "利用しない",
                "items": ["2023"],
            }
        }
        driver_tree_file = await test_data_seeder.create_driver_tree_file(
            project_file=project_file,
            sheet_name="Sheet1",
            axis_config=axis_config,
        )
        await test_data_seeder.db.commit()
        project = other_project  # 異なるプロジェクト
        file_id = project_file.id
        sheet_id = driver_tree_file.id
        columns = [
            DriverTreeColumnSetupItem(
                column_id=uuid.UUID(column_id),
                role=DriverTreeColumnRoleEnum.TRANSITION,
            )
        ]
        expected_message = None

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_column_config(
                project_id=project.id,
                file_id=file_id,
                sheet_id=sheet_id,
                columns=columns,
                user_id=owner.id,
            )

        if expected_message:
            assert expected_message in str(exc_info.value)


@pytest.mark.parametrize(
    "error_type",
    ["column_not_found", "sheet_wrong_file"],
    ids=["column_not_found", "sheet_wrong_file"],
)
@pytest.mark.asyncio
async def test_update_column_config_column_sheet_errors(
    db_session: AsyncSession, test_data_seeder, mock_storage_service, error_type: str
):
    """[test_column_config-004] カラム/シートのNotFoundErrorケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    if error_type == "column_not_found":
        project_file = await test_data_seeder.create_project_file(
            project=project,
            filename="test.xlsx",
            uploaded_by=owner.id,
        )
        existing_column_id = str(uuid.uuid4())
        axis_config = {
            existing_column_id: {
                "column_name": "年度",
                "role": "利用しない",
                "items": ["2023"],
            }
        }
        driver_tree_file = await test_data_seeder.create_driver_tree_file(
            project_file=project_file,
            sheet_name="Sheet1",
            axis_config=axis_config,
        )
        await test_data_seeder.db.commit()

        file_id = project_file.id
        sheet_id = driver_tree_file.id
        columns = [
            DriverTreeColumnSetupItem(
                column_id=uuid.uuid4(),  # 存在しないカラムID
                role=DriverTreeColumnRoleEnum.TRANSITION,
            )
        ]
        expected_message = "カラム"
    else:  # sheet_wrong_file
        project_file1 = await test_data_seeder.create_project_file(
            project=project,
            filename="test1.xlsx",
            uploaded_by=owner.id,
        )
        project_file2 = await test_data_seeder.create_project_file(
            project=project,
            filename="test2.xlsx",
            uploaded_by=owner.id,
        )
        column_id = str(uuid.uuid4())
        axis_config = {
            column_id: {
                "column_name": "年度",
                "role": "利用しない",
                "items": ["2023"],
            }
        }
        driver_tree_file = await test_data_seeder.create_driver_tree_file(
            project_file=project_file1,
            sheet_name="Sheet1",
            axis_config=axis_config,
        )
        await test_data_seeder.db.commit()

        file_id = project_file2.id  # 異なるファイル
        sheet_id = driver_tree_file.id
        columns = [
            DriverTreeColumnSetupItem(
                column_id=uuid.UUID(column_id),
                role=DriverTreeColumnRoleEnum.TRANSITION,
            )
        ]
        expected_message = "シート"

    with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
        service = DriverTreeFileService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_column_config(
                project_id=project.id,
                file_id=file_id,
                sheet_id=sheet_id,
                columns=columns,
                user_id=owner.id,
            )

        assert expected_message in str(exc_info.value)
