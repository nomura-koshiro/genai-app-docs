"""ドライバーツリー数式マスタモデル。

このモジュールは、ドライバー型ごとのKPI別計算式を管理するモデルを定義します。
"""

import uuid

from sqlalchemy import Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DriverTreeFormula(Base, TimestampMixin):
    """ドライバーツリー数式マスタ。

    ドライバー型ごとのKPI別計算式を管理します。

    Attributes:
        id: 主キー（UUID）
        driver_type_id: ドライバー型ID（1-24）
        driver_type: ドライバー型
        kpi: KPI種別（売上、原価、販管費、粗利、営業利益、EBITDA）
        formulas: 数式リスト（JSONB配列）
            例: ["売上 = 稼働部屋数 * 単価", "稼働部屋数 = キャパシティ * 稼働率 * 期間", ...]
        created_at: 作成日時（UTC）
        updated_at: 更新日時（UTC）

    Constraints:
        uq_driver_kpi: driver_type_id + kpi の一意制約

    Indexes:
        ix_formula_driver_kpi: driver_type_id + kpi による検索を最適化
    """

    __tablename__ = "driver_tree_formula"

    __table_args__ = (
        UniqueConstraint("driver_type_id", "kpi", name="uq_driver_kpi"),
        Index("ix_formula_driver_kpi", "driver_type_id", "kpi"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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

    kpi: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="KPI",
    )

    formulas: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="数式リスト",
    )

    def __repr__(self) -> str:
        """デバッグ用の文字列表現。"""
        return f"<DriverTreeFormula(id={self.id}, driver_type={self.driver_type}, kpi={self.kpi})>"
