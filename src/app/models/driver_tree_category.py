"""DriverTreeCategoryモデル定義。

このモジュールは、ドライバーツリーのカテゴリー（業種別テンプレート）を表すモデルを定義します。

DriverTreeCategoryは、業種ごとに事前定義されたドライバーツリーのテンプレートを管理します。

Example:
    >>> category = DriverTreeCategory(
    ...     industry_class="製造業",
    ...     industry="自動車製造",
    ...     tree_type="生産_製造数量×出荷率型",
    ...     kpi="粗利",
    ...     formulas=["粗利 = 売上 - 原価", "売上 = 数量 * 単価"]
    ... )
"""

import uuid
from typing import Any

from sqlalchemy import ARRAY, UUID, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DriverTreeCategory(Base, TimestampMixin):
    """ドライバーツリーカテゴリー。

    業種ごとに事前定義されたドライバーツリーのテンプレートを管理します。

    Attributes:
        id: カテゴリーの一意識別子
        industry_class: 業種大分類（例: 製造業、サービス業）
        industry: 業種（例: 自動車製造、ホテル業）
        tree_type: ツリータイプ（例: 生産_製造数量×出荷率型）
        kpi: KPI名（例: 粗利、営業利益）
        formulas: 数式のリスト
        category_metadata: その他のメタデータ（JSONB）

    Example:
        >>> category = DriverTreeCategory(
        ...     industry_class="製造業",
        ...     industry="自動車製造",
        ...     tree_type="生産_製造数量×出荷率型",
        ...     kpi="粗利",
        ...     formulas=["粗利 = 売上 - 原価", "売上 = 稼働部屋数 * 単価"]
        ... )
        >>> print(category.industry)
        自動車製造
    """

    __tablename__ = "driver_tree_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="カテゴリーの一意識別子",
    )
    industry_class: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="業種大分類")
    industry: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="業種")
    tree_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="ツリータイプ")
    kpi: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="KPI名")
    formulas: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, comment="数式のリスト")
    category_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, comment="その他のメタデータ")

    def __repr__(self) -> str:
        """文字列表現を返します。

        Returns:
            str: カテゴリーの文字列表現

        Example:
            >>> category = DriverTreeCategory(
            ...     industry="ホテル業",
            ...     tree_type="生産_製造数量×出荷率型",
            ...     kpi="粗利"
            ... )
            >>> print(repr(category))
            <DriverTreeCategory(industry='ホテル業', tree_type='生産_製造数量×出荷率型', kpi='粗利')>
        """
        return f"<DriverTreeCategory(industry='{self.industry}', tree_type='{self.tree_type}', kpi='{self.kpi}')>"
