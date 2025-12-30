"""操作履歴サービス。

このモジュールは、ユーザー操作履歴の記録・検索機能を提供します。
"""

import csv
import io
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.repositories.admin.user_activity_repository import UserActivityRepository
from app.schemas.admin.activity_log import (
    ActivityLogDetailResponse,
    ActivityLogFilter,
    ActivityLogListResponse,
    ActivityLogResponse,
)

logger = get_logger(__name__)


class ActivityTrackingService:
    """操作履歴サービス。

    ユーザー操作履歴の記録・検索・エクスポート機能を提供します。

    メソッド:
        - record_activity: 操作履歴を記録
        - list_activities: 操作履歴一覧を取得
        - get_activity_detail: 操作履歴詳細を取得
        - list_errors: エラー履歴を取得
        - export_to_csv: CSV形式でエクスポート
        - get_statistics: 統計情報を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = UserActivityRepository(db)

    async def record_activity(
        self,
        *,
        user_id: uuid.UUID | None,
        action_type: str,
        resource_type: str | None,
        resource_id: uuid.UUID | None,
        endpoint: str,
        method: str,
        request_body: dict | None,
        response_status: int,
        error_message: str | None,
        error_code: str | None,
        ip_address: str | None,
        user_agent: str | None,
        duration_ms: int,
    ) -> None:
        """操作履歴を記録します。

        このメソッドはミドルウェアから呼び出され、非同期で記録します。

        Args:
            user_id: ユーザーID
            action_type: 操作種別
            resource_type: リソース種別
            resource_id: リソースID
            endpoint: エンドポイント
            method: HTTPメソッド
            request_body: リクエストボディ（マスク済み）
            response_status: レスポンスステータス
            error_message: エラーメッセージ
            error_code: エラーコード
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            duration_ms: 処理時間
        """
        try:
            await self.repository.create(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=endpoint,
                method=method,
                request_body=request_body,
                response_status=response_status,
                error_message=error_message,
                error_code=error_code,
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms,
            )
            await self.db.commit()
        except Exception as e:
            logger.error(
                "操作履歴の記録に失敗しました",
                endpoint=endpoint,
                error=str(e),
                action="record_activity_error",
            )
            # エラーが発生してもリクエスト処理は継続

    @measure_performance
    async def list_activities(
        self,
        filter_params: ActivityLogFilter,
    ) -> ActivityLogListResponse:
        """操作履歴一覧を取得します。

        Args:
            filter_params: フィルタパラメータ

        Returns:
            ActivityLogListResponse: 操作履歴一覧
        """
        logger.info(
            "操作履歴一覧を取得中",
            filters=filter_params.model_dump(exclude_unset=True),
            action="list_activities",
        )

        activities = await self.repository.list_with_filters(
            user_id=filter_params.user_id,
            action_type=filter_params.action_type,
            resource_type=filter_params.resource_type,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            has_error=filter_params.has_error,
            skip=(filter_params.page - 1) * filter_params.limit,
            limit=filter_params.limit,
        )

        total = await self.repository.count_with_filters(
            user_id=filter_params.user_id,
            action_type=filter_params.action_type,
            resource_type=filter_params.resource_type,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            has_error=filter_params.has_error,
        )

        total_pages = (total + filter_params.limit - 1) // filter_params.limit

        items = [
            ActivityLogResponse(
                id=a.id,
                user_id=a.user_id,
                user_name=a.user.display_name if a.user else None,
                action_type=a.action_type,
                resource_type=a.resource_type,
                resource_id=a.resource_id,
                endpoint=a.endpoint,
                method=a.method,
                response_status=a.response_status,
                error_message=a.error_message,
                error_code=a.error_code,
                ip_address=a.ip_address,
                user_agent=a.user_agent,
                duration_ms=a.duration_ms,
                created_at=a.created_at,
            )
            for a in activities
        ]

        logger.info(
            "操作履歴一覧を取得しました",
            count=len(items),
            total=total,
        )

        return ActivityLogListResponse(
            items=items,
            total=total,
            page=filter_params.page,
            limit=filter_params.limit,
            total_pages=total_pages,
        )

    @measure_performance
    async def get_activity_detail(
        self,
        activity_id: uuid.UUID,
    ) -> ActivityLogDetailResponse | None:
        """操作履歴詳細を取得します。

        Args:
            activity_id: 操作履歴ID

        Returns:
            ActivityLogDetailResponse | None: 操作履歴詳細
        """
        logger.info(
            "操作履歴詳細を取得中",
            activity_id=str(activity_id),
            action="get_activity_detail",
        )

        activity = await self.repository.get_with_user(activity_id)
        if activity is None:
            return None

        return ActivityLogDetailResponse(
            id=activity.id,
            user_id=activity.user_id,
            user_name=activity.user.display_name if activity.user else None,
            user_email=activity.user.email if activity.user else None,
            action_type=activity.action_type,
            resource_type=activity.resource_type,
            resource_id=activity.resource_id,
            endpoint=activity.endpoint,
            method=activity.method,
            request_body=activity.request_body,
            response_status=activity.response_status,
            error_message=activity.error_message,
            error_code=activity.error_code,
            ip_address=activity.ip_address,
            user_agent=activity.user_agent,
            duration_ms=activity.duration_ms,
            created_at=activity.created_at,
        )

    @measure_performance
    async def export_to_csv(
        self,
        filter_params: ActivityLogFilter,
    ) -> str:
        """操作履歴をCSV形式でエクスポートします。

        Args:
            filter_params: フィルタパラメータ

        Returns:
            str: CSV文字列
        """
        logger.info(
            "操作履歴をエクスポート中",
            filters=filter_params.model_dump(exclude_unset=True),
            action="export_activities",
        )

        # エクスポート用に大量データを取得
        activities = await self.repository.list_with_filters(
            user_id=filter_params.user_id,
            action_type=filter_params.action_type,
            resource_type=filter_params.resource_type,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            has_error=filter_params.has_error,
            skip=0,
            limit=10000,  # エクスポート上限
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow([
            "ID",
            "日時",
            "ユーザーID",
            "ユーザー名",
            "操作種別",
            "リソース種別",
            "リソースID",
            "エンドポイント",
            "メソッド",
            "ステータス",
            "エラーメッセージ",
            "処理時間(ms)",
            "IPアドレス",
        ])

        # データ行
        for a in activities:
            writer.writerow([
                str(a.id),
                a.created_at.isoformat(),
                str(a.user_id) if a.user_id else "",
                a.user.display_name if a.user else "",
                a.action_type,
                a.resource_type or "",
                str(a.resource_id) if a.resource_id else "",
                a.endpoint,
                a.method,
                a.response_status,
                a.error_message or "",
                a.duration_ms,
                a.ip_address or "",
            ])

        logger.info(
            "操作履歴をエクスポートしました",
            count=len(activities),
        )

        return output.getvalue()

    @measure_performance
    async def get_statistics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """統計情報を取得します。

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            dict: 統計情報
        """
        return await self.repository.get_statistics(
            start_date=start_date,
            end_date=end_date,
        )
