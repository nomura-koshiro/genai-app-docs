"""FastAPI依存性注入（Dependency Injection）システムの定義。

このパッケージは、FastAPIのDepends機能を使用した依存性注入を提供します。
データベースセッション、各種サービス、認証ユーザーなどの依存性を
エンドポイント関数に注入するための関数とアノテーションを定義しています。

依存性の種類:
    1. データベース依存性:
       - DatabaseDep: 非同期データベースセッション

    2. サービス依存性:
       - UserServiceDep: ユーザーサービス
       - ProjectServiceDep: プロジェクトサービス
       - ProjectFileServiceDep: プロジェクトファイルサービス
       - ProjectMemberServiceDep: プロジェクトメンバーサービス
       - AnalysisTemplateServiceDep: 分析テンプレートサービス
       - AnalysisSessionServiceDep: 分析セッションサービス
       - DriverTreeFileServiceDep: ドライバーツリーファイルサービス
       - DriverTreeServiceDep: ドライバーツリーサービス
       - DriverTreeNodeServiceDep: ドライバーツリーノードサービス
       - AdminCategoryServiceDep: カテゴリ管理サービス
       - AdminValidationServiceDep: 検証マスタ管理サービス
       - AdminIssueServiceDep: 課題マスタ管理サービス

    3. 認証依存性:
       - CurrentUserAccountDep: 認証済みアクティブユーザー（必須）
       - SuperuserAccountDep: スーパーユーザー（必須）
       - CurrentUserAccountOptionalDep: 認証ユーザー（オプション）

使用例:
    >>> from fastapi import APIRouter
    >>> from app.api.core import CurrentUserAccountDep, UserServiceDep
    >>>
    >>> @router.get("/profile")
    >>> async def get_profile(
    ...     current_user: CurrentUserAccountDep,
    ...     user_service: UserServiceDep,
    ... ):
    ...     return {"email": current_user.email}
"""

# 共通サービス依存性
from app.api.core.dependencies.common import (
    UserContextServiceDep,
    get_user_context_service,
)

# 通知サービス依存性
from app.api.core.dependencies.notification import (
    UserNotificationServiceDep,
    get_user_notification_service,
)

# 検索サービス依存性
from app.api.core.dependencies.search import (
    GlobalSearchServiceDep,
    get_global_search_service,
)

# Admin管理サービス依存性
from app.api.core.dependencies.admin import (
    AdminCategoryServiceDep,
    AdminDummyChartServiceDep,
    AdminDummyFormulaServiceDep,
    AdminGraphAxisServiceDep,
    AdminIssueServiceDep,
    AdminValidationServiceDep,
    get_admin_category_service,
    get_admin_dummy_chart_service,
    get_admin_dummy_formula_service,
    get_admin_graph_axis_service,
    get_admin_issue_service,
    get_admin_validation_service,
)

# システム管理サービス依存性
from app.api.core.dependencies.system_admin import (
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
    get_activity_tracking_service,
    get_audit_log_service,
    get_bulk_operation_service,
    get_data_management_service,
    get_notification_service,
    get_session_management_service,
    get_statistics_service,
    get_support_tools_service,
    get_system_setting_service,
    require_system_admin,
)

# データベース依存性
# 分析サービス依存性
from app.api.core.dependencies.analysis import (
    AnalysisSessionServiceDep,
    AnalysisTemplateServiceDep,
    get_analysis_session_service,
    get_analysis_template_service,
)

# 認証依存性
from app.api.core.dependencies.auth import (
    AuthUserType,
    CurrentUserAccountDep,
    CurrentUserAccountOptionalDep,
    SuperuserAccountDep,
    get_current_active_user_account,
    get_current_superuser_account,
    get_current_user_account,
    get_current_user_account_optional,
    verify_active_user,
)

# 認可依存性（プロジェクトメンバーシップ・ロールチェック）
from app.api.core.dependencies.authorization import (
    ProjectManagerDep,
    ProjectMemberDep,
    ProjectModeratorDep,
    get_project_manager,
    get_project_member,
    get_project_moderator,
)
from app.api.core.dependencies.database import (
    DatabaseDep,
    get_db,
)

