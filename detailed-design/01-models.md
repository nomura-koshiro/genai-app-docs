# システム管理機能 詳細設計書 - モデル層

## 1. 概要

本ドキュメントでは、システム管理機能（SA-001〜SA-043）で追加するSQLAlchemyモデルの詳細設計を定義する。

### 1.1 既存パターンへの準拠

既存のモデル実装パターンに従い、以下の規約を適用する：

- `Base` クラスを継承
- `TimestampMixin` で `created_at`, `updated_at` を自動管理
- UUID型の主キー（`uuid.uuid4()` でデフォルト生成）
- `TYPE_CHECKING` による循環インポート回避
- `Mapped[型]` 型ヒントの使用
- リレーションシップは `relationship()` で定義、`cascade="all, delete-orphan"` を適切に設定

### 1.2 ファイル構成

```
src/app/models/
├── audit/
│   ├── __init__.py
│   ├── user_activity.py          # SA-001〜SA-006
│   └── audit_log.py              # SA-012〜SA-016
├── system/
│   ├── __init__.py
│   ├── system_setting.py         # SA-017〜SA-020
│   ├── system_announcement.py    # SA-033〜SA-034
│   ├── notification_template.py  # SA-032
│   └── system_alert.py           # SA-031
└── user_account/
    └── user_session.py           # SA-035〜SA-036（追加）
```

---

## 2. 共通定数定義（Enum）

### 2.1 定数Enum定義

**ファイル**: `src/app/models/enums/admin_enums.py`

文字列リテラルを `StrEnum` で型安全に管理します。

