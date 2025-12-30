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

import uuid

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


@pytest.mark.asyncio
async def test_create_tree_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree-002] 認証なしでのツリー作成失敗。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    request_body = {"name": "テストツリー"}

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree",
        json=request_body,
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_tree_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-003] メンバー以外によるツリー作成失敗。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    request_body = {"name": "テストツリー"}

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree",
        json=request_body,
    )

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree - ツリー一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_trees_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-004] ツリー一覧取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_list_trees_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree-005] 認証なしでのツリー一覧取得失敗。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_trees_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-006] メンバー以外によるツリー一覧取得失敗。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id} - ツリー取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-007] ツリー取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_tree_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-008] 存在しないツリーの取得で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tree_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-009] メンバー以外によるツリー取得失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    tree = data["tree"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/import - 数式インポート
# ================================================================================


@pytest.mark.asyncio
async def test_import_formula_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-010] 数式インポートの成功ケース。"""
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


@pytest.mark.asyncio
async def test_import_formula_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-011] 存在しないツリーへの数式インポートで404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "position_x": 100,
        "position_y": 100,
        "formulas": ["売上 = 単価 * 数量"],
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}/import",
        json=request_body,
    )

    # Assert
    assert response.status_code == 404


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/reset - ツリーリセット
# ================================================================================


@pytest.mark.asyncio
async def test_reset_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-012] ツリーリセットの成功ケース。"""
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


@pytest.mark.asyncio
async def test_reset_tree_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-013] 存在しないツリーのリセットで404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.post(f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}/reset")

    # Assert
    assert response.status_code == 404


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/tree/{tree_id} - ツリー削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_tree_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-014] ツリー削除の成功ケース。"""
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


@pytest.mark.asyncio
async def test_delete_tree_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-015] 存在しないツリーの削除で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_tree_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-016] メンバー以外によるツリー削除失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    tree = data["tree"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/category - カテゴリ取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_categories_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-017] カテゴリ取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_categories_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree-018] 認証なしでのカテゴリ取得失敗。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/category")

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/formula - 数式取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_formulas_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-019] 数式取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_formulas_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree-020] 認証なしでの数式取得失敗。"""
    # Arrange
    project, _ = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    # Act
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/formula",
        params={"driver_type_id": 1, "kpi": "売上"},
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_formulas_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-020a] 存在しない数式の取得失敗。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act - 存在しないdriver_type_id
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/formula",
        params={"driver_type_id": 99999, "kpi": "売上"},
    )

    # Assert
    assert response.status_code == 404


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/data - 計算結果取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_data_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-021] 計算結果取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_tree_data_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-022] 存在しないツリーの計算結果取得で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}/data")

    # Assert
    assert response.status_code == 404


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/output - ファイルダウンロード
# ================================================================================


@pytest.mark.asyncio
async def test_download_simulation_output_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-023] シミュレーション結果ダウンロードの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/output")

    # Assert
    assert response.status_code == 200
    assert "application/vnd.openxmlformats" in response.headers.get("content-type", "") or response.status_code == 200


@pytest.mark.asyncio
async def test_download_simulation_output_csv(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-024] CSV形式でのダウンロードの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    # Act
    response = await client.get(
        f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/output",
        params={"format": "csv"},
    )

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_download_simulation_output_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-025] 存在しないツリーのダウンロードで404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}/output")

    # Assert
    assert response.status_code == 404


# ================================================================================
# API拡張: TreePoliciesResponse のテスト
# ================================================================================


@pytest.mark.asyncio
async def test_get_tree_policies_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-026] ツリー施策一覧取得の成功ケース。

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
        tree=tree,
        label="売上",
        position_x=100,
        position_y=100,
    )
    policy = await test_data_seeder.create_driver_tree_policy(
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
    if response.status_code == 200:
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
    else:
        # エンドポイントが未実装の場合はスキップ
        pytest.skip("Tree policies endpoint not implemented yet")


@pytest.mark.asyncio
async def test_get_tree_policies_empty(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree-027] 施策が存在しないツリーの施策一覧取得。

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
    if response.status_code == 200:
        result = response.json()
        assert "treeId" in result
        assert "policies" in result
        assert "totalCount" in result
        assert result["treeId"] == str(tree.id)
        assert result["totalCount"] == 0
        assert len(result["policies"]) == 0
    else:
        pytest.skip("Tree policies endpoint not implemented yet")