# ドライバーツリーサービス依存性
from app.api.core.dependencies.driver_tree import (
    DriverTreeFileServiceDep,
    DriverTreeNodeServiceDep,
    DriverTreeServiceDep,
    get_driver_tree_file_service,
    get_driver_tree_node_service,
    get_driver_tree_service,
)

# Projectサービス依存性
from app.api.core.dependencies.project import (
    ProjectFileServiceDep,
    ProjectMemberServiceDep,
    ProjectServiceDep,
    get_project_file_service,
    get_project_member_service,
    get_project_service,
)

# UserAccountサービス依存性
from app.api.core.dependencies.user_account import (
    RoleHistoryServiceDep,
    UserServiceDep,
    UserSettingsServiceDep,
    get_role_history_service,
    get_user_service,
    get_user_settings_service,
)

__all__ = [
    # 型エイリアス
    "AuthUserType",
    # データベース依存性
    "DatabaseDep",
    "get_db",
    # 共通サービス依存性
    "UserContextServiceDep",
    "get_user_context_service",
    # 通知サービス依存性
    "UserNotificationServiceDep",
    "get_user_notification_service",
    # 検索サービス依存性
    "GlobalSearchServiceDep",
    "get_global_search_service",
    # Admin管理サービス依存性
    "AdminCategoryServiceDep",
    "AdminDummyChartServiceDep",
    "AdminDummyFormulaServiceDep",
    "AdminGraphAxisServiceDep",
    "AdminIssueServiceDep",
    "AdminValidationServiceDep",
    "get_admin_category_service",
    "get_admin_dummy_chart_service",
    "get_admin_dummy_formula_service",
    "get_admin_graph_axis_service",
    "get_admin_issue_service",
    "get_admin_validation_service",
    # システム管理サービス依存性
    "ActivityTrackingServiceDep",
    "AuditLogServiceDep",
    "BulkOperationServiceDep",
    "DataManagementServiceDep",
    "NotificationServiceDep",
    "RequireSystemAdminDep",
    "SessionManagementServiceDep",
    "StatisticsServiceDep",
    "SupportToolsServiceDep",
    "SystemSettingServiceDep",
    "get_activity_tracking_service",
    "get_audit_log_service",
    "get_bulk_operation_service",
    "get_data_management_service",
    "get_notification_service",
    "get_session_management_service",
    "get_statistics_service",
    "get_support_tools_service",
    "get_system_setting_service",
    "require_system_admin",
    # UserAccountサービス依存性
    "UserServiceDep",
    "RoleHistoryServiceDep",
    "UserSettingsServiceDep",
    "get_user_service",
    "get_role_history_service",
    "get_user_settings_service",
    # Projectサービス依存性
    "ProjectServiceDep",
    "ProjectFileServiceDep",
    "ProjectMemberServiceDep",
    "get_project_service",
    "get_project_file_service",
    "get_project_member_service",
    # 分析サービス依存性
    "AnalysisTemplateServiceDep",
    "AnalysisSessionServiceDep",
    "get_analysis_template_service",
    "get_analysis_session_service",
    # ドライバーツリーサービス依存性
    "DriverTreeFileServiceDep",
    "DriverTreeServiceDep",
    "DriverTreeNodeServiceDep",
    "get_driver_tree_file_service",
    "get_driver_tree_service",
    "get_driver_tree_node_service",
    # 認証依存性
    "CurrentUserAccountDep",
    "SuperuserAccountDep",
    "CurrentUserAccountOptionalDep",
    "get_current_user_account",
    "get_current_active_user_account",
    "get_current_superuser_account",
    "get_current_user_account_optional",
    # 認可依存性（プロジェクトメンバーシップ・ロールチェック）
    "ProjectMemberDep",
    "ProjectManagerDep",
    "ProjectModeratorDep",
    "get_project_member",
    "get_project_manager",
    "get_project_moderator",
    # ヘルパー関数
    "verify_active_user",
]
