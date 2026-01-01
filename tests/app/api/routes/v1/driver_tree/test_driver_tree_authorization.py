"""Driver Tree API共通認証・認可テスト。

このテストファイルは、Driver Tree APIエンドポイント全体に適用される
認証・認可の動作を検証します。

個別エンドポイントでの認証・認可テストは不要となります。
代表的なエンドポイントでの検証により、全エンドポイントの
認証・認可が機能することを保証します。

検証対象HTTPメソッド:
    - GET: ツリー一覧取得
    - POST: ノード作成
    - PATCH: ノード更新
    - DELETE: ノード削除
"""

import uuid

import pytest
from httpx import AsyncClient


# ================================================================================
# 認証テスト（Unauthorized - 認証なし）
# ================================================================================


@pytest.mark.asyncio
async def test_driver_tree_get_unauthorized(client: AsyncClient):
    """[test_driver_tree_authorization-001] 認証なしでのツリー一覧GETリクエスト拒否。

    認証トークンなしでGETリクエストを送信した場合、
    401 Unauthorizedまたは403 Forbiddenが返されることを確認します。
    """
    # Arrange
    project_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{project_id}/driver-tree/tree")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_driver_tree_post_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree_authorization-002] 認証なしでのノード作成POSTリクエスト拒否。

    認証トークンなしでPOSTリクエストを送信した場合、
    401 Unauthorizedまたは403 Forbiddenが返されることを確認します。
    """
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
async def test_driver_tree_patch_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree_authorization-003] 認証なしでのノード更新PATCHリクエスト拒否。

    認証トークンなしでPATCHリクエストを送信した場合、
    401 Unauthorizedまたは403 Forbiddenが返されることを確認します。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    node = data["child_nodes"][0]  # 最初の子ノードを使用

    request_body = {
        "label": "更新後ノード",
    }

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{node.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_driver_tree_delete_unauthorized(client: AsyncClient, test_data_seeder):
    """[test_driver_tree_authorization-004] 認証なしでのノード削除DELETEリクエスト拒否。

    認証トークンなしでDELETEリクエストを送信した場合、
    401 Unauthorizedまたは403 Forbiddenが返されることを確認します。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    node = data["child_nodes"][0]  # 最初の子ノードを使用

    # Act
    response = await client.delete(
        f"/api/v1/project/{project.id}/driver-tree/node/{node.id}"
    )

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# プロジェクトアクセス権テスト（Forbidden - プロジェクトメンバー以外）
# ================================================================================


@pytest.mark.asyncio
async def test_driver_tree_get_forbidden_no_access(
    client: AsyncClient, override_auth, test_data_seeder
):
    """[test_driver_tree_authorization-005] プロジェクトアクセス権なしでのツリー一覧GETリクエスト拒否。

    認証済みだが、プロジェクトメンバーではないユーザーによるGETリクエストで、
    403 Forbiddenまたは404 Not Foundが返されることを確認します。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/driver-tree/tree")

    # Assert
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_driver_tree_post_forbidden_no_access(
    client: AsyncClient, override_auth, test_data_seeder
):
    """[test_driver_tree_authorization-006] プロジェクトアクセス権なしでのノード作成POSTリクエスト拒否。

    認証済みだが、プロジェクトメンバーではないユーザーによるPOSTリクエストで、
    403 Forbiddenまたは404 Not Foundが返されることを確認します。
    """
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
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_driver_tree_patch_forbidden_no_access(
    client: AsyncClient, override_auth, test_data_seeder
):
    """[test_driver_tree_authorization-007] プロジェクトアクセス権なしでのノード更新PATCHリクエスト拒否。

    認証済みだが、プロジェクトメンバーではないユーザーによるPATCHリクエストで、
    403 Forbiddenまたは404 Not Foundが返されることを確認します。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    node = data["child_nodes"][0]  # 最初の子ノードを使用
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    request_body = {
        "label": "更新後ノード",
    }

    # Act
    response = await client.patch(
        f"/api/v1/project/{project.id}/driver-tree/node/{node.id}",
        json=request_body,
    )

    # Assert
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_driver_tree_delete_forbidden_no_access(
    client: AsyncClient, override_auth, test_data_seeder
):
    """[test_driver_tree_authorization-008] プロジェクトアクセス権なしでのノード削除DELETEリクエスト拒否。

    認証済みだが、プロジェクトメンバーではないユーザーによるDELETEリクエストで、
    403 Forbiddenまたは404 Not Foundが返されることを確認します。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    node = data["child_nodes"][0]  # 最初の子ノードを使用
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    # Act
    response = await client.delete(
        f"/api/v1/project/{project.id}/driver-tree/node/{node.id}"
    )

    # Assert
    assert response.status_code in [403, 404]
