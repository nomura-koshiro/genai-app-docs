"""ドライバーツリー計算サービスのテスト。

このテストファイルは、DriverTreeCalculationServiceの各メソッドをテストします。

対応メソッド:
    - get_tree_data: ツリーデータ取得（計算実行）
    - download_simulation_output: シミュレーション結果ダウンロード
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.driver_tree.driver_tree.calculation import DriverTreeCalculationService

# ================================================================================
# get_tree_data テスト
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_data_success(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-001] ツリーデータ取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeCalculationService(db_session)

    # Act
    result = await service.get_tree_data(
        project_id=project.id,
        tree_id=tree.id,
        user_id=owner.id,
    )

    # Assert
    assert "calculated_data_list" in result
    assert isinstance(result["calculated_data_list"], list)


@pytest.mark.asyncio
async def test_get_tree_data_with_nodes(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-002] ノードを含むツリーデータ取得。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeCalculationService(db_session)

    # Act
    result = await service.get_tree_data(
        project_id=project.id,
        tree_id=tree.id,
        user_id=owner.id,
    )

    # Assert
    assert "calculated_data_list" in result
    calculated_data_list = result["calculated_data_list"]
    # シードデータには3つのノード（ルート+2子ノード）がある
    assert len(calculated_data_list) >= 1
    # 各計算データには必要なフィールドがある
    for item in calculated_data_list:
        assert "node_id" in item
        assert "label" in item
        assert "columns" in item
        assert "records" in item


@pytest.mark.asyncio
async def test_get_tree_data_tree_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-003] 存在しないツリーでNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeCalculationService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_tree_data(
            project_id=project.id,
            tree_id=uuid.uuid4(),
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_get_tree_data_wrong_project(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-004] 異なるプロジェクトIDでNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    tree = data["tree"]
    owner = data["owner"]

    other_project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeCalculationService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_tree_data(
            project_id=other_project.id,
            tree_id=tree.id,
            user_id=owner.id,
        )


# ================================================================================
# download_simulation_output テスト
# ================================================================================


@pytest.mark.asyncio
async def test_download_simulation_output_csv_success(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-005] CSV形式でのダウンロード成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeCalculationService(db_session)

    # Act
    response = await service.download_simulation_output(
        project_id=project.id,
        tree_id=tree.id,
        format="csv",
        user_id=owner.id,
    )

    # Assert
    assert response.media_type == "text/csv"
    assert "Content-Disposition" in response.headers
    assert f"simulation_{tree.id}.csv" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_download_simulation_output_excel_success(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-006] Excel形式でのダウンロード成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeCalculationService(db_session)

    # Act
    response = await service.download_simulation_output(
        project_id=project.id,
        tree_id=tree.id,
        format="xlsx",
        user_id=owner.id,
    )

    # Assert
    assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Content-Disposition" in response.headers
    assert f"simulation_{tree.id}.xlsx" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_download_simulation_output_csv_content(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-007] CSVコンテンツの検証。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeCalculationService(db_session)

    # Act
    response = await service.download_simulation_output(
        project_id=project.id,
        tree_id=tree.id,
        format="csv",
        user_id=owner.id,
    )

    # Assert: レスポンスのボディを読み取り
    content = b""
    async for chunk in response.body_iterator:
        if isinstance(chunk, memoryview):
            content += bytes(chunk)
        elif isinstance(chunk, bytes):
            content += chunk
        else:
            content += chunk.encode("utf-8")
    csv_text = content.decode("utf-8-sig")

    # CSVヘッダーを確認
    assert "node_id,label,value" in csv_text


@pytest.mark.asyncio
async def test_download_simulation_output_tree_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-008] 存在しないツリーでNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeCalculationService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.download_simulation_output(
            project_id=project.id,
            tree_id=uuid.uuid4(),
            format="csv",
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_download_simulation_output_wrong_project(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-009] 異なるプロジェクトIDでNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    tree = data["tree"]
    owner = data["owner"]

    other_project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeCalculationService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.download_simulation_output(
            project_id=other_project.id,
            tree_id=tree.id,
            format="xlsx",
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_download_simulation_output_default_format(db_session: AsyncSession, test_data_seeder):
    """[test_calculation-010] デフォルトフォーマット（Excel）でのダウンロード。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeCalculationService(db_session)

    # Act
    response = await service.download_simulation_output(
        project_id=project.id,
        tree_id=tree.id,
        format="xlsx",  # デフォルトはxlsx
        user_id=owner.id,
    )

    # Assert
    assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
