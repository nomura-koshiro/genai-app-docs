"""分析検証マスタモデル。

このモジュールは、分析検証（validation）のマスタデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_issue_master import AnalysisIssueMaster


class AnalysisValidationMaster(Base, TimestampMixin):
    """分析検証マスタ。

    分析における検証項目のマスタデータを管理します。

    Attributes:
        id: 主キー（UUID）
        name: 検証名
        validation_order: 表示順序
    """

    __tablename__ = "analysis_validation_master"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="検証名",
    )

    validation_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="表示順序",
    )

    # リレーションシップ
    issues: Mapped[list["AnalysisIssueMaster"]] = relationship(
        "AnalysisIssueMaster",
        back_populates="validation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AnalysisValidationMaster(id={self.id}, name={self.name})>"
