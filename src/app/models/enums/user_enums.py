"""ユーザー設定関連のEnum定義。

このモジュールは、ユーザー設定機能で使用する定数をEnumで定義します。
"""

from enum import StrEnum


class ThemeEnum(StrEnum):
    """テーマ設定。

    Values:
        LIGHT: ライトテーマ
        DARK: ダークテーマ
        SYSTEM: システム設定に従う
    """

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class LanguageEnum(StrEnum):
    """言語設定。

    Values:
        JA: 日本語
        EN: 英語
    """

    JA = "ja"
    EN = "en"


class ProjectViewEnum(StrEnum):
    """プロジェクト表示形式。

    Values:
        GRID: グリッド表示
        LIST: リスト表示
    """

    GRID = "grid"
    LIST = "list"


class RoleChangeActionEnum(StrEnum):
    """ロール変更アクション種別。

    Values:
        GRANT: ロール付与
        REVOKE: ロール削除
        UPDATE: ロール更新（複数ロールの一括変更）
    """

    GRANT = "grant"
    REVOKE = "revoke"
    UPDATE = "update"


class RoleTypeEnum(StrEnum):
    """ロール種別。

    Values:
        SYSTEM: システムロール
        PROJECT: プロジェクトロール
    """

    SYSTEM = "system"
    PROJECT = "project"
