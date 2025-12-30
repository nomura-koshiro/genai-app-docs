"""管理機能のPydanticスキーマ。

このモジュールは、管理機能（システム管理、カテゴリ、検証、課題マスタ、ロール、グラフ軸）の
スキーマを提供します。
"""

# Activity Log
from app.schemas.admin.activity_log import (
    ActivityLogDetailResponse,
    ActivityLogFilter,
    ActivityLogListResponse,
    ActivityLogResponse,
)

# Announcement
from app.schemas.admin.announcement import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)

# Audit Log
from app.schemas.admin.audit_log import (
    AuditLogExportFilter,
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogResponse,
)

# Bulk Operation
from app.schemas.admin.bulk_operation import (
    BulkArchiveResponse,
    BulkDeactivateResponse,
    BulkImportResponse,
    BulkProjectArchiveRequest,
    BulkUserDeactivateRequest,
    UserExportFilter,
)

# Category (existing)
from app.schemas.admin.category import (
    DriverTreeCategoryCreate,
    DriverTreeCategoryListResponse,
    DriverTreeCategoryResponse,
    DriverTreeCategoryUpdate,
)

# Data Management
from app.schemas.admin.data_management import (
    CleanupExecuteRequest,
    CleanupExecuteResponse,
    CleanupPreviewRequest,
    CleanupPreviewResponse,
    OrphanFileCleanupRequest,
    OrphanFileCleanupResponse,
    OrphanFileListResponse,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
)

# Dummy Chart (existing)
from app.schemas.admin.dummy_chart import (
    AnalysisDummyChartListResponse,
)

# Dummy Formula (existing)
from app.schemas.admin.dummy_formula import (
    AnalysisDummyFormulaListResponse,
)

# Graph Axis (existing)
from app.schemas.admin.graph_axis import (
    AnalysisGraphAxisListResponse,
)

# Health Check
from app.schemas.admin.health_check import (
    HealthCheckDetailedResponse,
    HealthCheckSimpleResponse,
)

# Issue (existing)
from app.schemas.admin.issue import (
    AnalysisIssueCreate,
    AnalysisIssueListResponse,
    AnalysisIssueResponse,
    AnalysisIssueUpdate,
)

# Notification Template
from app.schemas.admin.notification_template import (
    NotificationTemplateCreate,
    NotificationTemplateListResponse,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
)

# Project Admin
from app.schemas.admin.project_admin import (
    AdminProjectFilter,
    AdminProjectListResponse,
    AdminProjectResponse,
    ProjectStorageListResponse,
)

# Role (existing)
from app.schemas.admin.role import (
    AllRolesResponse,
    ProjectRoleListResponse,
    RoleInfo,
    SystemRoleListResponse,
)

# Session Management
from app.schemas.admin.session_management import (
    SessionFilter,
    SessionListResponse,
    SessionResponse,
    SessionTerminateRequest,
)

# Statistics
from app.schemas.admin.statistics import (
    ApiStatisticsDetailResponse,
    ErrorStatisticsDetailResponse,
    StatisticsOverviewResponse,
    StorageStatisticsDetailResponse,
    UserStatisticsDetailResponse,
)

# Support Tools
from app.schemas.admin.support_tools import (
    DebugModeResponse,
    ImpersonateEndResponse,
    ImpersonateRequest,
    ImpersonateResponse,
)

# System Alert
from app.schemas.admin.system_alert import (
    SystemAlertCreate,
    SystemAlertListResponse,
    SystemAlertResponse,
    SystemAlertUpdate,
)

# System Setting
from app.schemas.admin.system_setting import (
    MaintenanceModeEnable,
    MaintenanceModeResponse,
    SystemSettingsByCategoryResponse,
    SystemSettingUpdate,
)

# Validation (existing)
from app.schemas.admin.validation import (
    AnalysisValidationCreate,
    AnalysisValidationListResponse,
    AnalysisValidationResponse,
    AnalysisValidationUpdate,
)

__all__ = [
    # Activity Log
    "ActivityLogFilter",
    "ActivityLogResponse",
    "ActivityLogDetailResponse",
    "ActivityLogListResponse",
    # Announcement
    "AnnouncementCreate",
    "AnnouncementUpdate",
    "AnnouncementResponse",
    "AnnouncementListResponse",
    # Audit Log
    "AuditLogFilter",
    "AuditLogExportFilter",
    "AuditLogResponse",
    "AuditLogListResponse",
    # Bulk Operation
    "BulkUserDeactivateRequest",
    "BulkProjectArchiveRequest",
    "UserExportFilter",
    "BulkImportResponse",
    "BulkDeactivateResponse",
    "BulkArchiveResponse",
    # Category (existing)
    "DriverTreeCategoryCreate",
    "DriverTreeCategoryListResponse",
    "DriverTreeCategoryResponse",
    "DriverTreeCategoryUpdate",
    # Data Management
    "CleanupPreviewRequest",
    "CleanupExecuteRequest",
    "CleanupPreviewResponse",
    "CleanupExecuteResponse",
    "OrphanFileCleanupRequest",
    "OrphanFileListResponse",
    "OrphanFileCleanupResponse",
    "RetentionPolicyUpdate",
    "RetentionPolicyResponse",
    # Dummy Chart (existing)
    "AnalysisDummyChartListResponse",
    # Dummy Formula (existing)
    "AnalysisDummyFormulaListResponse",
    # Graph Axis (existing)
    "AnalysisGraphAxisListResponse",
    # Health Check
    "HealthCheckSimpleResponse",
    "HealthCheckDetailedResponse",
    # Issue (existing)
    "AnalysisIssueCreate",
    "AnalysisIssueListResponse",
    "AnalysisIssueResponse",
    "AnalysisIssueUpdate",
    # Notification Template
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "NotificationTemplateListResponse",
    # Project Admin
    "AdminProjectFilter",
    "AdminProjectResponse",
    "AdminProjectListResponse",
    "ProjectStorageListResponse",
    # Role (existing)
    "AllRolesResponse",
    "ProjectRoleListResponse",
    "RoleInfo",
    "SystemRoleListResponse",
    # Session Management
    "SessionFilter",
    "SessionTerminateRequest",
    "SessionResponse",
    "SessionListResponse",
    # Statistics
    "StatisticsOverviewResponse",
    "UserStatisticsDetailResponse",
    "StorageStatisticsDetailResponse",
    "ApiStatisticsDetailResponse",
    "ErrorStatisticsDetailResponse",
    # Support Tools
    "ImpersonateRequest",
    "ImpersonateResponse",
    "ImpersonateEndResponse",
    "DebugModeResponse",
    # System Alert
    "SystemAlertCreate",
    "SystemAlertUpdate",
    "SystemAlertResponse",
    "SystemAlertListResponse",
    # System Setting
    "SystemSettingUpdate",
    "SystemSettingsByCategoryResponse",
    "MaintenanceModeEnable",
    "MaintenanceModeResponse",
    # Validation (existing)
    "AnalysisValidationCreate",
    "AnalysisValidationListResponse",
    "AnalysisValidationResponse",
    "AnalysisValidationUpdate",
]
