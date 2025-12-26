"""ドライバーツリーカテゴリマスタモデル。

このモジュールは、業界分類・業界名とドライバー型の対応関係を管理するモデルを定義します。
"""

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DriverTreeCategory(Base, TimestampMixin):
    """ドライバーツリーカテゴリマスタ。

    業界分類・業界名とドライバー型の対応関係を管理します。

    Attributes:
        id: 主キー（自動採番）
        category_id: 業界分類ID（業務ID）
        category_name: 業界分類名
        industry_id: 業界名ID（業務ID）
        industry_name: 業界名
        driver_type_id: ドライバー型ID（1-24）
        driver_type: ドライバー型

    Indexes:
        ix_category_industry: 業界名による検索を最適化
        ix_category_driver: ドライバー型IDによるJOINを最適化
    """

    __tablename__ = "driver_tree_category"

    __table_args__ = (
        Index("ix_category_industry", "industry_name"),
        Index("ix_category_driver", "driver_type_id"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    category_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="業界分類ID",
    )

    category_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="業界分類",
    )

    industry_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="業界名ID",
    )

    industry_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="業界名",
    )

    driver_type_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ドライバー型ID",
    )

    driver_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ドライバー型",
    )

    def __repr__(self) -> str:
        """デバッグ用の文字列表現。"""
        return f"<DriverTreeCategory(id={self.id}, industry={self.industry_name}, driver_type={self.driver_type})>"
