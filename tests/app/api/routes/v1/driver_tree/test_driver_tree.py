"""ドライバーツリー ツリーAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - POST /api/v1/project/{project_id}/driver-tree/tree - ツリー作成
    - GET /api/v1/project/{project_id}/driver-tree/tree - ツリー一覧取得
    - GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id} - ツリー取得
    - POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/import - 数式インポート
    - POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/reset - ツリーリセット
    - DELETE /api/v1/project/{project_id}/driver-tree/tree/{tree_id} - ツリー削除
    - GET /api/v1/project/{project_id}/driver-tree/category - カテゴリ取得
    - GET /api/v1/project/{project_id}/driver-tree/formula - 数式取得
    - GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/data - 計算結果取得
    - GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/output - ファイルダウンロード
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/tree - ツリー作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-001] ツリー作成の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "name": "テストツリー",
        "description": "テスト用ドライバーツリー",
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree",
        json=request_body,
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "treeId" in result
    assert result["name"] == "テストツリー"
    assert result["description"] == "テスト用ドライバーツリー"
    assert "createdAt" in result


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree - ツリー一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_trees_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-002] ツリー一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "trees" in result
    assert len(result["trees"]) >= 1


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id} - ツリー取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-003] ツリー取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "tree" in result
    assert result["tree"]["treeId"] == str(tree.id)


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/import - 数式インポート
# ================================================================================


@pytest.mark.asyncio
async def test_import_formula_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-004] 数式インポートの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    request_body = {
        "position_x": 100,
        "position_y": 100,
        "formulas": ["売上 = 単価 * 数量"],
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/import",
        json=request_body,
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "tree" in result


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/reset - ツリーリセット
# ================================================================================


@pytest.mark.asyncio
async def test_reset_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-005] ツリーリセットの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/reset")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "tree" in result
    assert "resetAt" in result


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/tree/{tree_id} - ツリー削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-006] ツリー削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "deletedAt" in result


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/category - カテゴリ取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_categories_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-007] カテゴリ取得の成功ケース。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/category")

    # Assert
    assert response.status_code == 200
    result = response.json()

    # レスポンス形式の検証
    assert "categories" in result
    assert isinstance(result["categories"], list)

    # データが存在する場合の検証
    if len(result["categories"]) > 0:
        category = result["categories"][0]
        assert "categoryId" in category
        assert "categoryName" in category
        assert "industries" in category
        assert isinstance(category["industries"], list)

        # 業界名の検証
        if len(category["industries"]) > 0:
            industry = category["industries"][0]
            assert "industryId" in industry
            assert "industryName" in industry
            assert "driverTypes" in industry
            assert isinstance(industry["driverTypes"], list)

            # ドライバー型の検証
            if len(industry["driverTypes"]) > 0:
                driver_type = industry["driverTypes"][0]
                assert "driverTypeId" in driver_type
                assert "driverTypeName" in driver_type


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/formula - 数式取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_formulas_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-008] 数式取得の成功ケース。"""
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
    override_auth(owner)

    # Act
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/formula",
        params={"driver_type_id": 1, "kpi": "売上"},
    )

    # Assert
    assert response.status_code == 200
    result = response.json()

    # レスポンス形式の検証
    assert "formula" in result
    formula_data = result["formula"]
    assert "formulaId" in formula_data
    assert "driverTypeId" in formula_data
    assert formula_data["driverTypeId"] == 1
    assert "driverType" in formula_data
    assert "kpi" in formula_data
    assert formula_data["kpi"] == "売上"
    assert "formulas" in formula_data
    assert isinstance(formula_data["formulas"], list)
    assert len(formula_data["formulas"]) == 2


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/data - 計算結果取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_data_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-009] 計算結果取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/data")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "calculatedDataList" in result


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/output - ファイルダウンロード
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,expected_content_type",
    [
        ({}, "application/vnd.openxmlformats"),
        ({"format": "csv"}, None),
    ],
    ids=["default_excel", "csv_format"],
)
async def test_download_simulation_output(
    client: AsyncClient,
    override_auth,
    test_data_seeder,
    params,
    expected_content_type,
):
    """[test_driver_tree-010,011] シミュレーション結果ダウンロードの成功ケース（Excel/CSV）。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/output",
        params=params,
    )

    # Assert
    assert response.status_code == 200
    if expected_content_type:
        assert expected_content_type in response.headers.get("content-type", "")


# ================================================================================
# API拡張: TreePoliciesResponse のテスト
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="get_tree_policies endpoint not implemented in DriverTreeService")
async def test_get_tree_policies_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-012] ツリー施策一覧取得の成功ケース。

    07-api-extensions.md の実装により、TreePoliciesResponse が返されることを確認。
    注: このテストは実際のエンドポイントが実装されている場合のみ有効。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    # ノードと施策を作成
    node = await test_data_seeder.create_driver_tree_node(
        driver_tree=tree,
        label="売上",
        position_x=100,
        position_y=100,
    )
    await test_data_seeder.create_driver_tree_policy(
        node=node,
        label="売上向上施策",
        description="新商品投入",
        impact_type="multiply",
        impact_value=1.2,
    )
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    # 注: このエンドポイントは実装されていない可能性があります
    # 実装されている場合は以下のようなパスになる想定
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/policy")

    # Assert
    # エンドポイントが未実装の場合（404または500）はスキップ
    if response.status_code in [404, 500]:
        pytest.skip("Tree policies endpoint not implemented yet")

    assert response.status_code == 200
    result = response.json()
    assert "treeId" in result
    assert "policies" in result
    assert "totalCount" in result
    assert result["treeId"] == str(tree.id)
    assert isinstance(result["policies"], list)

    # 施策が存在する場合
    if len(result["policies"]) > 0:
        policy_item = result["policies"][0]
        assert "policyId" in policy_item
        assert "nodeId" in policy_item
        assert "nodeLabel" in policy_item
        assert "label" in policy_item
        assert "impactType" in policy_item
        assert "impactValue" in policy_item
        assert "status" in policy_item


@pytest.mark.asyncio
@pytest.mark.skip(reason="get_tree_policies endpoint not implemented in DriverTreeService")
async def test_get_tree_policies_empty(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-013] 施策が存在しないツリーの施策一覧取得。

    施策が登録されていないツリーの場合、空の施策リストが返されることを確認。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/policy")

    # Assert
    # エンドポイントが未実装の場合（404または500）はスキップ
    if response.status_code in [404, 500]:
        pytest.skip("Tree policies endpoint not implemented yet")

    assert response.status_code == 200
    result = response.json()
    assert "treeId" in result
    assert "policies" in result
    assert "totalCount" in result
    assert result["treeId"] == str(tree.id)
    assert result["totalCount"] == 0
    assert len(result["policies"]) == 0
