"""ユーザー認証およびプロフィール管理のためのデータベースモデル。

このモジュールは、アプリケーションのユーザー管理の中核となるUserモデルを定義します。
認証情報、プロフィール情報、セキュリティ監査フィールド、リレーションシップを含みます。

主な機能:
    - ユーザー認証（メール/パスワード）
    - アカウント管理（アクティブ状態、管理者権限）
    - セキュリティ監査（ログイン追跡、アカウントロック）
    - リレーションシップ（セッション、ファイル）

セキュリティ機能:
    - パスワードハッシュ化（bcrypt）
    - ログイン失敗追跡（failed_login_attempts）
    - アカウントロック機能（locked_until）
    - IPアドレス追跡（IPv6対応）

パフォーマンス最適化:
    - 複合インデックス（email + is_active, username + is_active）
    - 個別インデックス（id, email, username）

使用例:
    >>> from app.models.sample.sample_user import SampleUser
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>>
    >>> async with get_db() as db:
    ...     user = SampleUser(
    ...         email="user@example.com",
    ...         username="johndoe",
    ...         hashed_password="$2b$12$...",
    ...         is_active=True,
    ...         is_superuser=False
    ...     )
    ...     db.add(user)
    ...     await db.commit()
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.sample.sample_session import SampleSession


class SampleUser(Base, PrimaryKeyMixin, TimestampMixin):
    """サンプル: ユーザーアカウント情報とセキュリティ監査を管理するモデル。

    このモデルは、ユーザー認証、プロフィール管理、セキュリティ監査を提供します。

    テーブル設計:
        - テーブル名: sample_users
        - プライマリキー: id（自動インクリメント整数）
        - ユニーク制約: email, username

    フィールドカテゴリ:
        認証情報:
            - email: メールアドレス（ログインID、ユニーク）
            - username: ユーザー名（表示名、ユニーク）
            - hashed_password: bcryptハッシュ化されたパスワード

        アカウント状態:
            - is_active: アクティブフラグ（False=無効化されたアカウント）
            - is_superuser: 管理者権限フラグ（True=スーパーユーザー）

        タイムスタンプ:
            - created_at: アカウント作成日時（UTC、自動設定）
            - updated_at: 最終更新日時（UTC、自動更新）

        セキュリティ監査:
            - last_login_at: 最終ログイン日時（UTC）
            - last_login_ip: 最終ログインIPアドレス（IPv4/IPv6対応）
            - failed_login_attempts: ログイン失敗回数（アカウントロック用）
            - locked_until: アカウントロック解除日時（None=ロックなし）

    インデックス戦略:
        - idx_user_email_active: (email, is_active) 複合インデックス
          → ログイン認証クエリを高速化
        - idx_user_username_active: (username, is_active) 複合インデックス
          → アクティブユーザー検索を高速化
        - email, username: 個別ユニークインデックス（UNIQUE制約により自動生成）

    セキュリティ考慮事項:
        - パスワードは必ずbcryptでハッシュ化してから保存
        - 平文パスワードは絶対にデータベースに保存しない
        - ログイン失敗時はfailed_login_attemptsをインクリメント
        - 一定回数失敗後、locked_untilを設定してアカウントをロック

    Example:
        >>> # ユーザー作成（サービス層経由を推奨）
        >>> user = SampleUser(
        ...     email="john@example.com",
        ...     username="johndoe",
        ...     hashed_password="$2b$12$KIX...",  # bcrypt hash
        ...     is_active=True,
        ...     is_superuser=False
        ... )
        >>> db.add(user)
        >>> await db.commit()
        >>>
        >>> # アカウントロック設定
        >>> from datetime import timedelta
        >>> user.failed_login_attempts = 5
        >>> user.locked_until = datetime.now(UTC) + timedelta(hours=1)
        >>> await db.commit()

    Note:
        - emailとusernameは大文字小文字を区別します
        - パスワードハッシュ化にはapp.core.security.hash_password()を使用
        - タイムゾーンは必ずUTCを使用（datetime.now(UTC)）
    """

    __tablename__ = "sample_user"

    # PrimaryKeyMixinからid継承
    # TimestampMixinからcreated_at, updated_at継承

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)  # bcryptは通常60文字
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 監査フィールド
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,  # IPv6対応
    )
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # リフレッシュトークン関連（セキュリティ: ハッシュ化して保存）
    refresh_token_hash: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # APIキー認証関連（セキュリティ: ハッシュ化して保存）
    api_key_hash: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None, index=True)
    api_key_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # クエリ最適化のための複合インデックス
    __table_args__ = (
        Index("idx_sample_user_email_active", "email", "is_active"),
        Index("idx_sample_user_username_active", "username", "is_active"),
    )

    # リレーションシップ
    sessions: Mapped[list["SampleSession"]] = relationship("SampleSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """デバッグ用のユーザーオブジェクト文字列表現を返します。

        このメソッドは、ログ出力やデバッグ時にユーザーオブジェクトを
        識別しやすい形式で表示するために使用されます。

        Returns:
            str: ユーザーの識別情報を含む文字列
                フォーマット: "<User(id=1, email=user@example.com)>"

        Example:
            >>> user = SampleUser(id=1, email="john@example.com", username="johndoe")
            >>> print(user)
            <SampleUser(id=1, email=john@example.com)>
            >>> repr(user)
            '<SampleUser(id=1, email=john@example.com)>'

        Note:
            - この表現はログ出力やデバッグ用です
            - JSON応答にはPydanticスキーマを使用してください
            - 機密情報（hashed_password等）は含まれません
        """
        return f"<SampleUser(id={self.id}, email={self.email})>"
