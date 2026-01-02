"""データベースモデル。"""

# Analysis models
from app.models.analysis import (
    AnalysisChat,
    AnalysisDummyChartMaster,
    AnalysisDummyFormulaMaster,
    AnalysisFile,
    AnalysisGraphAxisMaster,
    AnalysisIssueMaster,
    AnalysisSession,
    AnalysisSnapshot,
    AnalysisStep,
    AnalysisTemplate,
    AnalysisValidationMaster,
)

# Audit models
from app.models.audit import AuditLog, UserActivity

# Base classes
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

# Driver Tree models
from app.models.driver_tree import (
    DriverTree,
    DriverTreeCategory,
    DriverTreeDataFrame,
    DriverTreeFile,
    DriverTreeFormula,
    DriverTreeNode,
    DriverTreePolicy,
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
    DriverTreeTemplate,
)

# Enum definitions
from app.models.enums import (
    ActionType,
    AlertConditionType,
    AnnouncementType,
    AuditEventType,
    AuditSeverity,
    CleanupTargetType,
    ComparisonOperator,
    DriverTreeColumnRoleEnum,
    DriverTreeKpiEnum,
    DriverTreeNodeTypeEnum,
    DriverTreePolicyStatusEnum,
    LanguageEnum,
    NotificationChannel,
    NotificationTypeEnum,
    ProjectRole,
    ProjectViewEnum,
    ReferenceTypeEnum,
    ResourceType,
    RoleChangeActionEnum,
    RoleTypeEnum,
    SessionTerminationReason,
    SettingCategory,
    SettingValueType,
    SystemUserRole,
    ThemeEnum,
)

# Notification models
from app.models.notification import (
    UserNotification,
)

# Project models
from app.models.project import Project, ProjectFile, ProjectMember

# System models
from app.models.system import (
    NotificationTemplate,
    SystemAlert,
    SystemAnnouncement,
    SystemSetting,
)

# User models
from app.models.user_account import RoleHistory, UserAccount, UserSession

__all__ = [
    # Base classes
    "Base",
    "PrimaryKeyMixin",
    "TimestampMixin",
    # Enum definitions - Admin
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
    # Enum definitions - User
    "ThemeEnum",
    "LanguageEnum",
    "ProjectViewEnum",
    "RoleChangeActionEnum",
    "RoleTypeEnum",
    # Enum definitions - Role
    "SystemUserRole",
    "ProjectRole",
    # Enum definitions - Notification
    "NotificationTypeEnum",
    "ReferenceTypeEnum",
    # Enum definitions - Driver Tree
    "DriverTreeNodeTypeEnum",
    "DriverTreeColumnRoleEnum",
    "DriverTreeKpiEnum",
    "DriverTreePolicyStatusEnum",
    # User models
    "UserAccount",
    "UserSession",
    "RoleHistory",
    # Project models
    "Project",
    "ProjectFile",
    "ProjectMember",
    # Analysis models - Master
    "AnalysisValidationMaster",
    "AnalysisIssueMaster",
    "AnalysisGraphAxisMaster",
    "AnalysisDummyFormulaMaster",
    "AnalysisDummyChartMaster",
    # Analysis models - Session
    "AnalysisFile",
    "AnalysisSession",
    "AnalysisSnapshot",
    "AnalysisChat",
    "AnalysisStep",
    # Analysis models - Template
    "AnalysisTemplate",
    # Driver Tree models
    "DriverTree",
    "DriverTreeCategory",
    "DriverTreeFormula",
    "DriverTreeRelationship",
    "DriverTreeRelationshipChild",
    "DriverTreeNode",
    "DriverTreeFile",
    "DriverTreeDataFrame",
    "DriverTreePolicy",
    "DriverTreeTemplate",
    # Notification models
    "UserNotification",
    # Audit models
    "UserActivity",
    "AuditLog",
    # System models
    "SystemSetting",
    "SystemAnnouncement",
    "NotificationTemplate",
    "SystemAlert",
]
