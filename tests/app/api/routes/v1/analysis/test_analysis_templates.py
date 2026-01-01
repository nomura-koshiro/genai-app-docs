"""分析テンプレートAPIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/project/{project_id}/analysis/template - テンプレート一覧取得
    - GET /api/v1/project/{project_id}/analysis/template/{issue_id} - テンプレート詳細取得
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/project/{project_id}/analysis/template - テンプレート一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_templates_success(client: AsyncClient, override_auth, project_with_owner):
    """[test_analysis_templates-001] テンプレート一覧取得の成功ケース。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/template")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_templates_unauthorized(client: AsyncClient):
    """[test_analysis_templates-002] 認証なしでのテンプレート一覧取得拒否。"""
    # Arrange
    project_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{project_id}/analysis/template")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_templates_project_not_found(client: AsyncClient, override_auth, regular_user):
    """[test_analysis_templates-003] 存在しないプロジェクトのテンプレート一覧取得。"""
    # Arrange
    override_auth(regular_user)
    nonexistent_project_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{nonexistent_project_id}/analysis/template")

    # Assert
    # テンプレートはプロジェクトに依存せずマスタデータとして返される
    assert response.status_code == 200


# ================================================================================
# GET /api/v1/project/{project_id}/analysis/template/{issue_id} - テンプレート詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient, override_auth, project_with_owner):
    """[test_analysis_templates-004] 存在しないテンプレートの取得。"""
    # Arrange
    project, owner = project_with_owner
    override_auth(owner)
    nonexistent_issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/template/{nonexistent_issue_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_template_unauthorized(client: AsyncClient):
    """[test_analysis_templates-005] 認証なしでのテンプレート詳細取得拒否。"""
    # Arrange
    project_id = str(uuid.uuid4())
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{project_id}/analysis/template/{issue_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_template_project_not_found(client: AsyncClient, override_auth, regular_user):
    """[test_analysis_templates-006] 存在しないプロジェクトのテンプレート詳細取得。"""
    # Arrange
    override_auth(regular_user)
    nonexistent_project_id = str(uuid.uuid4())
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{nonexistent_project_id}/analysis/template/{issue_id}")

    # Assert
    # プロジェクトが存在しないか、アクセス権限がない場合
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_get_template_non_member_access(client: AsyncClient, override_auth, project_with_owner, regular_user):
    """[test_analysis_templates-007] プロジェクト非メンバーによるテンプレート詳細取得。"""
    # Arrange
    project, _ = project_with_owner
    override_auth(regular_user)  # プロジェクトのメンバーではないユーザー
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/project/{project.id}/analysis/template/{issue_id}")

    # Assert
    # テンプレートはプロジェクトメンバーシップに依存せずアクセス可能
    # 存在しないテンプレートIDの場合は404が返る
    assert response.status_code == 404
