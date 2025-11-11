"""AnalysisTemplateRepositoryのテスト。

このテストファイルは、分析テンプレートリポジトリの機能をテストします。
validation.ymlから自動的にシードされたテストデータを使用します。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analysis_template import AnalysisTemplateRepository


class TestAnalysisTemplateRepository:
    """AnalysisTemplateRepositoryのテストクラス。"""

    @pytest.mark.asyncio
    async def test_list_by_policy(self, db_session: AsyncSession, seeded_templates):
        """施策別のテンプレート一覧取得をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        templates = await repo.list_by_policy("施策①：不採算製品の撤退")

        # Assert
        assert len(templates) > 0
        for template in templates:
            assert template.policy == "施策①：不採算製品の撤退"
            assert template.issue is not None
            assert template.description is not None

    @pytest.mark.asyncio
    async def test_get_by_policy_issue(self, db_session: AsyncSession, seeded_templates):
        """施策・課題による特定テンプレート取得をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        template = await repo.get_by_policy_issue(
            policy="施策①：不採算製品の撤退",
            issue="不採算製品から撤退した場合の利益改善効果は​？",
        )

        # Assert
        assert template is not None
        assert template.policy == "施策①：不採算製品の撤退"
        assert template.issue == "不採算製品から撤退した場合の利益改善効果は​？"
        assert template.description != ""
        assert template.agent_prompt != ""
        assert template.initial_msg != ""
        assert len(template.initial_axis) > 0

    @pytest.mark.asyncio
    async def test_get_by_policy_issue_not_found(self, db_session: AsyncSession, seeded_templates):
        """存在しない施策・課題の組み合わせでNoneを返すことをテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        template = await repo.get_by_policy_issue(
            policy="存在しない施策",
            issue="存在しない課題",
        )

        # Assert
        assert template is None

    @pytest.mark.asyncio
    async def test_get_with_charts(self, db_session: AsyncSession, seeded_templates):
        """チャートデータを含むテンプレート詳細取得をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # まず、テンプレートを取得
        template = await repo.get_by_policy_issue(
            policy="施策①：不採算製品の撤退",
            issue="不採算製品から撤退した場合の利益改善効果は​？",
        )
        assert template is not None

        # Act
        template_with_charts = await repo.get_with_charts(template.id)

        # Assert
        assert template_with_charts is not None
        assert template_with_charts.id == template.id
        # チャートデータがロードされていることを確認
        assert hasattr(template_with_charts, "charts")
        # validation.ymlにチャートが定義されている場合、チャートが存在することを確認
        if len(template_with_charts.charts) > 0:
            chart = template_with_charts.charts[0]
            assert chart.chart_name is not None
            assert chart.chart_data is not None
            assert "data" in chart.chart_data or "layout" in chart.chart_data

    @pytest.mark.asyncio
    async def test_list_active(self, db_session: AsyncSession, seeded_templates):
        """アクティブなテンプレート一覧取得をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        templates = await repo.list_active(limit=100)

        # Assert
        assert len(templates) > 0
        # すべてのテンプレートがアクティブであることを確認
        for template in templates:
            assert template.is_active is True
            assert template.policy is not None
            assert template.issue is not None

    @pytest.mark.asyncio
    async def test_list_all_with_charts(self, db_session: AsyncSession, seeded_templates):
        """チャートデータを含むテンプレート一覧取得をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        templates = await repo.list_all_with_charts(limit=10)

        # Assert
        assert len(templates) > 0
        # 各テンプレートにchartsリレーションがロードされていることを確認
        for template in templates:
            assert hasattr(template, "charts")
            # chartsが空の場合もあり得る（validation.ymlでチャートが定義されていない場合）

    @pytest.mark.asyncio
    async def test_get_multi_with_pagination(self, db_session: AsyncSession, seeded_templates):
        """ページネーション付きテンプレート一覧取得をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        page1 = await repo.get_multi(skip=0, limit=2)
        page2 = await repo.get_multi(skip=2, limit=2)

        # Assert
        assert len(page1) > 0
        assert len(page2) >= 0

        # 異なるページでは異なるテンプレートが返されることを確認
        if len(page2) > 0:
            page1_ids = {t.id for t in page1}
            page2_ids = {t.id for t in page2}
            assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_count(self, db_session: AsyncSession, seeded_templates):
        """テンプレート数カウントをテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        count = await repo.count()

        # Assert
        assert count == seeded_templates["templates_created"]
        assert count > 0

    @pytest.mark.asyncio
    async def test_template_fields_structure(self, db_session: AsyncSession, seeded_templates):
        """テンプレートフィールドの構造をテストします。"""
        # Arrange
        repo = AnalysisTemplateRepository(db_session)

        # Act
        templates = await repo.list_active(limit=1)

        # Assert
        assert len(templates) > 0
        template = templates[0]

        # 必須フィールドの存在確認
        assert template.id is not None
        assert template.policy != ""
        assert template.issue != ""
        assert template.description != ""
        assert template.agent_prompt != ""
        assert template.initial_msg != ""
        assert isinstance(template.initial_axis, list)
        assert template.is_active is not None
        assert template.display_order is not None
        assert template.created_at is not None
        assert template.updated_at is not None

        # initial_axisの構造確認
        if len(template.initial_axis) > 0:
            axis = template.initial_axis[0]
            assert isinstance(axis, dict)
            # validation.ymlの一般的なキーを確認
            assert "name" in axis or "option" in axis
