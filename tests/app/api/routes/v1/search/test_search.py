"""グローバル検索APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/search - グローバル検索
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/search - グローバル検索
# ================================================================================


@pytest.mark.asyncio
async def test_search_success(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_search-001] グローバル検索の成功ケース。"""
    # Arrange
    # プロジェクトを作成（検索対象）
    project, owner = await test_data_seeder.create_project_with_owner(
        owner=regular_user,
        name="検索テストプロジェクト",
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/search?q=検索テスト")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "検索テスト"


@pytest.mark.asyncio
async def test_search_with_type_filter(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_search-002] タイプフィルター付きグローバル検索。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner(
        owner=regular_user,
        name="タイプフィルターテスト",
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act - プロジェクトのみ検索
    response = await client.get("/api/v1/search?q=タイプフィルター&type=project")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "types" in data
    # typeフィルターが適用されていることを確認
    for result in data["results"]:
        assert result["type"] == "project"


@pytest.mark.asyncio
async def test_search_with_project_id_filter(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_search-003] プロジェクトID絞り込み付きグローバル検索。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner(
        owner=regular_user,
        name="プロジェクト内検索テスト",
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.get(f"/api/v1/search?q=検索&project_id={project.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_search_with_limit(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_search-004] 件数制限付きグローバル検索。"""
    # Arrange
    # 複数のプロジェクトを作成
    for i in range(5):
        await test_data_seeder.create_project_with_owner(
            owner=regular_user,
            name=f"制限テストプロジェクト{i}",
        )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/search?q=制限テスト&limit=2")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2


@pytest.mark.asyncio
async def test_search_validation_error_short_query(
    client: AsyncClient, override_auth, regular_user
):
    """[test_search-005] 検索クエリが短すぎる場合のバリデーションエラー。"""
    # Arrange
    override_auth(regular_user)

    # Act - 1文字で検索（2文字以上必要）
    response = await client.get("/api/v1/search?q=a")

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_no_results(
    client: AsyncClient, override_auth, regular_user
):
    """[test_search-006] 検索結果が0件の場合。"""
    # Arrange
    override_auth(regular_user)

    # Act - 存在しないキーワードで検索
    response = await client.get("/api/v1/search?q=絶対に存在しないキーワード12345")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


@pytest.mark.asyncio
async def test_search_multiple_types(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_search-007] 複数タイプ指定でのグローバル検索。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner(
        owner=regular_user,
        name="複数タイプテスト",
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act - 複数タイプを指定（カンマ区切り）
    response = await client.get("/api/v1/search?q=複数タイプ&type=project,session")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "types" in data
