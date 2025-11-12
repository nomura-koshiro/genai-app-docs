"""DriverTreeCategoryリポジトリのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
カスタムメソッドのみをテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DriverTreeCategory
from app.repositories.driver_tree import DriverTreeCategoryRepository


@pytest.mark.asyncio
async def test_find_by_criteria_all_params(db_session: AsyncSession):
    """すべてのパラメータを指定した検索のテスト。

    カスタムクエリ: 複数条件でのフィルタリング。
    特定のKPI数式を取得するために使用される。
    """
    # Arrange
    repo = DriverTreeCategoryRepository(db_session)

    # カテゴリーを作成
    category1 = DriverTreeCategory(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価", "売上 = 数量 * 単価"],
        metadata={},
    )
    category2 = DriverTreeCategory(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="営業利益",
        formulas=["営業利益 = 粗利 - 販管費"],
        metadata={},
    )
    category3 = DriverTreeCategory(
        industry_class="サービス業",
        industry="ホテル業",
        tree_type="サービス_稼働率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 変動費"],
        metadata={},
    )
    db_session.add(category1)
    db_session.add(category2)
    db_session.add(category3)
    await db_session.commit()

    # Act
    result = await repo.find_by_criteria(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
    )

    # Assert
    assert len(result) == 1
    assert result[0].kpi == "粗利"
    assert result[0].industry == "自動車製造"
    assert len(result[0].formulas) == 2


@pytest.mark.asyncio
async def test_find_by_criteria_partial_params(db_session: AsyncSession):
    """一部のパラメータのみ指定した検索のテスト。

    ビジネスロジック: 業種全体のKPIを取得する場合。
    """
    # Arrange
    repo = DriverTreeCategoryRepository(db_session)

    # 複数のカテゴリーを作成
    category1 = DriverTreeCategory(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価"],
        metadata={},
    )
    category2 = DriverTreeCategory(
        industry_class="製造業",
        industry="電子機器製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価"],
        metadata={},
    )
    category3 = DriverTreeCategory(
        industry_class="サービス業",
        industry="ホテル業",
        tree_type="サービス_稼働率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 変動費"],
        metadata={},
    )
    db_session.add(category1)
    db_session.add(category2)
    db_session.add(category3)
    await db_session.commit()

    # Act - 業種大分類のみで検索
    result = await repo.find_by_criteria(industry_class="製造業")

    # Assert
    assert len(result) == 2
    assert all(c.industry_class == "製造業" for c in result)


@pytest.mark.asyncio
async def test_find_by_criteria_tree_type_and_kpi(db_session: AsyncSession):
    """ツリータイプとKPIでの検索テスト。

    ビジネスロジック: 特定のツリータイプのKPI数式を取得。
    APIエンドポイント GET /formulas で使用される。
    """
    # Arrange
    repo = DriverTreeCategoryRepository(db_session)

    # カテゴリーを作成
    category1 = DriverTreeCategory(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価", "売上 = 数量 * 単価"],
        metadata={},
    )
    category2 = DriverTreeCategory(
        industry_class="製造業",
        industry="電子機器製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価", "売上 = 数量 * 単価"],
        metadata={},
    )
    db_session.add(category1)
    db_session.add(category2)
    await db_session.commit()

    # Act
    result = await repo.find_by_criteria(
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
    )

    # Assert
    assert len(result) == 2
    assert all(c.tree_type == "生産_製造数量×出荷率型" for c in result)
    assert all(c.kpi == "粗利" for c in result)


@pytest.mark.asyncio
async def test_find_by_criteria_no_match(db_session: AsyncSession):
    """該当するカテゴリーがない場合のテスト。"""
    # Arrange
    repo = DriverTreeCategoryRepository(db_session)

    # カテゴリーを作成
    category = DriverTreeCategory(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価"],
        metadata={},
    )
    db_session.add(category)
    await db_session.commit()

    # Act
    result = await repo.find_by_criteria(industry_class="存在しない業種")

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_find_by_criteria_no_params(db_session: AsyncSession):
    """パラメータなしでの検索テスト（全件取得）。

    ビジネスロジック: すべてのカテゴリーを取得する場合。
    """
    # Arrange
    repo = DriverTreeCategoryRepository(db_session)

    # 3つのカテゴリーを作成
    for i in range(3):
        category = DriverTreeCategory(
            industry_class=f"業種{i}",
            industry=f"産業{i}",
            tree_type=f"タイプ{i}",
            kpi="粗利",
            formulas=["粗利 = 売上 - 原価"],
            metadata={},
        )
        db_session.add(category)

    await db_session.commit()

    # Act
    result = await repo.find_by_criteria()

    # Assert
    assert len(result) == 3
