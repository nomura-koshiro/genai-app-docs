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


@pytest.mark.asyncio
async def test_list_issues_unauthorized(client: AsyncClient):
    """[test_issue-003] 認証なしでの課題マスタ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/issue")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_issues_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_issue-004] 一般ユーザーでの課題マスタ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/issue")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/issue/{issue_id} - 課題マスタ詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_issue_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_issue-005] 存在しない課題マスタの取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/issue/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_issue_unauthorized(client: AsyncClient):
    """[test_issue-006] 認証なしでの課題マスタ詳細取得拒否。"""
    # Arrange
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/issue/{issue_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_issue_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_issue-007] 一般ユーザーでの課題マスタ詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/issue/{issue_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/issue - 課題マスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_issue_unauthorized(client: AsyncClient):
    """[test_issue-008] 認証なしでの課題マスタ作成拒否。"""
    # Arrange
    issue_data = {
        "validationId": str(uuid.uuid4()),
        "name": "テスト課題",
        "description": "テスト用の課題です",
        "issueOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/issue", json=issue_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_issue_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_issue-009] 一般ユーザーでの課題マスタ作成拒否。"""
    # Arrange
    override_auth(regular_user)
    issue_data = {
        "validationId": str(uuid.uuid4()),
        "name": "テスト課題",
        "description": "テスト用の課題です",
        "issueOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/issue", json=issue_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/issue/{issue_id} - 課題マスタ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_issue_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_issue-010] 存在しない課題マスタの更新。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())
    update_data = {"name": "更新課題"}

    # Act
    response = await client.patch(f"/api/v1/admin/issue/{nonexistent_id}", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_issue_unauthorized(client: AsyncClient):
    """[test_issue-011] 認証なしでの課題マスタ更新拒否。"""
    # Arrange
    issue_id = str(uuid.uuid4())
    update_data = {"name": "更新課題"}

    # Act
    response = await client.patch(f"/api/v1/admin/issue/{issue_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_issue_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_issue-012] 一般ユーザーでの課題マスタ更新拒否。"""
    # Arrange
    override_auth(regular_user)
    issue_id = str(uuid.uuid4())
    update_data = {"name": "更新課題"}

    # Act
    response = await client.patch(f"/api/v1/admin/issue/{issue_id}", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/admin/issue/{issue_id} - 課題マスタ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_issue_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_issue-013] 存在しない課題マスタの削除。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/issue/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_issue_unauthorized(client: AsyncClient):
    """[test_issue-014] 認証なしでの課題マスタ削除拒否。"""
    # Arrange
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/issue/{issue_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_issue_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_issue-015] 一般ユーザーでの課題マスタ削除拒否。"""
    # Arrange
    override_auth(regular_user)
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/issue/{issue_id}")

    # Assert
    assert response.status_code == 403
