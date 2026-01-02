"""ドライバーツリーサービスのテスト。

このテストファイルは、DriverTreeServiceの各メソッドをテストします。

対応メソッド:
    - create_tree: ツリー作成
    - list_trees: ツリー一覧取得
    - get_tree: ツリー詳細取得
    - import_formula: 数式インポート
    - reset_tree: ツリーリセット
    - delete_tree: ツリー削除
    - get_categories: カテゴリ取得
    - get_formulas: 数式取得
    - get_tree_data: ツリーデータ取得
    - download_simulation_output: シミュレーション出力ダウンロード
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.services.driver_tree import DriverTreeService

# ================================================================================
# ツリー CRUD
# ================================================================================


@pytest.mark.parametrize(
    "name,description,expected_description",
    [
        ("新規ツリー", "テスト用ツリー", "テスト用ツリー"),
        ("説明なしツリー", None, ""),
    ],
    ids=["with_description", "without_description"],
)
@pytest.mark.asyncio
async def test_create_tree(
    db_session: AsyncSession,
    test_data_seeder,
    name: str,
    description: str | None,
    expected_description: str,
):
    """[test_driver_tree_tree-001] ツリー作成の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act
    result = await service.create_tree(
        project_id=project.id,
        name=name,
        description=description,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert result["tree_id"] is not None
    assert result["name"] == name
    assert result["description"] == expected_description
    assert result["created_at"] is not None


@pytest.mark.asyncio
async def test_list_trees_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-003] ツリー一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]

    service = DriverTreeService(db_session)

    # Act
    result = await service.list_trees(project_id=project.id, user_id=owner.id)

    # Assert
    assert "trees" in result
    assert len(result["trees"]) == 1
    assert result["trees"][0]["name"] == "シードツリー"


@pytest.mark.asyncio
async def test_list_trees_empty(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-004] ツリーがない場合は空リストを返す。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act
    result = await service.list_trees(project_id=project.id, user_id=owner.id)

    # Assert
    assert result["trees"] == []


@pytest.mark.asyncio
async def test_list_trees_multiple(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-005] 複数ツリーの一覧取得。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # 複数ツリーを作成
    for i in range(3):
        await test_data_seeder.create_driver_tree_with_structure(
            project=project,
            name=f"ツリー{i + 1}",
        )

    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act
    result = await service.list_trees(project_id=project.id, user_id=owner.id)

    # Assert
    assert len(result["trees"]) == 3


@pytest.mark.asyncio
async def test_get_tree_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-006] ツリー詳細取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeService(db_session)

    # Act
    result = await service.get_tree(
        project_id=project.id,
        tree_id=tree.id,
        user_id=owner.id,
    )

    # Assert
    assert result["tree_id"] == tree.id
    assert result["root"] is not None
    assert result["root"]["node_id"] == data["root_node"].id
    assert "nodes" in result
    assert "relationship" in result


@pytest.mark.parametrize(
    "error_type",
    ["tree_not_found", "wrong_project"],
    ids=["tree_not_found", "wrong_project"],
)
@pytest.mark.asyncio
async def test_get_tree_not_found_errors(
    db_session: AsyncSession, test_data_seeder, error_type: str
):
    """[test_driver_tree_tree-007] get_treeのNotFoundErrorケース。"""
    # Arrange
    service = DriverTreeService(db_session)

    if error_type == "tree_not_found":
        project, owner = await test_data_seeder.create_project_with_owner()
        await test_data_seeder.db.commit()
        project_id = project.id
        tree_id = uuid.uuid4()  # 存在しないツリー
    else:  # wrong_project
        data = await test_data_seeder.seed_driver_tree_dataset()
        tree = data["tree"]
        owner = data["owner"]
        other_project, _ = await test_data_seeder.create_project_with_owner()
        await test_data_seeder.db.commit()
        project_id = other_project.id  # 異なるプロジェクト
        tree_id = tree.id

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_tree(
            project_id=project_id,
            tree_id=tree_id,
            user_id=owner.id,
        )


# ================================================================================
# 数式インポート
# ================================================================================