```python
"""システム管理機能用の定数Enum定義。

このモジュールは、システム管理機能で使用する定数をEnumで定義します。
文字列リテラルを型安全に管理し、コード補完・バリデーションを強化します。
"""

from enum import StrEnum


class ActionType(StrEnum):
    """操作種別。

    ユーザー操作履歴で使用する操作種別を定義します。

    Values:
        CREATE: リソース作成
        READ: リソース参照
        UPDATE: リソース更新
        DELETE: リソース削除
        LOGIN: ログイン
        LOGOUT: ログアウト
        EXPORT: データエクスポート
        IMPORT: データインポート
        BULK_UPDATE: 一括更新
        BULK_DELETE: 一括削除
        ERROR: エラー発生
    """

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    BULK_UPDATE = "BULK_UPDATE"
    BULK_DELETE = "BULK_DELETE"
    ERROR = "ERROR"


class ResourceType(StrEnum):
    """リソース種別。

    操作対象のリソース種別を定義します。

    Values:
        USER: ユーザー
        PROJECT: プロジェクト
        SESSION: 分析セッション
        TREE: ドライバーツリー
        FILE: ファイル
        SETTING: システム設定
        ANNOUNCEMENT: お知らせ
        TEMPLATE: 通知テンプレート
        ALERT: システムアラート
    """

    USER = "USER"
    PROJECT = "PROJECT"
    SESSION = "SESSION"
    TREE = "TREE"
    FILE = "FILE"
    SETTING = "SETTING"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    TEMPLATE = "TEMPLATE"
    ALERT = "ALERT"


class AuditEventType(StrEnum):
    """監査イベント種別。

    監査ログで記録するイベントの種別を定義します。

    Values:
        DATA_CHANGE: データ変更（作成/更新/削除）
        ACCESS: アクセス（ログイン/ログアウト/参照）
        SECURITY: セキュリティイベント（権限変更/認証失敗等）
        SYSTEM: システムイベント（設定変更/メンテナンス等）
    """

    DATA_CHANGE = "DATA_CHANGE"
    ACCESS = "ACCESS"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"


class AuditSeverity(StrEnum):
    """監査ログ重要度。

    監査ログの重要度レベルを定義します。

    Values:
        DEBUG: デバッグ情報
        INFO: 通常の操作
        WARNING: 警告（注意が必要な操作）
        ERROR: エラー（失敗した操作）
        CRITICAL: 重大（セキュリティ違反等）
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AnnouncementType(StrEnum):
    """お知らせ種別。

    システムお知らせの種別を定義します。

    Values:
        INFO: 一般情報
        WARNING: 警告・注意喚起
        MAINTENANCE: メンテナンス予告
        RELEASE: リリース情報
        URGENT: 緊急連絡
    """

    INFO = "INFO"
    WARNING = "WARNING"
    MAINTENANCE = "MAINTENANCE"
    RELEASE = "RELEASE"
    URGENT = "URGENT"


class AlertConditionType(StrEnum):
    """アラート条件種別。

    システムアラートの発火条件種別を定義します。

    Values:
        ERROR_RATE: エラー率
        RESPONSE_TIME: レスポンス時間
        STORAGE_USAGE: ストレージ使用量
        ACTIVE_SESSIONS: アクティブセッション数
        LOGIN_FAILURES: ログイン失敗数
        CUSTOM: カスタム条件
    """

    ERROR_RATE = "ERROR_RATE"
    RESPONSE_TIME = "RESPONSE_TIME"
    STORAGE_USAGE = "STORAGE_USAGE"
    ACTIVE_SESSIONS = "ACTIVE_SESSIONS"
    LOGIN_FAILURES = "LOGIN_FAILURES"
    CUSTOM = "CUSTOM"


class ComparisonOperator(StrEnum):
    """比較演算子。

    アラート閾値の比較演算子を定義します。

    Values:
        GT: より大きい (>)
        GTE: 以上 (>=)
        LT: より小さい (<)
        LTE: 以下 (<=)
        EQ: 等しい (==)
        NEQ: 等しくない (!=)
    """

    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EQ = "EQ"
    NEQ = "NEQ"


class NotificationChannel(StrEnum):
    """通知チャンネル。

    アラート通知先のチャンネルを定義します。

    Values:
        EMAIL: メール通知
        SLACK: Slack通知
        TEAMS: Microsoft Teams通知
        WEBHOOK: Webhook通知
        IN_APP: アプリ内通知
    """

    EMAIL = "EMAIL"
    SLACK = "SLACK"
    TEAMS = "TEAMS"
    WEBHOOK = "WEBHOOK"
    IN_APP = "IN_APP"


class SessionTerminationReason(StrEnum):
    """セッション終了理由。

    ユーザーセッションが終了した理由を定義します。

    Values:
        LOGOUT: 通常ログアウト
        EXPIRED: 有効期限切れ
        FORCED: 管理者による強制終了
        PASSWORD_CHANGED: パスワード変更による無効化
        ACCOUNT_DISABLED: アカウント無効化
        SECURITY: セキュリティ上の理由
    """

    LOGOUT = "LOGOUT"
    EXPIRED = "EXPIRED"
    FORCED = "FORCED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    SECURITY = "SECURITY"


class CleanupTargetType(StrEnum):
    """クリーンアップ対象種別。

    データクリーンアップの対象種別を定義します。

    Values:
        ACTIVITY_LOGS: 操作履歴
        AUDIT_LOGS: 監査ログ
        DELETED_PROJECTS: 削除済みプロジェクト
        SESSION_LOGS: セッションログ
        ORPHAN_FILES: 孤立ファイル
        TEMP_FILES: 一時ファイル
    """

    ACTIVITY_LOGS = "ACTIVITY_LOGS"
    AUDIT_LOGS = "AUDIT_LOGS"
    DELETED_PROJECTS = "DELETED_PROJECTS"
    SESSION_LOGS = "SESSION_LOGS"
    ORPHAN_FILES = "ORPHAN_FILES"
    TEMP_FILES = "TEMP_FILES"


class SettingCategory(StrEnum):
    """システム設定カテゴリ。

    システム設定のカテゴリを定義します。

    Values:
        GENERAL: 一般設定
        SECURITY: セキュリティ設定
        NOTIFICATION: 通知設定
        MAINTENANCE: メンテナンス設定
        STORAGE: ストレージ設定
        API: API設定
    """

    GENERAL = "GENERAL"
    SECURITY = "SECURITY"
    NOTIFICATION = "NOTIFICATION"
    MAINTENANCE = "MAINTENANCE"
    STORAGE = "STORAGE"
    API = "API"


class SettingValueType(StrEnum):
    """設定値の型。

    システム設定の値の型を定義します。

    Values:
        STRING: 文字列
        NUMBER: 数値
        BOOLEAN: 真偽値
        JSON: JSON（オブジェクト/配列）
    """

    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
```

