"""DriverTreeモデル定義。

このモジュールは、ドライバーツリー（KPI分解ツリー）を表すモデルを定義します。

DriverTreeは、KPIを構成要素に分解する数式ツリーを表します。
各ツリーはルートノードへの参照を持ち、ノード自体が親子関係を管理します。

Example:
    >>> # ツリー作成
    >>> tree = DriverTree(name="粗利分析")
    >>>
    >>> # ルートノード作成
    >>> root = DriverTreeNode(tree_id=tree.id, label="粗利")
    >>> tree.root_node_id = root.id
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.node import DriverTreeNode


class DriverTree(Base, TimestampMixin):
    """ドライバーツリー。

    KPIを構成要素に分解する数式ツリーを表します。
    ツリー自体はルートノードへの参照のみを持ち、
    実際の木構造はノード間の親子関係で表現されます。

    Attributes:
        id: ツリーの一意識別子
        name: ツリー名（任意、例：「売上分析」「粗利分析」）
        root_node_id: ルートノードID
        root_node: ルートノードオブジェクト
        nodes: このツリーに属するすべてのノード

    Example:
        >>> # 粗利 = 売上 - 原価 のツリー
        >>> tree = DriverTree(name="粗利分析")
        >>> root = DriverTreeNode(tree_id=tree.id, label="粗利")
        >>> tree.root_node_id = root.id
        >>> child1 = DriverTreeNode(
        ...     tree_id=tree.id,
        ...     label="売上",
        ...     parent_id=root.id,
        ...     operator="-"
        ... )
        >>> child2 = DriverTreeNode(
        ...     tree_id=tree.id,
        ...     label="原価",
        ...     parent_id=root.id,
        ...     operator="-"
        ... )
    """

    __tablename__ = "driver_trees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ツリーの一意識別子",
    )
    name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="ツリー名（任意）",
    )
    root_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ルートノードID",
    )

    # リレーション: ルートノード
    root_node: Mapped["DriverTreeNode | None"] = relationship(
        "DriverTreeNode",
        foreign_keys=[root_node_id],
        post_update=True,
    )

    # リレーション: このツリーに属するすべてのノード
    nodes: Mapped[list["DriverTreeNode"]] = relationship(
        "DriverTreeNode",
        back_populates="tree",
        foreign_keys="DriverTreeNode.tree_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """文字列表現を返します。

        Returns:
            str: ツリーの文字列表現

        Example:
            >>> tree = DriverTree(name="粗利分析")
            >>> print(repr(tree))
            <DriverTree(name='粗利分析', nodes=5)>
        """
        return f"<DriverTree(name='{self.name}', nodes={len(self.nodes) if self.nodes else 0})>"
