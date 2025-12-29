"""ユーザー操作履歴モデル。

このモジュールは、ユーザーの操作履歴を記録するためのモデルを提供します。

主な用途:
    - ユーザー問い合わせ対応（何をいつ行ったか確認）
    - エラー発生時のトラブルシューティング
    - システム監査ログ

記録される情報:
    - API呼び出し履歴（自動記録）
    - UI操作イベント（フロントエンドから送信）
    - エラー情報（発生時）
    - パフォーマンス情報（処理時間）
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserActivity(Base):
    """ユーザー操作履歴モデル。

    ユーザーの操作（API呼び出し、UI操作）を記録し、
    問い合わせ対応やトラブルシューティングに使用します。

    Attributes:
        id: 主キー（UUID）
        user_id: ユーザーID（外部キー）
        event_type: イベント種別（api_call / ui_action）
        action: 操作内容（create_project, button_click等）
        resource_type: リソース種別（project, session, tree等）
        resource_id: リソースID
        endpoint: APIエンドポイント（API呼び出し時）
        method: HTTPメソッド（GET, POST等）
        page_path: ページパス（UI操作時）
        status: 処理結果（success / error）
        status_code: HTTPステータスコード
        error_type: エラー種別（エラー時）
        error_message: エラーメッセージ（エラー時）
        duration_ms: 処理時間（ミリ秒）
        ip_address: クライアントIPアドレス
        user_agent: ユーザーエージェント
        metadata: 追加メタデータ（JSON）
        created_at: 記録日時

    インデックス:
        - user_id + created_at: ユーザー別時系列検索
        - created_at: 日時検索
        - action: 操作種別検索
        - status: ステータス検索（エラー抽出）
    """

    __tablename__ = "user_activities"

    # 主キー
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # ユーザー情報
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # イベント情報
    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="イベント種別: api_call / ui_action",
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="操作内容: create_project, delete_session等",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="リソース種別: project, session, tree等",
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="対象リソースのID",
    )

    # リクエスト情報
    endpoint: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="APIエンドポイント",
    )
    method: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="HTTPメソッド",
    )
    page_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="ページパス（UI操作時）",
    )

    # 結果情報
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
        index=True,
        comment="処理結果: success / error",
    )
    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTPステータスコード",
    )

    # エラー情報
    error_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="エラー種別",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="エラーメッセージ",
    )

    # パフォーマンス情報
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="処理時間（ミリ秒）",
    )

    # クライアント情報
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="クライアントIPアドレス",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="ユーザーエージェント",
    )

    # 追加メタデータ
    metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="追加メタデータ",
    )

    # タイムスタンプ（更新不要のため created_at のみ）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default="now()",
        comment="記録日時",
    )

    # リレーションシップ
    user = relationship("UserAccount", back_populates="activities", lazy="selectin")

    # 複合インデックス
    __table_args__ = (
        Index("ix_user_activities_user_created", "user_id", "created_at"),
        Index("ix_user_activities_action_created", "action", "created_at"),
        {"comment": "ユーザー操作履歴"},
    )

    def __repr__(self) -> str:
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, action={self.action}, status={self.status})>"
