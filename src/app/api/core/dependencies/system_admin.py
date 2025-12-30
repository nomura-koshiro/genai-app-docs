"""システム管理サービス依存性。

システム管理機能（SA-001〜SA-043）のサービスDI定義を提供します。

サービス:
    - ActivityTrackingService: 操作履歴追跡
    - AuditLogService: 監査ログ
    - SystemSettingService: システム設定
    - StatisticsService: 統計情報
    - NotificationService: 通知管理
    - SessionManagementService: セッション管理
    - BulkOperationService: 一括操作
    - DataManagementService: データ管理
    - SupportToolsService: サポートツール
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.auth import CurrentUserAccountDep
from app.api.core.dependencies.database import DatabaseDep
from app.core.exceptions import AuthorizationError
from app.models.user_account import SystemRole
from app.services.admin import (
    ActivityTrackingService,
    AuditLogService,
    BulkOperationService,
    DataManagementService,
    NotificationService,
    SessionManagementService,
    StatisticsService,
    SupportToolsService,
    SystemSettingService,
)

__all__ = [
    # サービス依存性
    "ActivityTrackingServiceDep",
    "AuditLogServiceDep",
    "BulkOperationServiceDep",
    "DataManagementServiceDep",
    "NotificationServiceDep",
    "SessionManagementServiceDep",
    "StatisticsServiceDep",
    "SupportToolsServiceDep",
    "SystemSettingServiceDep",
    # ファクトリ関数
    "get_activity_tracking_service",
    "get_audit_log_service",
    "get_bulk_operation_service",
    "get_data_management_service",
    "get_notification_service",
    "get_session_management_service",
    "get_statistics_service",
    "get_support_tools_service",
    "get_system_setting_service",
    # 権限チェック
    "RequireSystemAdminDep",
    "require_system_admin",
]


# ================================================================================
# 権限チェック依存性
# ================================================================================


async def require_system_admin(
    current_user: CurrentUserAccountDep,
) -> None:
    """システム管理者権限を要求する依存関係。

    Args:
        current_user: 現在のユーザー

    Raises:
        AuthorizationError: システム管理者権限がない場合
    """
    if current_user.system_role != SystemRole.ADMIN:
        raise AuthorizationError(
            "システム管理者権限が必要です",
            details={
                "required_role": "ADMIN",
                "current_role": current_user.system_role.value if current_user.system_role else "NONE",
            },
        )


RequireSystemAdminDep = Annotated[None, Depends(require_system_admin)]
"""システム管理者権限必須の依存性型。"""


# ================================================================================
# サービス依存性
# ================================================================================


def get_activity_tracking_service(db: DatabaseDep) -> ActivityTrackingService:
    """操作履歴追跡サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        ActivityTrackingService: 初期化された操作履歴追跡サービスインスタンス
    """
    return ActivityTrackingService(db)


ActivityTrackingServiceDep = Annotated[
    ActivityTrackingService, Depends(get_activity_tracking_service)
]
"""操作履歴追跡サービスの依存性型。"""


def get_audit_log_service(db: DatabaseDep) -> AuditLogService:
    """監査ログサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        AuditLogService: 初期化された監査ログサービスインスタンス
    """
    return AuditLogService(db)


AuditLogServiceDep = Annotated[AuditLogService, Depends(get_audit_log_service)]
"""監査ログサービスの依存性型。"""


def get_system_setting_service(db: DatabaseDep) -> SystemSettingService:
    """システム設定サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        SystemSettingService: 初期化されたシステム設定サービスインスタンス
    """
    return SystemSettingService(db)


SystemSettingServiceDep = Annotated[SystemSettingService, Depends(get_system_setting_service)]
"""システム設定サービスの依存性型。"""


def get_statistics_service(db: DatabaseDep) -> StatisticsService:
    """統計情報サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        StatisticsService: 初期化された統計情報サービスインスタンス
    """
    return StatisticsService(db)


StatisticsServiceDep = Annotated[StatisticsService, Depends(get_statistics_service)]
"""統計情報サービスの依存性型。"""


def get_notification_service(db: DatabaseDep) -> NotificationService:
    """通知管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        NotificationService: 初期化された通知管理サービスインスタンス
    """
    return NotificationService(db)


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
"""通知管理サービスの依存性型。"""


def get_session_management_service(db: DatabaseDep) -> SessionManagementService:
    """セッション管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        SessionManagementService: 初期化されたセッション管理サービスインスタンス
    """
    return SessionManagementService(db)


SessionManagementServiceDep = Annotated[
    SessionManagementService, Depends(get_session_management_service)
]
"""セッション管理サービスの依存性型。"""


def get_bulk_operation_service(db: DatabaseDep) -> BulkOperationService:
    """一括操作サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        BulkOperationService: 初期化された一括操作サービスインスタンス
    """
    return BulkOperationService(db)


BulkOperationServiceDep = Annotated[BulkOperationService, Depends(get_bulk_operation_service)]
"""一括操作サービスの依存性型。"""


def get_data_management_service(db: DatabaseDep) -> DataManagementService:
    """データ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        DataManagementService: 初期化されたデータ管理サービスインスタンス
    """
    return DataManagementService(db)


DataManagementServiceDep = Annotated[DataManagementService, Depends(get_data_management_service)]
"""データ管理サービスの依存性型。"""


def get_support_tools_service(db: DatabaseDep) -> SupportToolsService:
    """サポートツールサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        SupportToolsService: 初期化されたサポートツールサービスインスタンス
    """
    return SupportToolsService(db)


SupportToolsServiceDep = Annotated[SupportToolsService, Depends(get_support_tools_service)]
"""サポートツールサービスの依存性型。"""
