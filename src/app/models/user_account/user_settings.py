"""ユーザー設定モデル。

このモジュールは、ユーザー個人設定（テーマ、言語、通知、表示設定）を管理するモデルを定義します。

主な機能:
    - テーマ設定（light/dark/system）
    - 言語設定（ja/en）
    - 通知設定（メール、プロジェクト招待、セッション完了など）
    - 表示設定（ページあたり件数、デフォルトビューなど）

テーブル設計:
    - テーブル名: user_settings
    - プライマリキー: id (UUID)
    - 外部キー: user_id (user_account.id)
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import LanguageEnum, ProjectViewEnum, ThemeEnum


class UserSettings(Base, TimestampMixin):
    """ユーザー設定モデル。

    ユーザー個人設定を管理します。ユーザーアカウントと1対1の関係を持ちます。

    Attributes:
        id (UUID): プライマリキー（UUID）
        user_id (UUID): ユーザーID（外部キー）
        theme (str): テーマ設定（light/dark/system）
        language (str): 言語設定（ja/en）
        timezone (str): タイムゾーン設定
        email_enabled (bool): メール通知の有効化
        project_invite (bool): プロジェクト招待通知
        session_complete (bool): セッション完了通知
        tree_update (bool): ツリー更新通知
        system_announcement (bool): システムお知らせ通知
        items_per_page (int): ページあたり表示件数
        default_project_view (str): デフォルトプロジェクト表示形式
        show_welcome_message (bool): ウェルカムメッセージ表示
    """

    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="ユーザーID",
    )

    # テーマ・言語設定
    theme: Mapped[str] = mapped_column(
        String(20),
        default=ThemeEnum.LIGHT.value,
        nullable=False,
        comment="テーマ設定（light/dark/system）",
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default=LanguageEnum.JA.value,
        nullable=False,
        comment="言語設定（ja/en）",
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Tokyo",
        nullable=False,
        comment="タイムゾーン設定",
    )

    # 通知設定
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="メール通知の有効化",
    )

    project_invite: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="プロジェクト招待通知",
    )

    session_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="セッション完了通知",
    )

    tree_update: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="ツリー更新通知",
    )

    system_announcement: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="システムお知らせ通知",
    )

    # 表示設定
    items_per_page: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False,
        comment="ページあたり表示件数",
    )

    default_project_view: Mapped[str] = mapped_column(
        String(20),
        default=ProjectViewEnum.GRID.value,
        nullable=False,
        comment="デフォルトプロジェクト表示形式（grid/list）",
    )

    show_welcome_message: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="ウェルカムメッセージ表示",
    )

    # リレーションシップ
    user = relationship("UserAccount", backref="settings", uselist=False)

    def __repr__(self) -> str:
        """ユーザー設定オブジェクトの文字列表現。"""
        return f"<UserSettings(id={self.id}, user_id={self.user_id})>"
