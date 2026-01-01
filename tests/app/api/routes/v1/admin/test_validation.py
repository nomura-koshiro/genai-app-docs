"""検証マスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/validation - 検証マスタ一覧取得
    - GET /api/v1/admin/validation/{validation_id} - 検証マスタ詳細取得
    - POST /api/v1/admin/validation - 検証マスタ作成
    - PATCH /api/v1/admin/validation/{validation_id} - 検証マスタ更新
    - DELETE /api/v1/admin/validation/{validation_id} - 検証マスタ削除
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/validation - 検証マスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_validations_success(client: AsyncClient, override_auth, admin_user):
    """[test_validation-001] 検証マスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/validation")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "validations" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_validations_with_pagination(client: AsyncClient, override_auth, admin_user):
    """[test_validation-002] ページネーション付き検証マスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(
        "/api/v1/admin/validation",
        params={
            "skip": 0,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "validations" in data
