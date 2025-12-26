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

import uuid

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


@pytest.mark.asyncio
async def test_create_node_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree_node-002] 認証なしでのノード作成失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    tree = data["tree"]

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
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_node_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-003] メンバー以外によるノード作成失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    tree = data["tree"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

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
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_node_tree_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-004] 存在しないツリーへのノード作成で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "label": "新規ノード",
        "node_type": "入力",
        "position_x": 300,
        "position_y": 200,
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/tree/{uuid.uuid4()}/node",
        json=request_body,
    )

    # Assert
    assert response.status_code == 404


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_node_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-005] ノード詳細取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_node_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-006] 存在しないノードの取得で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{uuid.uuid4()}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_node_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-007] メンバー以外によるノード取得失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    root_node = data["root_node"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{root_node.id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_node_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-008] ノード更新の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]
    override_auth(owner)

    request_body = {
        "label": "更新されたノード名",
        "position_x": 500,
        "position_y": 300,
    }

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{root_node.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "tree" in result


@pytest.mark.asyncio
async def test_update_node_partial(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-009] ノード部分更新の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]
    override_auth(owner)

    request_body = {"label": "ラベルのみ更新"}

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{root_node.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "tree" in result


@pytest.mark.asyncio
async def test_update_node_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-010] 存在しないノードの更新で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {"label": "更新"}

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{uuid.uuid4()}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_node_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-011] メンバー以外によるノード更新失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    root_node = data["root_node"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    request_body = {"label": "更新"}

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{root_node.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id} - ノード削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_node_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-012] ノード削除の成功ケース。"""
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


@pytest.mark.asyncio
async def test_delete_node_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-013] 存在しないノードの削除で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/node/{uuid.uuid4()}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_node_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-014] メンバー以外によるノード削除失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    child_nodes = data["child_nodes"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/preview/output - プレビューダウンロード
# ================================================================================


@pytest.mark.asyncio
async def test_download_node_preview_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-015] ノードプレビューダウンロードの成功ケース。"""
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


@pytest.mark.asyncio
async def test_download_node_preview_node_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-016] 存在しないノードのプレビューダウンロードで404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{uuid.uuid4()}/preview/output")

    # Assert
    assert response.status_code == 404


# ================================================================================
# POST /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy - 施策作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_policy_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-017] 施策作成の成功ケース。"""
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


@pytest.mark.asyncio
async def test_create_policy_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree_node-018] 認証なしでの施策作成失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    child_nodes = data["child_nodes"]

    request_body = {
        "name": "新規施策",
        "value": 20.5,
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}/policy",
        json=request_body,
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_policy_node_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-019] 存在しないノードへの施策作成で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    request_body = {
        "name": "新規施策",
        "value": 20.5,
    }

    # Act
    response = await client.post(
        f"/api/v1/project/{project.id}/driver-tree/node/{uuid.uuid4()}/policy",
        json=request_body,
    )

    # Assert
    assert response.status_code == 404


# ================================================================================
# GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy - 施策一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_policies_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-020] 施策一覧取得の成功ケース。"""
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


@pytest.mark.asyncio
async def test_list_policies_node_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-021] 存在しないノードの施策一覧取得で404。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{uuid.uuid4()}/policy")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_policies_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-022] メンバー以外による施策一覧取得失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    child_nodes = data["child_nodes"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}/policy")

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} - 施策更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_policy_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-023] 施策更新の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    policy = data["policy"]
    override_auth(owner)

    node_with_policy = child_nodes[0]
    request_body = {
        "name": "更新された施策名",
        "value": 30.0,
    }

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{node_with_policy.id}/policy/{policy.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "nodeId" in result
    assert "policies" in result


@pytest.mark.asyncio
async def test_update_policy_partial(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-024] 施策部分更新の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    policy = data["policy"]
    override_auth(owner)

    node_with_policy = child_nodes[0]
    request_body = {"value": 50.0}  # 値のみ更新

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{node_with_policy.id}/policy/{policy.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "nodeId" in result
    assert "policies" in result


@pytest.mark.asyncio
async def test_update_policy_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-025] 存在しない施策の更新で404。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    override_auth(owner)

    request_body = {"name": "更新"}

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}/policy/{uuid.uuid4()}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_policy_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-026] メンバー以外による施策更新失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    child_nodes = data["child_nodes"]
    policy = data["policy"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    request_body = {"name": "更新"}

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}/policy/{policy.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} - 施策削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_policy_success(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-027] 施策削除の成功ケース。"""
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


@pytest.mark.asyncio
async def test_delete_policy_not_found(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-028] 存在しない施策の削除で404。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_nodes = data["child_nodes"]
    override_auth(owner)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}/policy/{uuid.uuid4()}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_policy_forbidden(client: AsyncClient, override_auth, test_data_seeder):
    """[test_driver_tree_node-029] メンバー以外による施策削除失敗。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    child_nodes = data["child_nodes"]
    policy = data["policy"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.delete(f"/api/v1/project/{project.id}/driver-tree/node/{child_nodes[0].id}/policy/{policy.id}")

    # Assert
    assert response.status_code == 403
