"""管理機能のリポジトリ。"""

from app.repositories.admin.announcement_repository import AnnouncementRepository
from app.repositories.admin.audit_log_repository import AuditLogRepository
from app.repositories.admin.category import DriverTreeCategoryRepository
from app.repositories.admin.dummy_chart import AnalysisDummyChartRepository
from app.repositories.admin.dummy_formula import AnalysisDummyFormulaRepository
from app.repositories.admin.graph_axis import AnalysisGraphAxisRepository
from app.repositories.admin.issue import AnalysisIssueRepository
from app.repositories.admin.notification_template_repository import (
    NotificationTemplateRepository,
)
from app.repositories.admin.system_alert_repository import SystemAlertRepository
from app.repositories.admin.system_setting_repository import SystemSettingRepository
from app.repositories.admin.user_activity_repository import UserActivityRepository
from app.repositories.admin.user_session_repository import UserSessionRepository
from app.repositories.admin.validation import AnalysisValidationRepository

__all__ = [
    # 既存リポジトリ
    "AnalysisDummyChartRepository",
    "AnalysisDummyFormulaRepository",
    "AnalysisGraphAxisRepository",
    "DriverTreeCategoryRepository",
    "AnalysisIssueRepository",
    "AnalysisValidationRepository",
    # システム管理リポジトリ
    "UserActivityRepository",
    "AuditLogRepository",
    "SystemSettingRepository",
    "AnnouncementRepository",
    "NotificationTemplateRepository",
    "SystemAlertRepository",
    "UserSessionRepository",
]
