"""Enum定義パッケージ。

このパッケージは、アプリケーション全体で使用するEnum定義を一元管理します。

モジュール構成:
    - admin_enums: 管理機能用Enum（監査、アラート、設定等）
    - user_enums: ユーザー設定用Enum（テーマ、言語等）
    - role_enums: ロール用Enum（システムロール、プロジェクトロール）
    - notification_enums: 通知用Enum（通知タイプ、参照タイプ）
    - driver_tree_enums: ドライバーツリー用Enum（ノードタイプ、KPI等）
"""

# Admin enums
from app.models.enums.admin_enums import (
    ActionType,
    AlertConditionType,
    AnnouncementType,
    AuditEventType,
    AuditSeverity,
    CleanupTargetType,
    ComparisonOperator,
    NotificationChannel,
    ResourceType,
    SessionTerminationReason,
    SettingCategory,
    SettingValueType,
)

# Driver Tree enums
from app.models.enums.driver_tree_enums import (
    DriverTreeColumnRoleEnum,
    DriverTreeKpiEnum,
    DriverTreeNodeTypeEnum,
    DriverTreePolicyStatusEnum,
)

# Notification enums
from app.models.enums.notification_enums import (
    NotificationTypeEnum,
    ReferenceTypeEnum,
)

# Role enums
from app.models.enums.role_enums import (
    ProjectRole,
    SystemUserRole,
)

# User enums
from app.models.enums.user_enums import (
    LanguageEnum,
    ProjectViewEnum,
    RoleChangeActionEnum,
    RoleTypeEnum,
    ThemeEnum,
)

__all__ = [
    # Admin enums
    "ActionType",
    "ResourceType",
    "AuditEventType",
    "AuditSeverity",
    "AnnouncementType",
    "AlertConditionType",
    "ComparisonOperator",
    "NotificationChannel",
    "SessionTerminationReason",
    "CleanupTargetType",
    "SettingCategory",
    "SettingValueType",
    # User enums
    "ThemeEnum",
    "LanguageEnum",
    "ProjectViewEnum",
    "RoleChangeActionEnum",
    "RoleTypeEnum",
    # Role enums
    "SystemUserRole",
    "ProjectRole",
    # Notification enums
    "NotificationTypeEnum",
    "ReferenceTypeEnum",
    # Driver Tree enums
    "DriverTreeNodeTypeEnum",
    "DriverTreeColumnRoleEnum",
    "DriverTreeKpiEnum",
    "DriverTreePolicyStatusEnum",
]
