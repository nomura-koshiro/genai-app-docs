"""分析ファイルモデル。

このモジュールは、分析セッションにアップロードされたファイルを管理するモデルを定義します。

主な機能:
    - アップロードファイルの基本情報管理
    - ストレージパスの管理
    - ファイルメタデータ（サイズ、タイプ）の保存
    - テーブル軸候補の保存

テーブル設計:
    - テーブル名: analysis_files
    - プライマリキー: id (UUID)
    - 外部キー: session_id (analysis_sessions), uploaded_by (users)

使用例:
    >>> from app.models.analysis import AnalysisFile
    >>> file = AnalysisFile(
    ...     session_id=session_id,
    ...     uploaded_by=user_id,
    ...     file_name="sales_data.xlsx",
    ...     table_name="売上データ",
    ...     storage_path="analysis/{session_id}/sales_data.csv"
    ... )
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.session import AnalysisSession
    from app.models.user.user import UserAccount


class AnalysisFile(Base, TimestampMixin):
    """分析ファイルモデル。

    分析セッションにアップロードされたExcel/CSVファイルの情報を管理します。
    ファイルはBlob Storageに保存され、メタデータはDBに記録されます。

    Attributes:
        id (UUID): プライマリキー（UUID）
        session_id (UUID): セッションID（外部キー）
        uploaded_by (UUID): アップロード者のユーザーID（外部キー）
        file_name (str): 元のファイル名（例: "sales_data.xlsx"）
        table_name (str): テーブル名（ユーザー定義）
        storage_path (str): ストレージパス（Blob Storage上のパス）
        file_size (int): ファイルサイズ（バイト）
        content_type (str | None): MIMEタイプ
        table_axis (list[str] | None): 軸候補のリスト（例: ["地域", "商品"]）
        file_metadata (dict | None): その他のメタデータ
            - sheet_name (str): Excelシート名
            - row_count (int): 行数
            - column_count (int): 列数
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    Relationships:
        session (AnalysisSession): 所属セッション
        uploader (UserAccount): アップロード者

    インデックス:
        - idx_analysis_files_session: session_id
        - idx_analysis_files_uploaded_by: uploaded_by
    """

    __tablename__ = "analysis_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="File ID (Primary Key)",
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Session ID (Foreign Key)",
    )

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Uploader user ID (Foreign Key)",
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original file name",
    )

    table_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Table name (user-defined)",
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Storage path in Blob Storage",
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="File size in bytes",
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type (e.g., application/vnd.ms-excel)",
    )

    table_axis: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Table axis candidates (e.g., ['地域', '商品'])",
    )

    file_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="File metadata (AnalysisFileMetadata as dict)",
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Active flag",
    )

    # リレーションシップ
    session: Mapped["AnalysisSession"] = relationship(
        "AnalysisSession",
        back_populates="files",
    )

    uploader: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[uploaded_by],
    )

    # インデックス
    __table_args__ = (
        Index("idx_analysis_files_session", "session_id"),
        Index("idx_analysis_files_uploaded_by", "uploaded_by"),
    )

    def __repr__(self) -> str:
        """分析ファイルオブジェクトの文字列表現。

        Returns:
            str: "<AnalysisFile(id=..., file_name=...)>" 形式

        Example:
            >>> file = AnalysisFile(id=uuid.uuid4(), file_name="sales_data.xlsx")
            >>> print(repr(file))
            '<AnalysisFile(id=..., file_name=sales_data.xlsx)>'
        """
        return f"<AnalysisFile(id={self.id}, file_name={self.file_name})>"
