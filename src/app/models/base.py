"""SQLAlchemy基底クラスと共通ミックスイン定義。

このモジュールは、すべてのデータベースモデル（ORMクラス）の基底クラスと、
共通機能を提供するミックスインクラスを提供します。

クラス:
    - Base: SQLAlchemy 2.0のDeclarativeBase
    - TimestampMixin: created_at, updated_atフィールドを提供
    - PrimaryKeyMixin: id主キーフィールドを提供

使用方法:
    >>> from sqlalchemy.orm import Mapped, mapped_column
    >>> from app.models.base import Base, TimestampMixin, PrimaryKeyMixin
    >>>
    >>> class SampleUser(Base, TimestampMixin, PrimaryKeyMixin):
    ...     __tablename__ = "sample_users"
    ...
    ...     email: Mapped[str] = mapped_column(unique=True)
    ...     username: Mapped[str]

Note:
    - すべてのモデルはBaseを継承してください
    - タイムスタンプが必要な場合はTimestampMixinを追加
    - 主キーidが必要な場合はPrimaryKeyMixinを追加
    - 本番環境ではAlembicマイグレーションを使用します
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """すべてのデータベースモデル（ORMクラス）の基底クラス。

    SQLAlchemy 2.0のDeclarativeBaseを継承し、テーブルマッピングの基盤を提供します。
    アプリケーション内のすべてのモデル（User, Session, File等）はこのクラスを継承します。

    機能:
        - metadata: すべてのテーブル定義を保持するMetaDataオブジェクト
        - __tablename__: 各モデルで定義するテーブル名
        - カラム定義: Mapped[型]アノテーションでカラムを定義

    使用方法:
        >>> from sqlalchemy.orm import Mapped, mapped_column
        >>> from app.models.base import Base, TimestampMixin, PrimaryKeyMixin
        >>>
        >>> class SampleUser(Base, TimestampMixin, PrimaryKeyMixin):
        ...     __tablename__ = "sample_users"
        ...
        ...     email: Mapped[str] = mapped_column(unique=True)
        ...     username: Mapped[str]

    Note:
        - すべてのモデルはこのBaseを継承してください
        - 共通フィールドはミックスインクラスを使用
        - Base.metadata.create_all()でテーブル作成（開発環境のみ）
        - 本番環境ではAlembicマイグレーションを使用します
    """


class PrimaryKeyMixin:
    """主キー（id）を提供するミックスイン。

    すべてのモデルで共通のUUID型主キーを提供します。
    UUID v4形式でランダム生成されます。

    Attributes:
        id: 主キー（UUID v4、インデックス付き）

    使用例:
        >>> class SampleUser(Base, PrimaryKeyMixin, TimestampMixin):
        ...     __tablename__ = "sample_users"
        ...     email: Mapped[str] = mapped_column(unique=True)
    """

    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        """主キーID。

        UUID v4形式のランダム生成される主キー。
        すべてのテーブルで一貫した主キー定義を提供します。

        Returns:
            Mapped[uuid.UUID]: 主キーカラム定義
        """
        return mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            index=True,
        )


class TimestampMixin:
    """タイムスタンプフィールドを提供するミックスイン。

    作成日時（created_at）と更新日時（updated_at）を自動管理します。
    すべてのタイムスタンプはUTCタイムゾーンで統一されます。

    Attributes:
        created_at: レコード作成日時（UTC、自動設定）
        updated_at: レコード更新日時（UTC、自動更新）

    実装詳細:
        - タイムゾーン: 明示的にUTCを使用（datetime.now(UTC)）
        - 作成日時: レコード挿入時に自動設定
        - 更新日時: レコード更新時に自動更新（onupdate）
        - データベース側ではなくPython側で制御（明示的なタイムゾーン管理）

    使用例:
        >>> class SampleUser(Base, PrimaryKeyMixin, TimestampMixin):
        ...     __tablename__ = "sample_users"
        ...     email: Mapped[str] = mapped_column(unique=True)
        >>>
        >>> # 使用時
        >>> user = SampleUser(email="test@example.com")
        >>> db.add(user)
        >>> await db.commit()  # created_atとupdated_atが自動設定
        >>>
        >>> user.email = "new@example.com"
        >>> await db.commit()  # updated_atが自動更新
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """レコード作成日時。

        レコードが最初にデータベースに挿入された日時を記録します。
        UTCタイムゾーンで自動設定されます。

        Returns:
            Mapped[datetime]: 作成日時カラム定義（UTC、自動設定）
        """
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        """レコード更新日時。

        レコードが最後に更新された日時を記録します。
        UTCタイムゾーンで自動設定され、更新時に自動的に更新されます。

        Returns:
            Mapped[datetime]: 更新日時カラム定義（UTC、自動更新）
        """
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            onupdate=lambda: datetime.now(UTC),
            nullable=False,
        )
