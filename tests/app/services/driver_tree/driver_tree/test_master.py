"""ドライバーツリーマスタデータサービスのテスト。

このテストファイルは、DriverTreeMasterServiceの各メソッドをテストします。

対応メソッド:
    - get_categories: 業界分類一覧取得
    - get_formulas: 数式取得
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.driver_tree import DriverTreeCategory, DriverTreeFormula
from app.services.driver_tree.driver_tree.master import DriverTreeMasterService

# ================================================================================
# get_categories テスト
# ================================================================================


@pytest.mark.asyncio
async def test_get_categories_success(db_session: AsyncSession, test_data_seeder):
    """[test_master-001] カテゴリ取得の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # テスト用のcategoryデータを作成
    category = DriverTreeCategory(
        category_id=1,
        category_name="テストカテゴリ",
        industry_id=1,
        industry_name="テスト業種",
        driver_type_id=1,
        driver_type="テストドライバー型",
    )
    test_data_seeder.db.add(category)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_categories(
        project_id=project.id,
        user_id=owner.id,
    )

    # Assert
    assert "categories" in result
    assert isinstance(result["categories"], list)
    assert len(result["categories"]) >= 1


@pytest.mark.asyncio
async def test_get_categories_with_multiple_categories(db_session: AsyncSession, test_data_seeder):
    """[test_master-002] 複数カテゴリの取得。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # 複数カテゴリを作成
    for i in range(3):
        category = DriverTreeCategory(
            category_id=i + 1,
            category_name=f"カテゴリ{i + 1}",
            industry_id=i + 1,
            industry_name=f"業種{i + 1}",
            driver_type_id=i + 1,
            driver_type=f"ドライバー型{i + 1}",
        )
        test_data_seeder.db.add(category)

    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_categories(
        project_id=project.id,
        user_id=owner.id,
    )

    # Assert
    assert len(result["categories"]) >= 3


@pytest.mark.asyncio
async def test_get_categories_structure(db_session: AsyncSession, test_data_seeder):
    """[test_master-003] カテゴリレスポンス構造の検証。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    category = DriverTreeCategory(
        category_id=1,
        category_name="構造テストカテゴリ",
        industry_id=1,
        industry_name="構造テスト業種",
        driver_type_id=1,
        driver_type="構造テストドライバー型",
    )
    test_data_seeder.db.add(category)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_categories(
        project_id=project.id,
        user_id=owner.id,
    )

    # Assert
    category_data = result["categories"][0]
    assert "category_id" in category_data
    assert "category_name" in category_data
    assert "industries" in category_data
    assert isinstance(category_data["industries"], list)

    industry_data = category_data["industries"][0]
    assert "industry_id" in industry_data
    assert "industry_name" in industry_data
    assert "driver_types" in industry_data


@pytest.mark.asyncio
async def test_get_categories_with_multiple_industries(db_session: AsyncSession, test_data_seeder):
    """[test_master-004] 同一カテゴリに複数業種がある場合。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # 同一カテゴリに複数業種を追加
    for i in range(2):
        category = DriverTreeCategory(
            category_id=1,  # 同じカテゴリ
            category_name="共通カテゴリ",
            industry_id=i + 1,  # 異なる業種
            industry_name=f"業種{i + 1}",
            driver_type_id=i + 1,
            driver_type=f"ドライバー型{i + 1}",
        )
        test_data_seeder.db.add(category)

    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_categories(
        project_id=project.id,
        user_id=owner.id,
    )

    # Assert
    # 共通カテゴリは1つ
    common_category = None
    for cat in result["categories"]:
        if cat["category_name"] == "共通カテゴリ":
            common_category = cat
            break

    assert common_category is not None
    assert len(common_category["industries"]) == 2


@pytest.mark.asyncio
async def test_get_categories_empty(db_session: AsyncSession, test_data_seeder):
    """[test_master-005] カテゴリが空の場合。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_categories(
        project_id=project.id,
        user_id=owner.id,
    )

    # Assert
    assert "categories" in result
    assert result["categories"] == []


# ================================================================================
# get_formulas テスト
# ================================================================================


