"""アップロードされたファイル用のファイルモデル。"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class File(Base):
    """アップロードされたファイルを追跡するためのファイルデータベースモデル。"""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="files")

    def __repr__(self) -> str:
        """文字列表現。"""
        return f"<File(id={self.id}, filename={self.filename})>"
