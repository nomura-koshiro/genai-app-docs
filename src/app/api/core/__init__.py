"""API層のコア機能。

依存性注入、例外ハンドリングなど、FastAPI層の基盤機能を提供します。

主な機能:
    1. **依存性注入**: データベース、サービス、認証ユーザーの注入
    2. **例外ハンドリング**: グローバル例外ハンドラーの登録

使用例:
    >>> from app.api.core import CurrentUserAccountDep, DatabaseDep
    >>> from app.api.core import register_exception_handlers
    >>>
    >>> @router.get("/profile")
    >>> async def get_profile(
    ...     current_user: CurrentUserAccountDep,
    ...     db: DatabaseDep,
    ... ):
    ...     return {"email": current_user.email}
"""

# 依存性注入
from app.api.core.dependencies import (
    # Admin管理サービス
    AdminCategoryServiceDep,
    AdminDummyChartServiceDep,
    AdminDummyFormulaServiceDep,
    AdminGraphAxisServiceDep,
    AdminIssueServiceDep,
    AdminValidationServiceDep,
    # システム管理サービス
    ActivityTrackingServiceDep,
    AuditLogServiceDep,
    BulkOperationServiceDep,
    DataManagementServiceDep,
    NotificationServiceDep,
    RequireSystemAdminDep,
    SessionManagementServiceDep,
    StatisticsServiceDep,
    SupportToolsServiceDep,
    SystemSettingServiceDep,
    # 分析サービス
    AnalysisSessionServiceDep,
    AnalysisTemplateServiceDep,
    CurrentUserAccountDep,
    CurrentUserAccountOptionalDep,
    DatabaseDep,
    # ドライバーツリーサービス
    DriverTreeFileServiceDep,
    DriverTreeNodeServiceDep,
    DriverTreeServiceDep,
    ProjectFileServiceDep,
    # 認可依存性（プロジェクトメンバーシップ・ロールチェック）
    ProjectManagerDep,
    ProjectMemberDep,
    ProjectMemberServiceDep,
    ProjectModeratorDep,
    ProjectServiceDep,
    # ロール履歴サービス
    RoleHistoryServiceDep,
    SuperuserAccountDep,
    UserServiceDep,
    get_activity_tracking_service,
    get_admin_category_service,
    get_admin_dummy_chart_service,
    get_admin_dummy_formula_service,
    get_admin_graph_axis_service,
    get_admin_issue_service,
    get_admin_validation_service,
    get_analysis_session_service,
    get_analysis_template_service,
    get_audit_log_service,
    get_bulk_operation_service,
    get_current_active_user_account,
    get_current_superuser_account,
    get_current_user_account_optional,
    get_data_management_service,
    get_db,
    get_driver_tree_file_service,
    get_driver_tree_node_service,
    get_driver_tree_service,
    get_notification_service,
    get_project_file_service,
    get_project_manager,
    get_project_member,
    get_project_member_service,
    get_project_moderator,
    get_project_service,
    get_role_history_service,
    get_session_management_service,
    get_statistics_service,
    get_support_tools_service,
    get_system_setting_service,
    get_user_service,
    require_system_admin,
)

# 例外ハンドラー
from app.api.core.exception_handlers import register_exception_handlers

__all__ = [
    # Database Dependencies
    "DatabaseDep",
    "get_db",
    # Admin Service Dependencies
    "AdminCategoryServiceDep",
    "get_admin_category_service",
    "AdminDummyChartServiceDep",
    "get_admin_dummy_chart_service",
    "AdminDummyFormulaServiceDep",
    "get_admin_dummy_formula_service",
    "AdminGraphAxisServiceDep",
    "get_admin_graph_axis_service",
    "AdminIssueServiceDep",
    "get_admin_issue_service",
    "AdminValidationServiceDep",
    "get_admin_validation_service",
    # System Admin Service Dependencies
    "ActivityTrackingServiceDep",
    "get_activity_tracking_service",
    "AuditLogServiceDep",
    "get_audit_log_service",
    "BulkOperationServiceDep",
    "get_bulk_operation_service",
    "DataManagementServiceDep",
    "get_data_management_service",
    "NotificationServiceDep",
    "get_notification_service",
    "RequireSystemAdminDep",
    "require_system_admin",
    "SessionManagementServiceDep",
    "get_session_management_service",
    "StatisticsServiceDep",
    "get_statistics_service",
    "SupportToolsServiceDep",
    "get_support_tools_service",
    "SystemSettingServiceDep",
    "get_system_setting_service",
    # UserAccount Service Dependencies
    "UserServiceDep",
    "get_user_service",
    "RoleHistoryServiceDep",
    "get_role_history_service",
    # Project Service Dependencies
    "ProjectServiceDep",
    "get_project_service",
    "ProjectFileServiceDep",
    "get_project_file_service",
    "ProjectMemberServiceDep",
    "get_project_member_service",
    # Analysis Service Dependencies
    "AnalysisTemplateServiceDep",
    "get_analysis_template_service",
    "AnalysisSessionServiceDep",
    "get_analysis_session_service",
    # Driver Tree Service Dependencies
    "DriverTreeFileServiceDep",
    "get_driver_tree_file_service",
    "DriverTreeServiceDep",
    "get_driver_tree_service",
    "DriverTreeNodeServiceDep",
    "get_driver_tree_node_service",
    # Authentication Dependencies
    "CurrentUserAccountDep",
    "get_current_active_user_account",
    "SuperuserAccountDep",
    "get_current_superuser_account",
    "CurrentUserAccountOptionalDep",
    "get_current_user_account_optional",
    # Authorization Dependencies (Project Membership/Role Check)
    "ProjectMemberDep",
    "get_project_member",
    "ProjectManagerDep",
    "get_project_manager",
    "ProjectModeratorDep",
    "get_project_moderator",
    # Exception Handlers
    "register_exception_handlers",
]