### 2.2 Enumの使用例

```python
# モデルでの使用例
from app.models.enums.admin_enums import ActionType, ResourceType

class UserActivity(Base, TimestampMixin):
    action_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="操作種別",
    )

    # バリデーション用にCheckConstraintを追加
    __table_args__ = (
        CheckConstraint(
            f"action_type IN ({', '.join(repr(e.value) for e in ActionType)})",
            name="ck_user_activity_action_type",
        ),
    )


# サービスでの使用例
from app.models.enums.admin_enums import ActionType

async def record_activity(self, action_type: ActionType, ...):
    await self.repository.create(
        action_type=action_type.value,  # または action_type（StrEnumは自動変換）
        ...
    )
```

---

## 3. モデル詳細設計

### 3.1 UserActivity（ユーザー操作履歴）

**ファイル**: `src/app/models/audit/user_activity.py`

**対応ユースケース**: SA-001〜SA-006

```python
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

from sqlalchemy import Index, Integer, String, Text
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
        Index("idx_user_activity_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
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
```

---

### 2.2 AuditLog（監査ログ）

**ファイル**: `src/app/models/audit/audit_log.py`

**対応ユースケース**: SA-012〜SA-016

```python
"""監査ログモデル。

このモジュールは、データ変更・アクセス・セキュリティイベントの監査ログを定義します。

主な機能:
    - データ変更履歴の追跡（old_value/new_value）
    - アクセスログの記録
    - セキュリティイベントの記録

テーブル設計:
    - テーブル名: audit_log
    - プライマリキー: id (UUID)
    - 外部キー: user_id -> user_account.id
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class AuditEventType(str, Enum):
    """監査イベント種別。"""
    DATA_CHANGE = "DATA_CHANGE"
    ACCESS = "ACCESS"
    SECURITY = "SECURITY"


class AuditSeverity(str, Enum):
    """監査ログ重要度。"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AuditLog(Base, TimestampMixin):
    """監査ログモデル。

    データ変更、アクセス、セキュリティイベントを記録します。

    Attributes:
        id (UUID): プライマリキー
        user_id (UUID | None): 操作ユーザーID
        event_type (str): イベント種別（DATA_CHANGE/ACCESS/SECURITY）
        action (str): アクション（CREATE/UPDATE/DELETE/LOGIN_SUCCESS/LOGIN_FAILED等）
        resource_type (str): リソース種別
        resource_id (UUID | None): リソースID
        old_value (dict | None): 変更前の値
        new_value (dict | None): 変更後の値
        changed_fields (list | None): 変更されたフィールド一覧
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        severity (str): 重要度（INFO/WARNING/CRITICAL）
        metadata (dict | None): 追加メタデータ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    インデックス:
        - idx_audit_log_user_id: user_id
        - idx_audit_log_event_type: event_type
        - idx_audit_log_resource: (resource_type, resource_id)
        - idx_audit_log_severity: severity
        - idx_audit_log_created_at: created_at DESC
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="操作ユーザーID",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="イベント種別（DATA_CHANGE/ACCESS/SECURITY）",
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="アクション（CREATE/UPDATE/DELETE/LOGIN_SUCCESS/LOGIN_FAILED等）",
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="リソース種別",
    )

    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="リソースID",
    )

    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="変更前の値",
    )

    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="変更後の値",
    )

    changed_fields: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="変更されたフィールド一覧",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IPアドレス",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="ユーザーエージェント",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditSeverity.INFO.value,
        comment="重要度（INFO/WARNING/CRITICAL）",
    )

    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="追加メタデータ",
    )

    # リレーションシップ
    user: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (
        Index("idx_audit_log_user_id", "user_id"),
        Index("idx_audit_log_event_type", "event_type"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_severity", "severity"),
        Index("idx_audit_log_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event={self.event_type}, action={self.action})>"
```

