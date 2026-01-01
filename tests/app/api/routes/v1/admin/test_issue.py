"""課題マスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/issue - 課題マスタ一覧取得
    - GET /api/v1/admin/issue/{issue_id} - 課題マスタ詳細取得
    - POST /api/v1/admin/issue - 課題マスタ作成
    - PATCH /api/v1/admin/issue/{issue_id} - 課題マスタ更新
    - DELETE /api/v1/admin/issue/{issue_id} - 課題マスタ削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/issue - 課題マスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_issues_success(client: AsyncClient, override_auth, admin_user):
    """[test_issue-001] 課題マスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/issue")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_issues_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_issue-002] フィルタ付き課題マスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)
    validation_id = str(uuid.uuid4())

    # Act
    response = await client.get(
        "/api/v1/admin/issue",
        params={
            "skip": 0,
            "limit": 10,
            "validationId": validation_id,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
