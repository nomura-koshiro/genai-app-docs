"""Admin API共通認証・認可テスト。

このテストファイルは、Admin APIエンドポイント全体に適用される
認証・認可ミドルウェアの動作を検証します。

個別エンドポイントでの認証・認可テストは不要となります。
代表的なエンドポイントでミドルウェアの動作を確認することで、
全エンドポイントの認証・認可が機能することを保証します。

テスト対象エンドポイント（代表例）:
    - GET /api/v1/admin/category - 一覧取得
    - POST /api/v1/admin/category - 作成
    - PATCH /api/v1/admin/category/{category_id} - 更新
    - DELETE /api/v1/admin/category/{category_id} - 削除
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# 認証テスト（Unauthorized）
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,endpoint,request_body",
    [
        ("GET", "/api/v1/admin/category", None),
        (
            "POST",
            "/api/v1/admin/category",
            {
                "categoryId": 100,
                "categoryName": "テストカテゴリ",
                "industryId": 1,
                "industryName": "テスト業界",
                "driverTypeId": 1,
                "driverType": "テストドライバー型",
            },
        ),
        ("PATCH", "/api/v1/admin/category/1", {"categoryName": "更新カテゴリ"}),
        ("DELETE", "/api/v1/admin/category/1", None),
    ],
    ids=["get", "post", "patch", "delete"],
)
async def test_admin_api_unauthorized(
    client: AsyncClient,
    method: str,
    endpoint: str,
    request_body: dict | None,
):
    """[test_admin_authorization-001-004] 認証なしでのAdmin APIリクエスト拒否。

    認証トークンなしでAdmin APIエンドポイントにアクセスした場合、
    401または403ステータスコードを返すことを検証します。

    テストケース:
        - GET: 一覧取得
        - POST: カテゴリ作成
        - PATCH: カテゴリ更新
        - DELETE: カテゴリ削除
    """
    # Act
    response = await client.request(method, endpoint, json=request_body)

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# 認可テスト（Forbidden - Regular User）
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,endpoint,request_body",
    [
        ("GET", "/api/v1/admin/category", None),
        (
            "POST",
            "/api/v1/admin/category",
            {
                "categoryId": 100,
                "categoryName": "テストカテゴリ",
                "industryId": 1,
                "industryName": "テスト業界",
                "driverTypeId": 1,
                "driverType": "テストドライバー型",
            },
        ),
        ("PATCH", "/api/v1/admin/category/1", {"categoryName": "更新カテゴリ"}),
        ("DELETE", "/api/v1/admin/category/1", None),
    ],
    ids=["get", "post", "patch", "delete"],
)
async def test_admin_api_forbidden_regular_user(
    client: AsyncClient,
    override_auth,
    regular_user,
    method: str,
    endpoint: str,
    request_body: dict | None,
):
    """[test_admin_authorization-005-008] 一般ユーザーでのAdmin APIリクエスト拒否。

    一般ユーザー権限でAdmin APIエンドポイントにアクセスした場合、
    403ステータスコード（Forbidden）を返すことを検証します。

    テストケース:
        - GET: 一覧取得
        - POST: カテゴリ作成
        - PATCH: カテゴリ更新
        - DELETE: カテゴリ削除
    """
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.request(method, endpoint, json=request_body)

    # Assert
    assert response.status_code == 403