---

### 2.3 SystemSetting（システム設定）

**ファイル**: `src/app/models/system/system_setting.py`

**対応ユースケース**: SA-017〜SA-020

```python
"""システム設定モデル。

このモジュールは、アプリケーション全体の設定を管理するモデルを定義します。

主な機能:
    - カテゴリ別設定管理
    - 型情報の保持
    - 機密設定のフラグ管理

テーブル設計:
    - テーブル名: system_setting
    - プライマリキー: id (UUID)
    - ユニーク制約: (category, key)
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class SettingCategory(str, Enum):
    """設定カテゴリ。"""
    GENERAL = "GENERAL"
    SECURITY = "SECURITY"
    MAINTENANCE = "MAINTENANCE"


class SettingValueType(str, Enum):
    """設定値の型。"""
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"


class SystemSetting(Base, TimestampMixin):
    """システム設定モデル。

    アプリケーション全体の設定値を管理します。

    Attributes:
        id (UUID): プライマリキー
        category (str): カテゴリ（GENERAL/SECURITY/MAINTENANCE）
        key (str): 設定キー
        value (dict): 設定値（JSONB）
        value_type (str): 値の型（STRING/NUMBER/BOOLEAN/JSON）
        description (str | None): 説明
        is_secret (bool): 機密設定フラグ
        is_editable (bool): 編集可能フラグ
        updated_by (UUID | None): 更新者ID
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    ユニーク制約:
        - uq_system_setting_category_key: (category, key)
    """

    __tablename__ = "system_setting"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="カテゴリ（GENERAL/SECURITY/MAINTENANCE）",
    )

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="設定キー",
    )

    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="設定値",
    )

    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="値の型（STRING/NUMBER/BOOLEAN/JSON）",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="説明",
    )

    is_secret: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="機密設定フラグ",
    )

    is_editable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="編集可能フラグ",
    )

    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID",
    )

    # リレーションシップ
    updater: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[updated_by],
        lazy="selectin",
    )

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint("category", "key", name="uq_system_setting_category_key"),
    )

    def __repr__(self) -> str:
        return f"<SystemSetting(id={self.id}, category={self.category}, key={self.key})>"
```

---

### 2.4 SystemAnnouncement（システムお知らせ）

**ファイル**: `src/app/models/system/system_announcement.py`

**対応ユースケース**: SA-033〜SA-034

```python
"""システムお知らせモデル。

このモジュールは、システム全体のお知らせを管理するモデルを定義します。

主な機能:
    - お知らせの作成・管理
    - 表示期間の制御
    - 対象ロールの指定

テーブル設計:
    - テーブル名: system_announcement
    - プライマリキー: id (UUID)
    - 外部キー: created_by -> user_account.id
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class AnnouncementType(str, Enum):
    """お知らせ種別。"""
    INFO = "INFO"
    WARNING = "WARNING"
    MAINTENANCE = "MAINTENANCE"


class SystemAnnouncement(Base, TimestampMixin):
    """システムお知らせモデル。

    システム全体のお知らせを管理します。

    Attributes:
        id (UUID): プライマリキー
        title (str): タイトル
        content (str): 本文
        announcement_type (str): 種別（INFO/WARNING/MAINTENANCE）
        priority (int): 優先度（1が最高、デフォルト: 5）
        start_at (datetime): 表示開始日時
        end_at (datetime | None): 表示終了日時（NULLは無期限）
        is_active (bool): 有効フラグ
        target_roles (list | None): 対象ロール（NULLまたは空配列は全員）
        created_by (UUID): 作成者ID
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    インデックス:
        - idx_announcement_active: (is_active, start_at, end_at)
    """

    __tablename__ = "system_announcement"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="タイトル",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="本文",
    )

    announcement_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="種別（INFO/WARNING/MAINTENANCE）",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="優先度（1が最高）",
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="表示開始日時",
    )

    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="表示終了日時（NULLは無期限）",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="有効フラグ",
    )

    target_roles: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="対象ロール（NULLまたは空配列は全員）",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="作成者ID",
    )

    # リレーションシップ
    creator: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (
        Index("idx_announcement_active", "is_active", "start_at", "end_at"),
    )

    def __repr__(self) -> str:
        return f"<SystemAnnouncement(id={self.id}, title={self.title})>"
```

