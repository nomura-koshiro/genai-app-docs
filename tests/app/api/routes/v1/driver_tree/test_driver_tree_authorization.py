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
@pytest.mark.parametrize(
    "method,endpoint_template,needs_data,request_body",
    [
        ("GET", "/api/v1/project/{project_id}/driver-tree/tree", False, None),
        (
            "POST",
            "/api/v1/project/{project_id}/driver-tree/tree/{tree_id}/node",
            True,
            {
                "label": "新規ノード",
                "node_type": "入力",
                "position_x": 300,
                "position_y": 200,
            },
        ),
        (
            "PATCH",
            "/api/v1/project/{project_id}/driver-tree/node/{node_id}",
            True,
            {"label": "更新後ノード"},
        ),
        (
            "DELETE",
            "/api/v1/project/{project_id}/driver-tree/node/{node_id}",
            True,
            None,
        ),
    ],
    ids=["get", "post", "patch", "delete"],
)
async def test_driver_tree_unauthorized(
    client: AsyncClient,
    test_data_seeder,
    method: str,
    endpoint_template: str,
    needs_data: bool,
    request_body: dict | None,
):
    """[test_driver_tree_authorization-001-004] 認証なしでのリクエスト拒否。

    認証トークンなしでリクエストを送信した場合、
    401 Unauthorizedまたは403 Forbiddenが返されることを確認します。
    """
    # Arrange
    if needs_data:
        data = await test_data_seeder.seed_driver_tree_dataset()
        project = data["project"]
        tree = data["tree"]
        node = data["child_nodes"][0]  # 最初の子ノードを使用

        endpoint = endpoint_template.format(
            project_id=project.id, tree_id=tree.id, node_id=node.id
        )
    else:
        # GETの場合はランダムなproject_idを使用
        project_id = str(uuid.uuid4())
        endpoint = endpoint_template.format(project_id=project_id)

    # Act
    if method == "GET":
        response = await client.get(endpoint)
    elif method == "POST":
        response = await client.post(endpoint, json=request_body)
    elif method == "PATCH":
        response = await client.patch(endpoint, json=request_body)
    elif method == "DELETE":
        response = await client.delete(endpoint)

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# プロジェクトアクセス権テスト（Forbidden - プロジェクトメンバー以外）
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,endpoint_template,request_body",
    [
        ("GET", "/api/v1/project/{project_id}/driver-tree/tree", None),
        (
            "POST",
            "/api/v1/project/{project_id}/driver-tree/tree/{tree_id}/node",
            {
                "label": "新規ノード",
                "node_type": "入力",
                "position_x": 300,
                "position_y": 200,
            },
        ),
        (
            "PATCH",
            "/api/v1/project/{project_id}/driver-tree/node/{node_id}",
            {"label": "更新後ノード"},
        ),
        (
            "DELETE",
            "/api/v1/project/{project_id}/driver-tree/node/{node_id}",
            None,
        ),
    ],
    ids=["get", "post", "patch", "delete"],
)
async def test_driver_tree_forbidden_no_access(
    client: AsyncClient,
    override_auth,
    test_data_seeder,
    method: str,
    endpoint_template: str,
    request_body: dict | None,
):
    """[test_driver_tree_authorization-005-008] プロジェクトアクセス権なしでのリクエスト拒否。

    認証済みだが、プロジェクトメンバーではないユーザーによるリクエストで、
    403 Forbiddenまたは404 Not Foundが返されることを確認します。
    """
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    tree = data["tree"]
    node = data["child_nodes"][0]  # 最初の子ノードを使用
    other_user = await test_data_seeder.create_user(display_name="Other User")
    await test_data_seeder.db.commit()
    override_auth(other_user)

    endpoint = endpoint_template.format(
        project_id=project.id, tree_id=tree.id, node_id=node.id
    )

    # Act
    if method == "GET":
        response = await client.get(endpoint)
    elif method == "POST":
        response = await client.post(endpoint, json=request_body)
    elif method == "PATCH":
        response = await client.patch(endpoint, json=request_body)
    elif method == "DELETE":
        response = await client.delete(endpoint)

    # Assert
    assert response.status_code in [403, 404]