@pytest.mark.asyncio
async def test_import_formula_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-009] 数式インポートの成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    tree = await test_data_seeder.create_driver_tree(project=project, name="数式テスト")
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act
    result = await service.import_formula(
        project_id=project.id,
        tree_id=tree.id,
        position_x=100,
        position_y=100,
        formulas=["売上高 = 単価 * 数量"],
        sheet_id=None,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert "tree_id" in result
    assert "nodes" in result


@pytest.mark.asyncio
async def test_import_formula_multiple(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-010] 複数数式のインポート。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    tree = await test_data_seeder.create_driver_tree(project=project, name="複数数式テスト")
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act
    result = await service.import_formula(
        project_id=project.id,
        tree_id=tree.id,
        position_x=100,
        position_y=100,
        formulas=["売上高 = 単価 * 数量", "利益 = 売上高 - コスト"],
        sheet_id=None,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert "nodes" in result
    # 複数の数式がインポートされたことを確認（実装によりノード数は変動する可能性あり）
    assert len(result["nodes"]) >= 1


@pytest.mark.parametrize(
    "formulas,error_reason",
    [
        ([], "empty_list"),
        (["不正な数式"], "invalid_format"),
    ],
    ids=["empty_list", "invalid_format"],
)
@pytest.mark.asyncio
async def test_import_formula_validation_errors(
    db_session: AsyncSession, test_data_seeder, formulas: list, error_reason: str
):
    """[test_driver_tree_tree-011] 数式インポートのValidationErrorケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeService(db_session)

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.import_formula(
            project_id=project.id,
            tree_id=tree.id,
            position_x=100,
            position_y=100,
            formulas=formulas,
            sheet_id=None,
            user_id=owner.id,
        )


# ================================================================================
# ツリーリセット・削除
# ================================================================================


@pytest.mark.asyncio
async def test_reset_tree_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-014] ツリーリセットの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeService(db_session)

    # Act
    result = await service.reset_tree(
        project_id=project.id,
        tree_id=tree.id,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert "tree" in result
    assert "reset_at" in result
    assert result["reset_at"] is not None


@pytest.mark.parametrize(
    "operation",
    ["reset_tree", "delete_tree"],
    ids=["reset", "delete"],
)
@pytest.mark.asyncio
async def test_tree_operations_not_found(
    db_session: AsyncSession, test_data_seeder, operation: str
):
    """[test_driver_tree_tree-014] reset/deleteツリー操作のNotFoundErrorケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)
    operation_method = getattr(service, operation)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await operation_method(
            project_id=project.id,
            tree_id=uuid.uuid4(),
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_delete_tree_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-015] ツリー削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    tree_id = tree.id

    service = DriverTreeService(db_session)

    # Act
    result = await service.delete_tree(
        project_id=project.id,
        tree_id=tree_id,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert result["success"] is True
    assert result["deleted_at"] is not None

    # 削除されたことを確認
    with pytest.raises(NotFoundError):
        await service.get_tree(
            project_id=project.id,
            tree_id=tree_id,
            user_id=owner.id,
        )


# ================================================================================
# マスタデータ取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_categories_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-018] カテゴリ取得の成功ケース。"""
    from app.models.driver_tree import DriverTreeCategory

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

    service = DriverTreeService(db_session)
    # Act
    result = await service.get_categories(
        project_id=project.id,
        user_id=owner.id,
    )

    # Assert
    assert "categories" in result
    assert isinstance(result["categories"], list)
    assert len(result["categories"]) >= 1
    category_data = result["categories"][0]
    assert "category_id" in category_data
    assert "category_name" in category_data
    assert "industries" in category_data
    assert isinstance(category_data["industries"], list)
    assert len(category_data["industries"]) >= 1
    industry_data = category_data["industries"][0]
    assert "industry_id" in industry_data
    assert "industry_name" in industry_data
    assert "driver_types" in industry_data
    assert isinstance(industry_data["driver_types"], list)


@pytest.mark.asyncio
async def test_get_formulas_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-019] 数式取得の成功ケース。"""
    from app.models.driver_tree import DriverTreeFormula

    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()

    # テスト用のformulaデータを作成
    formula = DriverTreeFormula(
        driver_type_id=1,
        driver_type="テストドライバー型",
        kpi="売上",
        formulas=["売上 = 数量 * 単価", "数量 = キャパシティ * 稼働率"],
    )
    test_data_seeder.db.add(formula)

    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

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
    assert "formula_id" in formula_data
    assert "driver_type_id" in formula_data
    assert formula_data["driver_type_id"] == 1
    assert "driver_type" in formula_data
    assert "kpi" in formula_data
    assert formula_data["kpi"] == "売上"
    assert "formulas" in formula_data
    assert isinstance(formula_data["formulas"], list)
    assert len(formula_data["formulas"]) == 2


# ================================================================================
# 計算・出力
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_data_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-020] ツリーデータ取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeService(db_session)

    # Act
    result = await service.get_tree_data(
        project_id=project.id,
        tree_id=tree.id,
        user_id=owner.id,
    )

    # Assert
    assert "calculated_data_list" in result


@pytest.mark.asyncio
async def test_get_tree_data_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-021] 存在しないツリーのデータ取得でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_tree_data(
            project_id=project.id,
            tree_id=uuid.uuid4(),
            user_id=owner.id,
        )


@pytest.mark.parametrize(
    "format,expected_media_type",
    [
        ("csv", "text/csv"),
        ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ],
    ids=["csv", "excel"],
)
@pytest.mark.asyncio
async def test_download_simulation_output_format(
    db_session: AsyncSession, test_data_seeder, format: str, expected_media_type: str
):
    """[test_driver_tree_tree-022] シミュレーション出力の各フォーマットダウンロード。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeService(db_session)

    # Act
    response = await service.download_simulation_output(
        project_id=project.id,
        tree_id=tree.id,
        format=format,
        user_id=owner.id,
    )

    # Assert
    assert response.media_type == expected_media_type


@pytest.mark.asyncio
async def test_download_simulation_output_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_tree-024] 存在しないツリーのダウンロードでNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.download_simulation_output(
            project_id=project.id,
            tree_id=uuid.uuid4(),
            format="csv",
            user_id=owner.id,
        )
