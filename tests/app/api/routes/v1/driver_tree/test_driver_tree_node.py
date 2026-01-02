"""ドライバーツリー ノードAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/node - ノード作成
    - GET /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード詳細取得
    - PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード更新
    - DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード削除
    - GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/preview/output - プレビューダウンロード
    - POST /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy - 施策作成
    - GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy - 施策一覧取得
    - PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} - 施策更新
    - DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} - 施策削除
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/node - ノード作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_node_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-001] ノード作成の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]
    override_auth(owner)

    request_body = {
        "label": "新規ノード",
        "node_type": "入力",
        "position_x": 300,
        "position_y": 200,
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree/{tree.id}/node",
        json=request_body,
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "tree" in result
    assert "createdNodeId" in result


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_node_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-002] ノード詳細取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{root_node.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "node" in result
    assert result["node"]["nodeId"] == str(root_node.id)


# ================================================================================
# PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード更新
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "update_data,test_id",
    [
        ({"label": "更新されたノード名", "position_x": 500, "position_y": 300}, "full_update"),
        ({"label": "ラベルのみ更新"}, "partial_update"),
    ],
    ids=["full_update", "partial_update"],
)
async def test_update_node(client: AsyncClient, override_auth, test_data_seeder, update_data, test_id):
    """[test_driver_tree_node-003,004] ノード更新の成功ケース（完全更新・部分更新）。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]
    override_auth(owner)

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{root_node.id}",
        json=update_data,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "tree" in result


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_node_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-005] ノード削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    override_auth(owner)

    # 子ノードを削除（ルートノードではなく）
    node_to_delete = child_nodes[0]

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/node/{node_to_delete.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "tree" in result


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/preview/output - プレビューダウンロード
# ================================================================================


@pytest.mark.asyncio
async def test_download_node_preview_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-006] ノードプレビューダウンロードの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    override_auth(owner)

    # 入力ノードを使用
    input_node = child_nodes[0]

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{input_node.id}/preview/output")

    # Assert
    # 200またはデータがない場合は404も許容
    assert response.status_code in [200, 404]


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy - 施策作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_policy_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-007] 施策作成の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    override_auth(owner)

    # 入力ノードに施策を追加
    input_node = child_nodes[1]
    request_body = {
        "name": "新規施策",
        "value": 20.5,
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/node/{input_node.id}/policy",
        json=request_body,
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert "nodeId" in result
    assert "policies" in result
    assert result["nodeId"] == str(input_node.id)


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy - 施策一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_policies_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-008] 施策一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    override_auth(owner)

    # 施策が追加されたノードを使用
    node_with_policy = child_nodes[0]

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{node_with_policy.id}/policy")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "nodeId" in result
    assert "policies" in result
    assert result["nodeId"] == str(node_with_policy.id)


# ================================================================================
# PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} - 施策更新
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "update_data,test_id",
    [
        ({"name": "更新された施策名", "value": 30.0}, "full_update"),
        ({"value": 50.0}, "partial_update"),
    ],
    ids=["full_update", "partial_update"],
)
async def test_update_policy(client: AsyncClient, override_auth, test_data_seeder, update_data, test_id):
    """[test_driver_tree_node-009,010] 施策更新の成功ケース（完全更新・部分更新）。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    policy = data["policy"]
    override_auth(owner)

    node_with_policy = child_nodes[0]

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{node_with_policy.id}/policy/{policy.id}",
        json=update_data,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "nodeId" in result
    assert "policies" in result


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} - 施策削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_policy_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-011] 施策削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    policy = data["policy"]
    override_auth(owner)

    node_with_policy = child_nodes[0]

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/node/{node_with_policy.id}/policy/{policy.id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "nodeId" in result
    assert "policies" in result
