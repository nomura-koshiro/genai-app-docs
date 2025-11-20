"""ファイルモデル。

アップロードされたファイルのメタデータを管理するモデル。
"""

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PrimaryKeyMixin


class SampleFile(Base, PrimaryKeyMixin):
    """サンプル: ファイルモデル。

    アップロードされたファイルのメタデータを管理します。
    実際のファイルはディスク上に保存され、このモデルはメタデータのみを保持します。

    Attributes:
        id: ファイルID（主キー）
        file_id: 外部から参照するファイル識別子（一意）
        user_id: ファイルの所有者（ゲストの場合はNone）
        filename: 元のファイル名
        filepath: サーバー上のファイルパス
        size: ファイルサイズ（バイト）
        content_type: ファイルのMIMEタイプ
        created_at: アップロード日時
    """

    __tablename__ = "sample_file"

    # PrimaryKeyMixinからid継承
    # created_atのみ（updated_atは不要なのでTimestampMixinは使用しない）

    file_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sample_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        """デバッグ用の文字列表現。"""
        return f"<SampleFile(id={self.id}, file_id={self.file_id}, filename={self.filename})>"
