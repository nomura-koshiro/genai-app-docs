"""分析テンプレートAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはRepository層でカバーされます。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_templates_success(client: AsyncClient, seeded_templates):
    """テンプレート一覧取得の成功ケース。"""
    # Act
    response = await client.get("/api/v1/analysis/templates?skip=0&limit=20")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # 最初のテンプレートの構造確認
    template = data[0]
    assert "id" in template
    assert "policy" in template
    assert "issue" in template
    assert "description" in template
    assert "agent_prompt" in template
    assert "initial_msg" in template
    assert "initial_axis" in template
    assert "is_active" in template
    assert "display_order" in template
    assert "created_at" in template
    assert "updated_at" in template


@pytest.mark.asyncio
async def test_list_templates_pagination(client: AsyncClient, seeded_templates):
    """ページネーション付きテンプレート一覧取得のテスト。"""
    # Act - 1ページ目
    response1 = await client.get("/api/v1/analysis/templates?skip=0&limit=2")

    # Assert
    assert response1.status_code == 200
    page1 = response1.json()
    assert isinstance(page1, list)
    assert len(page1) <= 2

    # Act - 2ページ目
    response2 = await client.get("/api/v1/analysis/templates?skip=2&limit=2")

    # Assert
    assert response2.status_code == 200
    page2 = response2.json()
    assert isinstance(page2, list)

    # 異なるページでは異なるテンプレートが返されることを確認
    if len(page1) > 0 and len(page2) > 0:
        page1_ids = {t["id"] for t in page1}
        page2_ids = {t["id"] for t in page2}
        # IDが重複していないことを確認
        assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_get_template_detail_success(client: AsyncClient, seeded_templates):
    """テンプレート詳細取得の成功ケース。"""
    # Arrange - まず一覧から1つのテンプレートIDを取得
    list_response = await client.get("/api/v1/analysis/templates?skip=0&limit=1")
    assert list_response.status_code == 200
    templates = list_response.json()
    assert len(templates) > 0
    template_id = templates[0]["id"]

    # Act
    response = await client.get(f"/api/v1/analysis/templates/{template_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert "policy" in data
    assert "issue" in data
    assert "description" in data
    assert "agent_prompt" in data
    assert "initial_msg" in data
    assert "initial_axis" in data
    assert "charts" in data  # 詳細取得はchartsを含む
    assert isinstance(data["charts"], list)


@pytest.mark.asyncio
async def test_get_template_detail_not_found(client: AsyncClient, seeded_templates):
    """存在しないテンプレートIDでの詳細取得（404エラー）。"""
    # Arrange
    fake_id = "00000000-0000-0000-0000-000000000000"

    # Act
    response = await client.get(f"/api/v1/analysis/templates/{fake_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_templates_by_policy_success(client: AsyncClient, seeded_templates):
    """施策別テンプレート一覧取得の成功ケース。"""
    # Arrange - まず一覧から1つの施策名を取得
    list_response = await client.get("/api/v1/analysis/templates?skip=0&limit=1")
    assert list_response.status_code == 200
    templates = list_response.json()
    assert len(templates) > 0
    policy = templates[0]["policy"]

    # Act
    response = await client.get(f"/api/v1/analysis/templates/policy/{policy}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # すべてのテンプレートが同じ施策であることを確認
    for template in data:
        assert template["policy"] == policy


@pytest.mark.asyncio
async def test_search_template_success(client: AsyncClient, seeded_templates):
    """施策・課題による検索の成功ケース。"""
    # Arrange - まず一覧から1つのテンプレートを取得
    list_response = await client.get("/api/v1/analysis/templates?skip=0&limit=1")
    assert list_response.status_code == 200
    templates = list_response.json()
    assert len(templates) > 0
    template = templates[0]
    policy = template["policy"]
    issue = template["issue"]

    # Act
    response = await client.get(f"/api/v1/analysis/templates/search/by-policy-issue?policy={policy}&issue={issue}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["policy"] == policy
    assert data["issue"] == issue
    assert "charts" in data  # 検索結果もchartsを含む
    assert isinstance(data["charts"], list)


@pytest.mark.asyncio
async def test_search_template_not_found(client: AsyncClient, seeded_templates):
    """存在しない施策・課題での検索（404エラー）。"""
    # Act
    response = await client.get("/api/v1/analysis/templates/search/by-policy-issue?policy=存在しない施策&issue=存在しない課題")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_template_with_charts(client: AsyncClient, seeded_templates):
    """チャートデータを持つテンプレートの詳細取得テスト。"""
    # Arrange - validation.ymlに定義されているテンプレートを探す
    # 「施策①：不採算製品の撤退」はチャートデータを持つ
    response = await client.get(
        "/api/v1/analysis/templates/search/by-policy-issue"
        "?policy=施策①：不採算製品の撤退"
        "&issue=不採算製品から撤退した場合の利益改善効果は​？"
    )

    # Act & Assert
    if response.status_code == 200:
        data = response.json()
        assert "charts" in data
        # このテンプレートはvalidation.ymlでチャートが定義されているはず
        if len(data["charts"]) > 0:
            chart = data["charts"][0]
            assert "id" in chart
            assert "chart_name" in chart
            assert "chart_data" in chart
            assert isinstance(chart["chart_data"], dict)
            assert "chart_order" in chart
            assert "created_at" in chart
            assert "updated_at" in chart


@pytest.mark.asyncio
async def test_template_initial_axis_structure(client: AsyncClient, seeded_templates):
    """initial_axisフィールドの構造テスト。"""
    # Arrange
    list_response = await client.get("/api/v1/analysis/templates?skip=0&limit=1")
    assert list_response.status_code == 200
    templates = list_response.json()
    assert len(templates) > 0

    # Act
    template = templates[0]

    # Assert
    assert "initial_axis" in template
    assert isinstance(template["initial_axis"], list)

    # initial_axisが空でない場合、構造を確認
    if len(template["initial_axis"]) > 0:
        axis = template["initial_axis"][0]
        assert isinstance(axis, dict)
        # validation.ymlの一般的なキーを確認
        assert "name" in axis or "option" in axis