---

### 2.5 NotificationTemplate（通知テンプレート）

**ファイル**: `src/app/models/system/notification_template.py`

**対応ユースケース**: SA-032

```python
"""通知テンプレートモデル。

このモジュールは、通知メッセージのテンプレートを管理するモデルを定義します。

主な機能:
    - イベント種別ごとのテンプレート管理
    - 変数置換のサポート
    - テンプレートの有効/無効管理

テーブル設計:
    - テーブル名: notification_template
    - プライマリキー: id (UUID)
"""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class NotificationTemplate(Base, TimestampMixin):
    """通知テンプレートモデル。

    通知メッセージのテンプレートを管理します。

    Attributes:
        id (UUID): プライマリキー
        name (str): テンプレート名
        event_type (str): イベント種別（PROJECT_CREATED/MEMBER_ADDED等）
        subject (str): 件名テンプレート
        body (str): 本文テンプレート
        variables (list): 利用可能変数リスト
        is_active (bool): 有効フラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）
    """

    __tablename__ = "notification_template"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="テンプレート名",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="イベント種別（PROJECT_CREATED/MEMBER_ADDED等）",
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="件名テンプレート",
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="本文テンプレート",
    )

    variables: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="利用可能変数リスト",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="有効フラグ",
    )

    def __repr__(self) -> str:
        return f"<NotificationTemplate(id={self.id}, event_type={self.event_type})>"
```

---

### 2.6 SystemAlert（システムアラート設定）

**ファイル**: `src/app/models/system/system_alert.py`

**対応ユースケース**: SA-031

```python
"""システムアラート設定モデル。

このモジュールは、システム監視アラートの設定を管理するモデルを定義します。

主な機能:
    - 条件ベースのアラート設定
    - 通知チャネルの指定
    - 発火履歴の追跡

テーブル設計:
    - テーブル名: system_alert
    - プライマリキー: id (UUID)
    - 外部キー: created_by -> user_account.id
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class AlertConditionType(str, Enum):
    """アラート条件種別。"""
    ERROR_RATE = "ERROR_RATE"
    STORAGE_USAGE = "STORAGE_USAGE"
    INACTIVE_USERS = "INACTIVE_USERS"
    API_LATENCY = "API_LATENCY"
    LOGIN_FAILURES = "LOGIN_FAILURES"


class ComparisonOperator(str, Enum):
    """比較演算子。"""
    GT = "GT"    # Greater Than
    GTE = "GTE"  # Greater Than or Equal
    LT = "LT"    # Less Than
    LTE = "LTE"  # Less Than or Equal
    EQ = "EQ"    # Equal


class SystemAlert(Base, TimestampMixin):
    """システムアラート設定モデル。

    システム監視アラートの設定を管理します。

    Attributes:
        id (UUID): プライマリキー
        name (str): アラート名
        condition_type (str): 条件種別
        threshold (dict): 閾値設定
        comparison_operator (str): 比較演算子
        notification_channels (list): 通知先
        is_enabled (bool): 有効フラグ
        last_triggered_at (datetime | None): 最終発火日時
        trigger_count (int): 発火回数
        created_by (UUID): 作成者ID
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）
    """

    __tablename__ = "system_alert"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="アラート名",
    )

    condition_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="条件種別（ERROR_RATE/STORAGE_USAGE等）",
    )

    threshold: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="閾値設定",
    )

    comparison_operator: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="比較演算子（GT/GTE/LT/LTE/EQ）",
    )

    notification_channels: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="通知先（EMAIL/SLACK等）",
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="有効フラグ",
    )

    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最終発火日時",
    )

    trigger_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="発火回数",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="作成者ID",
    )

    # リレーションシップ
    creator: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SystemAlert(id={self.id}, name={self.name})>"
```