@pytest.mark.asyncio
async def test_get_formulas_success(db_session: AsyncSession, test_data_seeder):
    """[test_master-006] 数式取得の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    formula = DriverTreeFormula(
        driver_type_id=1,
        driver_type="テストドライバー型",
        kpi="売上",
        formulas=["売上 = 数量 * 単価"],
    )
    test_data_seeder.db.add(formula)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_formulas(
        project_id=project.id,
        driver_type_id=1,
        kpi="売上",
        user_id=owner.id,
    )

    # Assert
    assert "formula" in result
    formula_data = result["formula"]
    assert formula_data["driver_type_id"] == 1
    assert formula_data["kpi"] == "売上"


@pytest.mark.asyncio
async def test_get_formulas_structure(db_session: AsyncSession, test_data_seeder):
    """[test_master-007] 数式レスポンス構造の検証。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    formula = DriverTreeFormula(
        driver_type_id=1,
        driver_type="構造テストドライバー型",
        kpi="利益",
        formulas=["利益 = 売上 - コスト", "売上 = 数量 * 単価"],
    )
    test_data_seeder.db.add(formula)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act
    result = await service.get_formulas(
        project_id=project.id,
        driver_type_id=1,
        kpi="利益",
        user_id=owner.id,
    )

    # Assert
    formula_data = result["formula"]
    assert "formula_id" in formula_data
    assert "driver_type_id" in formula_data
    assert "driver_type" in formula_data
    assert "kpi" in formula_data
    assert "formulas" in formula_data
    assert isinstance(formula_data["formulas"], list)
    assert len(formula_data["formulas"]) == 2


@pytest.mark.asyncio
async def test_get_formulas_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_master-008] 存在しない数式でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_formulas(
            project_id=project.id,
            driver_type_id=999,  # 存在しないID
            kpi="存在しないKPI",
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_get_formulas_wrong_driver_type(db_session: AsyncSession, test_data_seeder):
    """[test_master-009] 異なるdriver_type_idでNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    formula = DriverTreeFormula(
        driver_type_id=1,
        driver_type="テストドライバー型",
        kpi="売上",
        formulas=["売上 = 数量 * 単価"],
    )
    test_data_seeder.db.add(formula)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act & Assert: 異なるdriver_type_idでは見つからない
    with pytest.raises(NotFoundError):
        await service.get_formulas(
            project_id=project.id,
            driver_type_id=2,  # 存在しないdriver_type_id
            kpi="売上",
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_get_formulas_wrong_kpi(db_session: AsyncSession, test_data_seeder):
    """[test_master-010] 異なるKPIでNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    formula = DriverTreeFormula(
        driver_type_id=1,
        driver_type="テストドライバー型",
        kpi="売上",
        formulas=["売上 = 数量 * 単価"],
    )
    test_data_seeder.db.add(formula)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act & Assert: 異なるKPIでは見つからない
    with pytest.raises(NotFoundError):
        await service.get_formulas(
            project_id=project.id,
            driver_type_id=1,
            kpi="利益",  # 異なるKPI
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_get_formulas_multiple_entries(db_session: AsyncSession, test_data_seeder):
    """[test_master-011] 複数の数式エントリがある場合。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # 複数の数式を追加
    formula1 = DriverTreeFormula(
        driver_type_id=1,
        driver_type="テストドライバー型",
        kpi="売上",
        formulas=["売上 = 数量 * 単価"],
    )
    formula2 = DriverTreeFormula(
        driver_type_id=1,
        driver_type="テストドライバー型",
        kpi="利益",
        formulas=["利益 = 売上 - コスト"],
    )
    test_data_seeder.db.add(formula1)
    test_data_seeder.db.add(formula2)
    await test_data_seeder.db.commit()

    service = DriverTreeMasterService(db_session)

    # Act: 売上のKPIを取得
    result_sales = await service.get_formulas(
        project_id=project.id,
        driver_type_id=1,
        kpi="売上",
        user_id=owner.id,
    )

    # Act: 利益のKPIを取得
    result_profit = await service.get_formulas(
        project_id=project.id,
        driver_type_id=1,
        kpi="利益",
        user_id=owner.id,
    )

    # Assert
    assert result_sales["formula"]["kpi"] == "売上"
    assert result_profit["formula"]["kpi"] == "利益"
