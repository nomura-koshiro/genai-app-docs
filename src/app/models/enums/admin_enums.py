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