---

### 2.7 UserSession（ユーザーセッション）

**ファイル**: `src/app/models/user_account/user_session.py`

**対応ユースケース**: SA-035〜SA-036

```python
"""ユーザーセッションモデル。

このモジュールは、ユーザーのログインセッションを管理するモデルを定義します。

主な機能:
    - セッション情報の管理
    - デバイス情報の記録
    - 強制ログアウト対応

テーブル設計:
    - テーブル名: user_session
    - プライマリキー: id (UUID)
    - 外部キー: user_id -> user_account.id
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class LogoutReason(str, Enum):
    """ログアウト理由。"""
    MANUAL = "MANUAL"           # ユーザー自身によるログアウト
    FORCED = "FORCED"           # 管理者による強制ログアウト
    EXPIRED = "EXPIRED"         # セッション期限切れ
    SESSION_LIMIT = "SESSION_LIMIT"  # セッション数上限


class UserSession(Base):
    """ユーザーセッションモデル。

    ユーザーのログインセッションを管理します。

    Attributes:
        id (UUID): プライマリキー
        user_id (UUID): ユーザーID
        session_token_hash (str): セッショントークンハッシュ（SHA-256）
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        device_info (dict | None): デバイス情報
        login_at (datetime): ログイン日時
        last_activity_at (datetime): 最終アクティビティ日時
        expires_at (datetime): 有効期限
        is_active (bool): アクティブフラグ
        logout_at (datetime | None): ログアウト日時
        logout_reason (str | None): ログアウト理由

    インデックス:
        - idx_user_session_user_id: user_id
        - idx_user_session_active: (is_active, expires_at)
        - idx_user_session_token: session_token_hash
    """

    __tablename__ = "user_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="ユーザーID（FK: user_account）",
    )

    session_token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="セッショントークンハッシュ（SHA-256）",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IPアドレス",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="ユーザーエージェント",
    )

    device_info: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="デバイス情報（OS、ブラウザ等）",
    )

    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="ログイン日時",
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="最終アクティビティ日時",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="有効期限",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="アクティブフラグ",
    )

    logout_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="ログアウト日時",
    )

    logout_reason: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="ログアウト理由（MANUAL/FORCED/EXPIRED/SESSION_LIMIT）",
    )

    # リレーションシップ
    user: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (
        Index("idx_user_session_user_id", "user_id"),
        Index("idx_user_session_active", "is_active", "expires_at"),
        Index("idx_user_session_token", "session_token_hash"),
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
```

---

## 3. __init__.py ファイル

### 3.1 audit/__init__.py

```python
"""監査関連モデル。"""

from app.models.audit.audit_log import AuditEventType, AuditLog, AuditSeverity
from app.models.audit.user_activity import UserActivity

__all__ = [
    "UserActivity",
    "AuditLog",
    "AuditEventType",
    "AuditSeverity",
]
```

### 3.2 system/__init__.py

