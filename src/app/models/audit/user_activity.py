"""ユーザー操作履歴モデル。

このモジュールは、ユーザーのAPI操作履歴を記録するモデルを定義します。

主な機能:
    - 全APIリクエストの自動記録
    - エラー情報の追跡
    - パフォーマンス計測

テーブル設計:
    - テーブル名: user_activity
    - プライマリキー: id (UUID)
    - 外部キー: user_id -> user_account.id

使用例:
    >>> from app.models.audit.user_activity import UserActivity
    >>> activity = UserActivity(
    ...     user_id=user_id,
    ...     action_type="CREATE",
    ...     resource_type="PROJECT",
    ...     endpoint="/api/v1/projects",
    ...     method="POST",
    ...     response_status=201,
    ...     duration_ms=150
    ... )
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class UserActivity(Base, TimestampMixin):
    """ユーザー操作履歴モデル。

    全APIリクエストを記録し、操作追跡・エラー分析に使用します。

    Attributes:
        id (UUID): プライマリキー
        user_id (UUID | None): 操作ユーザーID（未認証時はNULL）
        action_type (str): 操作種別（CREATE/READ/UPDATE/DELETE/LOGIN/LOGOUT/ERROR）
        resource_type (str | None): リソース種別（PROJECT/SESSION/TREE等）
        resource_id (UUID | None): 操作対象リソースID
        endpoint (str): APIエンドポイント
        method (str): HTTPメソッド
        request_body (dict | None): リクエストボディ（機密情報除外）
        response_status (int): HTTPレスポンスステータス
        error_message (str | None): エラーメッセージ
        error_code (str | None): エラーコード
        ip_address (str | None): クライアントIPアドレス
        user_agent (str | None): ユーザーエージェント
        duration_ms (int): 処理時間（ミリ秒）
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    インデックス:
        - idx_user_activity_user_id: user_id
        - idx_user_activity_action_type: action_type
        - idx_user_activity_resource: (resource_type, resource_id)
        - idx_user_activity_created_at: created_at DESC
        - idx_user_activity_status: response_status
        - idx_user_activity_error: created_at DESC WHERE error_message IS NOT NULL
    """

    __tablename__ = "user_activity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作ユーザーID（FK: user_account、未認証時はNULL）",
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="操作種別（CREATE/READ/UPDATE/DELETE/LOGIN/LOGOUT/ERROR）",
    )

    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="リソース種別（PROJECT/SESSION/TREE等）",
    )

    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="操作対象リソースID",
    )

    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="APIエンドポイント",
    )

    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="HTTPメソッド",
    )

    request_body: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="リクエストボディ（機密情報除外）",
    )

    response_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="HTTPレスポンスステータス",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="エラーメッセージ（エラー時のみ）",
    )

    error_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="エラーコード",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="クライアントIPアドレス（IPv6対応）",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="ユーザーエージェント",
    )

    duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="処理時間（ミリ秒）",
    )

    # リレーションシップ
    user: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (
        Index("idx_user_activity_user_id", "user_id"),
        Index("idx_user_activity_action_type", "action_type"),
        Index("idx_user_activity_resource", "resource_type", "resource_id"),
        Index(
            "idx_user_activity_created_at",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
        Index("idx_user_activity_status", "response_status"),
        Index(
            "idx_user_activity_error",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
            postgresql_where="error_message IS NOT NULL",
        ),
    )

    def __repr__(self) -> str:
        return f"<UserActivity(id={self.id}, action={self.action_type}, endpoint={self.endpoint})>"
