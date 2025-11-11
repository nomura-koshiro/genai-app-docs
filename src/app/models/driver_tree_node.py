"""DriverTreeNodeモデル定義。

このモジュールは、ドライバーツリーのノード（KPI構成要素）を表すモデルを定義します。

DriverTreeNodeは、KPIを構成要素に分解する真の木構造のノードを表します。
各ノードは親ノードへの参照を持ち、階層構造を形成します。

Example:
    >>> # ルートノード: 粗利
    >>> root = DriverTreeNode(tree_id=tree_id, label="粗利")
    >>>
    >>> # 子ノード: 売上
    >>> sales = DriverTreeNode(
    ...     tree_id=tree_id,
    ...     label="売上",
    ...     parent_id=root.id,
    ...     operator="-"
    ... )
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree import DriverTree


class DriverTreeNode(Base, TimestampMixin):
    """ドライバーツリーのノード。

    KPIを構成要素に分解する木構造のノードを表します。
    各ノードは親ノードへの参照を持ち、真の階層構造を形成します。

    Attributes:
        id: ノードの一意識別子
        tree_id: 所属するツリーのID
        label: ノードのラベル（KPI名や計算要素名）
        parent_id: 親ノードID（Noneの場合はルートノード）
        operator: 親ノードとの演算子（+, -, *, /, %など）
        x: X座標（ツリー表示用）
        y: Y座標（ツリー表示用）
        tree: 所属するツリー
        parent: 親ノード
        children: 子ノードのリスト

    Example:
        >>> # 粗利 = 売上 - 原価 の木構造
        >>> root = DriverTreeNode(tree_id=tree_id, label="粗利")
        >>> child1 = DriverTreeNode(
        ...     tree_id=tree_id,
        ...     label="売上",
        ...     parent_id=root.id,
        ...     operator="-"
        ... )
        >>> child2 = DriverTreeNode(
        ...     tree_id=tree_id,
        ...     label="原価",
        ...     parent_id=root.id,
        ...     operator="-"
        ... )
    """

    __tablename__ = "driver_tree_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ノードの一意識別子",
    )
    tree_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_trees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属するツリーのID",
    )
    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="ノードのラベル",
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_nodes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="親ノードID（Noneの場合はルートノード）",
    )
    operator: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="親ノードとの演算子（+, -, *, /, %など）",
    )
    x: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="X座標（ツリー表示用）",
    )
    y: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Y座標（ツリー表示用）",
    )

    # リレーション: 所属するツリー
    tree: Mapped["DriverTree"] = relationship(
        "DriverTree",
        back_populates="nodes",
        foreign_keys=[tree_id],
    )

    # リレーション: 親ノード（自己参照）
    parent: Mapped["DriverTreeNode | None"] = relationship(
        "DriverTreeNode",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )

    # リレーション: 子ノード（自己参照）
    children: Mapped[list["DriverTreeNode"]] = relationship(
        "DriverTreeNode",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """文字列表現を返します。

        Returns:
            str: ノードの文字列表現

        Example:
            >>> node = DriverTreeNode(label="粗利", operator="-")
            >>> print(repr(node))
            <DriverTreeNode(label='粗利', operator='-', parent=None)>
        """
        parent_label = self.parent.label if self.parent else None
        return (
            f"<DriverTreeNode(label='{self.label}', "
            f"operator='{self.operator}', parent={parent_label})>"
        )
