"""DriverTreeNodeリポジトリのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
カスタムメソッドのみをテストします。

基本的なCRUD操作はサービス層のテストでカバーされます。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.driver_tree import (
    DriverTreeNodeRepository,
    DriverTreeRepository,
)


@pytest.mark.asyncio
async def test_create_with_tree_id(db_session: AsyncSession):
    """tree_idを指定したノード作成のテスト。

    カスタムメソッド: create() による簡易作成。
    サービス層から頻繁に呼ばれる。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    # ツリーを作成
    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # Act
    node = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # Assert
    assert node is not None
    assert node.id is not None
    assert node.tree_id == tree.id
    assert node.label == "粗利"
    assert node.x == 0
    assert node.y == 0
    assert node.parent_id is None
    assert node.operator is None


@pytest.mark.asyncio
async def test_create_with_parent_and_operator(db_session: AsyncSession):
    """親ノードと演算子を指定したノード作成のテスト。

    ビジネスロジック: 子ノードは親ノードIDと演算子を持つ。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    # ツリーを作成
    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # 親ノードを作成
    parent = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # Act - 子ノードを作成
    child = await node_repo.create(
        tree_id=tree.id,
        label="売上",
        parent_id=parent.id,
        operator="-",
        x=1,
        y=0,
    )
    await db_session.commit()

    # Assert
    assert child is not None
    assert child.tree_id == tree.id
    assert child.label == "売上"
    assert child.parent_id == parent.id
    assert child.operator == "-"
    assert child.x == 1
    assert child.y == 0


@pytest.mark.asyncio
async def test_create_without_coordinates(db_session: AsyncSession):
    """座標なしでのノード作成テスト。

    ビジネスロジック: 座標は後で計算される場合がある。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # Act
    node = await node_repo.create(tree_id=tree.id, label="営業利益")
    await db_session.commit()

    # Assert
    assert node is not None
    assert node.tree_id == tree.id
    assert node.label == "営業利益"
    assert node.x is None
    assert node.y is None


@pytest.mark.asyncio
async def test_find_by_tree_id(db_session: AsyncSession):
    """ツリーIDによる全ノード検索のテスト。

    カスタムクエリ: 特定ツリーに属する全ノードを取得。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # 複数のノードを作成
    await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await node_repo.create(tree_id=tree.id, label="売上", x=1, y=0)
    await node_repo.create(tree_id=tree.id, label="原価", x=1, y=1)
    await db_session.commit()

    # Act
    result = await node_repo.find_by_tree_id(tree.id)

    # Assert
    assert len(result) == 3
    labels = {node.label for node in result}
    assert "粗利" in labels
    assert "売上" in labels
    assert "原価" in labels


@pytest.mark.asyncio
async def test_find_root_by_tree_id(db_session: AsyncSession):
    """ツリーのルートノード検索のテスト。

    カスタムクエリ: parent_idがNullのノードを検索。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # ルートノードと子ノードを作成
    root = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    await node_repo.create(
        tree_id=tree.id, label="売上", parent_id=root.id, operator="-", x=1, y=0
    )
    await db_session.commit()

    # Act
    result = await node_repo.find_root_by_tree_id(tree.id)

    # Assert
    assert result is not None
    assert result.id == root.id
    assert result.label == "粗利"
    assert result.parent_id is None


@pytest.mark.asyncio
async def test_find_children(db_session: AsyncSession):
    """親ノードの子ノード検索のテスト。

    カスタムクエリ: 指定された親IDを持つノードを検索。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # 親ノードを作成
    parent = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # 複数の子ノードを作成
    await node_repo.create(
        tree_id=tree.id, label="売上", parent_id=parent.id, operator="-", x=1, y=0
    )
    await node_repo.create(
        tree_id=tree.id, label="原価", parent_id=parent.id, operator="-", x=1, y=1
    )
    await db_session.commit()

    # Act
    result = await node_repo.find_children(parent.id)

    # Assert
    assert len(result) == 2
    labels = {node.label for node in result}
    assert "売上" in labels
    assert "原価" in labels
    for child in result:
        assert child.parent_id == parent.id
        assert child.operator == "-"


@pytest.mark.asyncio
async def test_find_by_label_and_tree(db_session: AsyncSession):
    """ツリー内でラベルによるノード検索のテスト。

    カスタムクエリ: 同じラベルでも異なるツリーで区別される。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    tree1 = await tree_repo.create(name="ツリー1")
    tree2 = await tree_repo.create(name="ツリー2")
    await db_session.commit()

    # 異なるツリーに同じラベルのノードを作成
    node1 = await node_repo.create(tree_id=tree1.id, label="粗利", x=0, y=0)
    node2 = await node_repo.create(tree_id=tree2.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # Act
    result1 = await node_repo.find_by_label_and_tree(tree1.id, "粗利")
    result2 = await node_repo.find_by_label_and_tree(tree2.id, "粗利")

    # Assert
    assert result1 is not None
    assert result2 is not None
    assert result1.id == node1.id
    assert result2.id == node2.id
    assert result1.id != result2.id
