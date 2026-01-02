"""データ管理APIエンドポイント。

データクリーンアップ・保持ポリシー管理APIを提供します。

主な機能:
    - 削除プレビュー（GET /api/v1/admin/data/cleanup/preview）
    - データ一括削除（POST /api/v1/admin/data/cleanup/execute）
    - 保持ポリシー取得（GET /api/v1/admin/data/retention-policy）
    - 保持ポリシー更新（PATCH /api/v1/admin/data/retention-policy）

セキュリティ:
    - システム管理者権限必須
"""

from fastapi import APIRouter, Query, status

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    DataManagementServiceDep,
    RequireSystemAdminDep,
)
from app.core.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.data_management import (
    CleanupExecuteResponse,
    CleanupPreviewResponse,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
)

logger = get_logger(__name__)

data_management_router = APIRouter(prefix="/data", tags=["Data Management"])


@data_management_router.get(
    "/cleanup/preview",
    response_model=CleanupPreviewResponse,
    summary="削除対象データプレビュー",
    description="""
    削除対象データのプレビューを取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - target_types: 対象種別（ACTIVITY_LOGS/AUDIT_LOGS/SESSION_LOGS）
        - retention_days: 保持日数
    """,
)
@handle_service_errors
async def preview_cleanup(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
    target_types: list[str] = Query(..., description="対象種別"),
    retention_days: int = Query(..., ge=1, description="保持日数"),
) -> CleanupPreviewResponse:
    """削除対象データをプレビューします。"""
    logger.info(
        "削除対象データプレビュー",
        user_id=str(current_user.id),
        target_types=target_types,
        retention_days=retention_days,
        action="preview_cleanup",
    )

    result = await service.preview_cleanup(
        target_types=target_types,
        retention_days=retention_days,
    )

    return result


@data_management_router.post(
    "/cleanup/execute",
    response_model=CleanupExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="データ一括削除",
    description="""
    古いデータを一括削除します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def execute_cleanup(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
    target_types: list[str] = Query(..., description="対象種別"),
    retention_days: int = Query(..., ge=1, description="保持日数"),
) -> CleanupExecuteResponse:
    """データを一括削除します。"""
    logger.info(
        "データ一括削除",
        user_id=str(current_user.id),
        target_types=target_types,
        retention_days=retention_days,
        action="execute_cleanup",
    )

    result = await service.execute_cleanup(
        target_types=target_types,
        retention_days=retention_days,
        performed_by=current_user.id,
    )

    return result


@data_management_router.get(
    "/retention-policy",
    response_model=RetentionPolicyResponse,
    summary="保持ポリシー取得",
    description="""
    データ保持ポリシーを取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_retention_policy(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> RetentionPolicyResponse:
    """保持ポリシーを取得します。"""
    logger.info(
        "保持ポリシー取得",
        user_id=str(current_user.id),
        action="get_retention_policy",
    )

    result = await service.get_retention_policy()

    return result


@data_management_router.patch(
    "/retention-policy",
    response_model=RetentionPolicyResponse,
    summary="保持ポリシー更新",
    description="""
    データ保持ポリシーを更新します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def update_retention_policy(
    request: RetentionPolicyUpdate,
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> RetentionPolicyResponse:
    """保持ポリシーを更新します。"""
    logger.info(
        "保持ポリシー更新",
        user_id=str(current_user.id),
        action="update_retention_policy",
    )

    result = await service.update_retention_policy(
        policy=request,
        updated_by=current_user.id,
    )

    return result
