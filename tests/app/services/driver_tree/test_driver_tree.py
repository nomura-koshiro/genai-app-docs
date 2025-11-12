"""Driver Treeサービスのテスト。

ビジネスロジックと検証のテストに焦点を当てます。
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import DriverTreeCategory
from app.repositories import DriverTreeRepository
from app.services import DriverTreeService


@pytest.mark.asyncio
async def test_create_node_success(db_session: AsyncSession):
    """ノード作成の成功ケース。"""
    # Arrange
    service = DriverTreeService(db_session)
    tree_repo = DriverTreeRepository(db_session)

    # ツリーを先に作成
    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # Act
    node = await service.create_node(tree_id=tree.id, label="売上", x=1, y=0)
    await db_session.commit()

    # Assert
    assert node.id is not None
    assert node.tree_id == tree.id
    assert node.label == "売上"
    assert node.x == 1
    assert node.y == 0


@pytest.mark.asyncio
async def test_create_node_without_coordinates(db_session: AsyncSession):
    """座標なしでのノード作成。"""
    # Arrange
    service = DriverTreeService(db_session)
    tree_repo = DriverTreeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # Act
    node = await service.create_node(tree_id=tree.id, label="粗利")
    await db_session.commit()

    # Assert
    assert node.id is not None
    assert node.tree_id == tree.id
    assert node.label == "粗利"
    assert node.x is None
    assert node.y is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "label,expected_error",
    [
        ("", "ラベルは1～100文字で指定してください"),
        ("a" * 101, "ラベルは1～100文字で指定してください"),
    ],
)
async def test_create_node_validation_error(db_session: AsyncSession, label, expected_error):
    """ノード作成時のラベル検証エラーテスト（パラメータ化）。"""
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    service = DriverTreeService(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        await service.create_node(tree_id=tree.id, label=label)

    assert expected_error in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_get_node_success(db_session: AsyncSession):
    """ノード取得の成功ケース。"""
    # Arrange
    service = DriverTreeService(db_session)
    tree_repo = DriverTreeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    created_node = await service.create_node(tree_id=tree.id, label="原価")
    await db_session.commit()

    # Act
    result = await service.get_node(created_node.id)

    # Assert
    assert result.id == created_node.id
    assert result.label == "原価"


@pytest.mark.asyncio
async def test_get_node_not_found(db_session: AsyncSession):
    """存在しないノードの取得エラー。"""
    # Arrange
    service = DriverTreeService(db_session)
    nonexistent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_node(nonexistent_id)

    assert "ノードが見つかりません" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_update_node_success(db_session: AsyncSession):
    """ノード更新の成功ケース。"""
    # Arrange
    service = DriverTreeService(db_session)
    tree_repo = DriverTreeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    node = await service.create_node(tree_id=tree.id, label="売上", x=0, y=0)
    await db_session.commit()

    # Act
    updated_node = await service.update_node(
        node_id=node.id,
        label="売上高",
        x=1,
        y=1,
    )
    await db_session.commit()

    # Assert
    assert updated_node.id == node.id
    assert updated_node.label == "売上高"
    assert updated_node.x == 1
    assert updated_node.y == 1


@pytest.mark.asyncio
async def test_update_node_partial_update(db_session: AsyncSession):
    """ノードの部分更新。"""
    # Arrange
    service = DriverTreeService(db_session)
    tree_repo = DriverTreeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    node = await service.create_node(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # Act - ラベルのみ更新
    updated_node = await service.update_node(
        node_id=node.id,
        label="営業粗利",
    )
    await db_session.commit()

    # Assert
    assert updated_node.label == "営業粗利"
    assert updated_node.x == 0  # 変更されていない
    assert updated_node.y == 0  # 変更されていない


@pytest.mark.asyncio
async def test_create_tree_from_formulas_simple(db_session: AsyncSession):
    """単純な数式からのツリー作成。

    重要: create_tree_from_formulas は単一のツリーを返すようになった。
    """
    # Arrange
    service = DriverTreeService(db_session)
    formulas = ["粗利 = 売上 - 原価"]

    # Act
    tree = await service.create_tree_from_formulas(formulas)
    await db_session.commit()

    # Assert
    assert tree is not None
    assert tree.id is not None
    assert tree.root_node_id is not None

    # ツリー構造を取得して確認
    tree_with_structure = await service.get_tree(tree.id)
    assert tree_with_structure.root_node is not None
    assert tree_with_structure.root_node.label == "粗利"


@pytest.mark.asyncio
async def test_create_tree_from_formulas_multiple(db_session: AsyncSession):
    """複数の数式からのツリー作成。

    重要: 複数の数式でも単一のツリーが返される（ルートは1つ）。
    """
    # Arrange
    service = DriverTreeService(db_session)
    formulas = [
        "粗利 = 売上 - 原価",
        "売上 = 数量 * 単価",
    ]

    # Act
    tree = await service.create_tree_from_formulas(formulas)
    await db_session.commit()

    # Assert
    assert tree is not None
    assert tree.root_node_id is not None

    # ツリー構造を確認
    tree_response = await service.get_tree_response(tree.id)
    assert tree_response.root_node is not None
    assert tree_response.root_node.label == "粗利"

    # 子ノードが存在することを確認
    assert tree_response.root_node.children is not None
    assert len(tree_response.root_node.children) == 2

    child_labels = {child.label for child in tree_response.root_node.children}
    assert "売上" in child_labels
    assert "原価" in child_labels


@pytest.mark.asyncio
async def test_create_tree_from_formulas_with_name(db_session: AsyncSession):
    """名前付きでツリーを作成。"""
    # Arrange
    service = DriverTreeService(db_session)
    formulas = ["粗利 = 売上 - 原価"]

    # Act
    tree = await service.create_tree_from_formulas(formulas, tree_name="粗利分析")
    await db_session.commit()

    # Assert
    assert tree.name == "粗利分析"
    assert tree.root_node_id is not None


@pytest.mark.asyncio
async def test_create_tree_from_formulas_with_coordinates(db_session: AsyncSession):
    """座標計算を含むツリー作成。"""
    # Arrange
    service = DriverTreeService(db_session)
    formulas = [
        "粗利 = 売上 - 原価",
        "売上 = 数量 * 単価",
    ]

    # Act
    tree = await service.create_tree_from_formulas(formulas)
    await db_session.commit()

    # Assert
    tree_response = await service.get_tree_response(tree.id)
    assert tree_response.root_node is not None

    # ルートノードの座標が設定されていることを確認
    assert tree_response.root_node.x is not None
    assert tree_response.root_node.y is not None

    # 子ノードの座標も設定されている
    for child in tree_response.root_node.children:
        assert child.x is not None
        assert child.y is not None


@pytest.mark.asyncio
async def test_create_tree_from_formulas_empty_formulas(db_session: AsyncSession):
    """空の数式リストでのエラー。"""
    # Arrange
    service = DriverTreeService(db_session)
    formulas = []

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        await service.create_tree_from_formulas(formulas)

    assert "数式が指定されていません" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_create_tree_from_formulas_multiple_roots(db_session: AsyncSession):
    """複数のルートノードがある場合のエラー。"""
    # Arrange
    service = DriverTreeService(db_session)
    # 2つの独立したツリー（ルートが2つ）
    formulas = [
        "粗利 = 売上 - 原価",
        "営業利益 = EBITDA - 減価償却",
    ]

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        await service.create_tree_from_formulas(formulas)

    assert "ルートノードが複数あります" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_get_tree_not_found(db_session: AsyncSession):
    """存在しないツリーの取得エラー。"""
    # Arrange
    service = DriverTreeService(db_session)
    nonexistent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_tree(nonexistent_id)

    assert "ツリーが見つかりません" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_get_tree_response_success(db_session: AsyncSession):
    """ツリーレスポンス取得の成功ケース。"""
    # Arrange
    service = DriverTreeService(db_session)
    formulas = ["粗利 = 売上 - 原価"]

    created_tree = await service.create_tree_from_formulas(formulas, tree_name="テスト")
    await db_session.commit()

    # Act
    result = await service.get_tree_response(created_tree.id)

    # Assert
    assert result.id == created_tree.id
    assert result.name == "テスト"
    assert result.root_node is not None
    assert result.root_node.label == "粗利"
    assert result.root_node.children is not None


@pytest.mark.asyncio
async def test_get_categories_success(db_session: AsyncSession):
    """カテゴリー一覧取得の成功ケース。"""
    # Arrange
    service = DriverTreeService(db_session)

    # カテゴリーを作成
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
        tree_type="生産_在庫管理型",
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

    # Act
    result = await service.get_categories()

    # Assert
    assert "製造業" in result
    assert "サービス業" in result
    assert "自動車製造" in result["製造業"]
    assert "電子機器製造" in result["製造業"]
    assert "ホテル業" in result["サービス業"]

    # ツリータイプの確認
    assert "生産_製造数量×出荷率型" in result["製造業"]["自動車製造"]
    assert "生産_在庫管理型" in result["製造業"]["電子機器製造"]
    assert "サービス_稼働率型" in result["サービス業"]["ホテル業"]


@pytest.mark.asyncio
async def test_get_formulas_success(db_session: AsyncSession):
    """数式取得の成功ケース。"""
    # Arrange
    service = DriverTreeService(db_session)

    # カテゴリーを作成
    category = DriverTreeCategory(
        industry_class="製造業",
        industry="自動車製造",
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
        formulas=["粗利 = 売上 - 原価", "売上 = 数量 * 単価"],
        metadata={},
    )
    db_session.add(category)
    await db_session.commit()

    # Act
    result = await service.get_formulas(
        tree_type="生産_製造数量×出荷率型",
        kpi="粗利",
    )

    # Assert
    assert len(result) == 2
    assert "粗利 = 売上 - 原価" in result
    assert "売上 = 数量 * 単価" in result


@pytest.mark.asyncio
async def test_get_formulas_not_found(db_session: AsyncSession):
    """存在しないツリータイプ/KPIの数式取得エラー。"""
    # Arrange
    service = DriverTreeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_formulas(
            tree_type="存在しないツリータイプ",
            kpi="粗利",
        )

    assert "数式が見つかりません" in str(exc_info.value.message)
