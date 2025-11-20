"""分析セッションモデル。

このモジュールは、AIエージェントによるデータ分析セッションを管理するモデルを定義します。

主な機能:
    - 分析セッションの基本情報管理
    - プロジェクトとの関連付け
    - validation設定の保存（JSONB）
    - チャット履歴の保存（JSONB）
    - スナップショット履歴の管理

テーブル設計:
    - テーブル名: analysis_sessions
    - プライマリキー: id (UUID)
    - 外部キー: project_id (projects), created_by (users)

使用例:
    >>> from app.models.analysis import AnalysisSession
    >>> session = AnalysisSession(
    ...     project_id=project_id,
    ...     created_by=user_id,
    ...     validation_config={"policy": "市場拡大", "issue": "新規参入"}
    ... )
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_file import AnalysisFile
    from app.models.analysis.analysis_step import AnalysisStep
    from app.models.project.project import Project
    from app.models.user_account.user_account import UserAccount


class AnalysisSession(Base, TimestampMixin):
    """分析セッションモデル。

    AIエージェントによるデータ分析セッションの情報を管理します。
    各セッションはプロジェクトに紐づき、複数のステップとファイルを持ちます。

    Attributes:
        id (UUID): プライマリキー（UUID）
        project_id (UUID): プロジェクトID（外部キー）
        created_by (UUID): セッション作成者のユーザーID（外部キー）
        session_name (str | None): セッション名
        validation_config (dict): 分析設定（validation.ymlの内容）
            - policy (str): 施策名
            - issue (str): 課題名
            - その他validation設定
        chat_history (list[dict]): チャット履歴（論理型: list[AnalysisChatMessage]）
            各メッセージは AnalysisChatMessage スキーマに対応
            - role (str): "user" | "assistant"
            - content (str): メッセージ内容
            - timestamp (str): タイムスタンプ
        snapshot_history (list[list[dict]] | None): スナップショット履歴
            - snapshot_id (int): スナップショットID
            - timestamp (str): 作成日時
            - step_count (int): ステップ数
        original_file_id (UUID | None): 選択中のファイルID
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    Relationships:
        project (Project): 所属プロジェクト
        creator (UserAccount): セッション作成者
        steps (list[AnalysisStep]): 分析ステップリスト
        files (list[AnalysisFile]): アップロードファイルリスト

    インデックス:
        - idx_analysis_sessions_project: project_id
        - idx_analysis_sessions_created_by: created_by
    """

    __tablename__ = "analysis_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="セッションID（主キー）",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="プロジェクトID（外部キー）",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="作成者ユーザーID（外部キー）",
    )

    session_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="セッション名",
    )

    validation_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="validation.ymlからの検証設定",
    )

    chat_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="AIエージェントとのチャット履歴（AnalysisChatMessageのリストを辞書形式で保存）",
    )

    snapshot_history: Mapped[list[list[dict[str, Any]]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="スナップショット履歴（各スナップショットはステップ状態のリスト）",
    )

    original_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="現在選択中のファイルID",
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="アクティブフラグ",
    )

    # リレーションシップ
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="analysis_sessions",
    )

    creator: Mapped["UserAccount"] = relationship(
        "UserAccount",
        back_populates="analysis_sessions",
    )

    steps: Mapped[list["AnalysisStep"]] = relationship(
        "AnalysisStep",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AnalysisStep.step_order",
    )

    files: Mapped[list["AnalysisFile"]] = relationship(
        "AnalysisFile",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    # インデックス
    __table_args__ = (
        Index("idx_analysis_sessions_project", "project_id"),
        Index("idx_analysis_sessions_created_by", "created_by"),
    )

    def __repr__(self) -> str:
        """分析セッションオブジェクトの文字列表現。

        Returns:
            str: "<AnalysisSession(id=..., project_id=...)>" 形式

        Example:
            >>> session = AnalysisSession(id=uuid.uuid4(), project_id=uuid.uuid4())
            >>> print(repr(session))
            '<AnalysisSession(id=..., project_id=...)>'
        """
        return f"<AnalysisSession(id={self.id}, project_id={self.project_id})>"
