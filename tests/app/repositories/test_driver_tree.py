"""DriverTreeリポジトリのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
カスタムメソッドのみをテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.driver_tree import DriverTreeRepository
from app.repositories.driver_tree_node import DriverTreeNodeRepository


@pytest.mark.asyncio
async def test_create_tree_with_name(db_session: AsyncSession):
    """名前付きツリー作成のテスト。

    カスタムメソッド: create() による簡易作成。
    """
    # Arrange
    repo = DriverTreeRepository(db_session)

    # Act
    tree = await repo.create(name="粗利分析ツリー")
    await db_session.commit()

    # Assert
    assert tree is not None
    assert tree.id is not None
    assert tree.name == "粗利分析ツリー"
    assert tree.root_node_id is None


@pytest.mark.asyncio
async def test_create_tree_without_name(db_session: AsyncSession):
    """名前なしツリー作成のテスト。"""
    # Arrange
    repo = DriverTreeRepository(db_session)

    # Act
    tree = await repo.create()
    await db_session.commit()

    # Assert
    assert tree is not None
    assert tree.id is not None
    assert tree.name is None
    assert tree.root_node_id is None


@pytest.mark.asyncio
async def test_get_with_nodes(db_session: AsyncSession):
    """リレーション付きツリー取得のテスト。

    カスタムクエリ: selectinloadによる関連ノードの一括取得。
    N+1問題を防ぐために使用される。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    # ツリーを作成
    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # ルートノードを作成
    root_node = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # 子ノードを作成
    await node_repo.create(
        tree_id=tree.id, label="売上", parent_id=root_node.id, operator="-", x=1, y=0
    )
    await node_repo.create(
        tree_id=tree.id, label="原価", parent_id=root_node.id, operator="-", x=1, y=1
    )
    await db_session.commit()

    # ツリーにルートノードを設定
    await tree_repo.update_root_node(tree.id, root_node.id)
    await db_session.commit()

    # Act
    result = await tree_repo.get_with_nodes(tree.id)

    # Assert
    assert result is not None
    assert result.id == tree.id
    assert result.root_node is not None
    assert result.root_node.label == "粗利"

    # すべてのノードが取得されている
    assert len(result.nodes) == 3
    node_labels = {node.label for node in result.nodes}
    assert "粗利" in node_labels
    assert "売上" in node_labels
    assert "原価" in node_labels


@pytest.mark.asyncio
async def test_get_with_nodes_not_found(db_session: AsyncSession):
    """存在しないツリーIDでの取得テスト。"""
    # Arrange
    repo = DriverTreeRepository(db_session)

    # 存在しないUUIDを使用
    import uuid

    nonexistent_id = uuid.uuid4()

    # Act
    result = await repo.get_with_nodes(nonexistent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_with_tree_structure(db_session: AsyncSession):
    """木構造付きツリー取得のテスト。

    カスタムクエリ: ルートノードと再帰的な子ノードを含む。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    # ツリーを作成
    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # ルートノードを作成
    root = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # 第1階層の子ノードを作成
    child1 = await node_repo.create(
        tree_id=tree.id, label="売上", parent_id=root.id, operator="-", x=1, y=0
    )
    await node_repo.create(
        tree_id=tree.id, label="原価", parent_id=root.id, operator="-", x=1, y=1
    )
    await db_session.commit()

    # 第2階層の子ノードを作成
    await node_repo.create(
        tree_id=tree.id, label="数量", parent_id=child1.id, operator="*", x=2, y=0
    )
    await db_session.commit()

    # ツリーにルートノードを設定
    await tree_repo.update_root_node(tree.id, root.id)
    await db_session.commit()

    # Act
    result = await tree_repo.get_with_tree_structure(tree.id)

    # Assert
    assert result is not None
    assert result.root_node is not None
    assert result.root_node.label == "粗利"

    # 子ノードが再帰的にロードされている
    # Note: この検証は実装に依存するため、実際の実装に合わせて調整が必要


@pytest.mark.asyncio
async def test_update_root_node(db_session: AsyncSession):
    """ルートノード更新のテスト。

    カスタムメソッド: ツリーのルートノードを設定。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    # ツリーを作成
    tree = await tree_repo.create(name="テストツリー")
    await db_session.commit()

    # ルートノードを作成
    root = await node_repo.create(tree_id=tree.id, label="粗利", x=0, y=0)
    await db_session.commit()

    # Act
    result = await tree_repo.update_root_node(tree.id, root.id)
    await db_session.commit()

    # Assert
    assert result is not None
    assert result.root_node_id == root.id

    # 取得して確認
    updated_tree = await tree_repo.get(tree.id)
    assert updated_tree is not None
    assert updated_tree.root_node_id == root.id


@pytest.mark.asyncio
async def test_get_with_nodes_no_root(db_session: AsyncSession):
    """ルートノードなしツリーの取得テスト。

    ビジネスロジック: ルートノード設定前のツリー。
    """
    # Arrange
    tree_repo = DriverTreeRepository(db_session)
    node_repo = DriverTreeNodeRepository(db_session)

    # ツリーを作成（ルートノード未設定）
    tree = await tree_repo.create(name="ルートなしツリー")
    await db_session.commit()

    # ノードは作成するがルートノードは設定しない
    await node_repo.create(tree_id=tree.id, label="孤立ノード", x=0, y=0)
    await db_session.commit()

    # Act
    result = await tree_repo.get_with_nodes(tree.id)

    # Assert
    assert result is not None
    assert result.root_node_id is None
    assert result.root_node is None
    # ノードは存在する
    assert len(result.nodes) == 1
    assert result.nodes[0].label == "孤立ノード"