```python
"""システム管理関連モデル。"""

from app.models.system.notification_template import NotificationTemplate
from app.models.system.system_alert import (
    AlertConditionType,
    ComparisonOperator,
    SystemAlert,
)
from app.models.system.system_announcement import AnnouncementType, SystemAnnouncement
from app.models.system.system_setting import (
    SettingCategory,
    SettingValueType,
    SystemSetting,
)

__all__ = [
    "SystemSetting",
    "SettingCategory",
    "SettingValueType",
    "SystemAnnouncement",
    "AnnouncementType",
    "NotificationTemplate",
    "SystemAlert",
    "AlertConditionType",
    "ComparisonOperator",
]
```

---

## 4. マイグレーション

### 4.1 マイグレーションファイル

**ファイル**: `alembic/versions/xxxx_add_system_admin_tables.py`

```python
"""add system admin tables

Revision ID: xxxx
Revises: previous_revision
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxxx'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # user_activity テーブル
    op.create_table(
        'user_activity',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('request_body', postgresql.JSONB(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_user_activity_user_id', 'user_activity', ['user_id'])
    op.create_index('idx_user_activity_action_type', 'user_activity', ['action_type'])
    op.create_index('idx_user_activity_resource', 'user_activity', ['resource_type', 'resource_id'])
    op.create_index('idx_user_activity_created_at', 'user_activity', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_user_activity_status', 'user_activity', ['response_status'])

    # audit_log テーブル
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('changed_fields', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, default='INFO'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_event_type', 'audit_log', ['event_type'])
    op.create_index('idx_audit_log_resource', 'audit_log', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_log_severity', 'audit_log', ['severity'])
    op.create_index('idx_audit_log_created_at', 'audit_log', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # system_setting テーブル
    op.create_table(
        'system_setting',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('value_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_editable', sa.Boolean(), nullable=False, default=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', 'key', name='uq_system_setting_category_key'),
    )

    # system_announcement テーブル
    op.create_table(
        'system_announcement',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('announcement_type', sa.String(30), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('target_roles', postgresql.JSONB(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_announcement_active', 'system_announcement', ['is_active', 'start_at', 'end_at'])

    # notification_template テーブル
    op.create_table(
        'notification_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False, unique=True),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('variables', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # system_alert テーブル
    op.create_table(
        'system_alert',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('condition_type', sa.String(50), nullable=False),
        sa.Column('threshold', postgresql.JSONB(), nullable=False),
        sa.Column('comparison_operator', sa.String(10), nullable=False),
        sa.Column('notification_channels', postgresql.JSONB(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # user_session テーブル
    op.create_table(
        'user_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token_hash', sa.String(64), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('login_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('logout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('logout_reason', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_user_session_user_id', 'user_session', ['user_id'])
    op.create_index('idx_user_session_active', 'user_session', ['is_active', 'expires_at'])
    op.create_index('idx_user_session_token', 'user_session', ['session_token_hash'])


def downgrade() -> None:
    op.drop_table('user_session')
    op.drop_table('system_alert')
    op.drop_table('notification_template')
    op.drop_table('system_announcement')
    op.drop_table('system_setting')
    op.drop_table('audit_log')
    op.drop_table('user_activity')
```

---

## 5. 注意事項

### 5.1 外部キー制約

- `user_activity.user_id` → `user_account.id`（未認証時NULL許容）
- `audit_log.user_id` → `user_account.id`（未認証時NULL許容）
- `system_setting.updated_by` → `user_account.id`
- `system_announcement.created_by` → `user_account.id`
- `system_alert.created_by` → `user_account.id`
- `user_session.user_id` → `user_account.id`

### 5.2 パフォーマンス考慮

- `user_activity` テーブルは高頻度で書き込みが発生するため、インデックスを最小限に抑える
- `created_at DESC` インデックスで最新レコードの取得を高速化
- 部分インデックス（`WHERE error_message IS NOT NULL`）でエラーログの検索を効率化

### 5.3 データ保持ポリシー

- `user_activity`: デフォルト90日保持
- `audit_log`: デフォルト365日保持
- `user_session`: 非アクティブセッションは30日後に削除可能
