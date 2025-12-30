# システム管理機能 詳細設計書 - サービス層

## 1. 概要

本ドキュメントでは、システム管理機能（SA-001〜SA-043）で追加するサービスの詳細設計を定義する。

### 1.1 既存パターンへの準拠

既存のサービス実装パターンに従い、以下の規約を適用する：

- 機能ごとにサービスクラスを分離
- `@measure_performance` デコレータでパフォーマンス計測
- `@transactional` デコレータでトランザクション管理
- ロギングは構造化ログ（action, entity_id等のメタデータ）
- 例外は `NotFoundError`, `AuthorizationError`, `ValidationError` を使用

### 1.2 ファイル構成

```
src/app/services/admin/
├── __init__.py
├── activity_tracking_service.py   # 操作履歴記録・検索
├── audit_log_service.py           # 監査ログ管理
├── system_setting_service.py      # システム設定管理
├── statistics_service.py          # 統計情報集計
├── notification_service.py        # 通知・お知らせ管理
├── session_management_service.py  # セッション管理
├── bulk_operation_service.py      # 一括操作実行
├── data_management_service.py     # データクリーンアップ
└── support_tools_service.py       # サポートツール
```

---

## 2. サービス詳細設計

### 2.1 ActivityTrackingService（操作履歴サービス）

**ファイル**: `src/app/services/admin/activity_tracking_service.py`

**対応ユースケース**: SA-001〜SA-006

```python
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
```

---

### 2.2 AuditLogService（監査ログサービス）

**ファイル**: `src/app/services/admin/audit_log_service.py`

**対応ユースケース**: SA-012〜SA-016

```python
"""監査ログサービス。

このモジュールは、監査ログの記録・検索機能を提供します。
"""

import csv
import io
import json
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.models.audit.audit_log import AuditEventType, AuditSeverity
from app.repositories.admin.audit_log_repository import AuditLogRepository
from app.schemas.admin.audit_log import (
    AuditLogExportFilter,
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogResponse,
)

logger = get_logger(__name__)


class AuditLogService:
    """監査ログサービス。

    監査ログの記録・検索・エクスポート機能を提供します。

    メソッド:
        - record_data_change: データ変更を記録
        - record_access: アクセスを記録
        - record_security_event: セキュリティイベントを記録
        - list_audit_logs: 監査ログ一覧を取得
        - list_by_event_type: イベント種別で取得
        - list_by_resource: リソースで取得
        - export: エクスポート
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.repository = AuditLogRepository(db)

    async def record_data_change(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None,
        old_value: dict | None,
        new_value: dict | None,
        changed_fields: list[str] | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        severity: str = AuditSeverity.INFO.value,
        metadata: dict | None = None,
    ) -> None:
        """データ変更を記録します。

        Args:
            user_id: ユーザーID
            action: アクション（CREATE/UPDATE/DELETE）
            resource_type: リソース種別
            resource_id: リソースID
            old_value: 変更前の値
            new_value: 変更後の値
            changed_fields: 変更フィールド
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            severity: 重要度
            metadata: メタデータ
        """
        try:
            await self.repository.create(
                user_id=user_id,
                event_type=AuditEventType.DATA_CHANGE.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_value=old_value,
                new_value=new_value,
                changed_fields=changed_fields,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                metadata=metadata,
            )
            await self.db.commit()

            logger.info(
                "データ変更を記録しました",
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
            )
        except Exception as e:
            logger.error(
                "データ変更の記録に失敗しました",
                error=str(e),
                resource_type=resource_type,
            )

    async def record_access(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """アクセスを記録します。

        Args:
            user_id: ユーザーID
            action: アクション（LOGIN_SUCCESS/LOGIN_FAILED/LOGOUT等）
            resource_type: リソース種別
            resource_id: リソースID
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            metadata: メタデータ
        """
        try:
            await self.repository.create(
                user_id=user_id,
                event_type=AuditEventType.ACCESS.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=AuditSeverity.INFO.value,
                metadata=metadata,
            )
            await self.db.commit()
        except Exception as e:
            logger.error(
                "アクセス記録に失敗しました",
                error=str(e),
                action=action,
            )

    async def record_security_event(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        severity: str = AuditSeverity.WARNING.value,
        metadata: dict | None = None,
    ) -> None:
        """セキュリティイベントを記録します。

        Args:
            user_id: ユーザーID
            action: アクション
            resource_type: リソース種別
            resource_id: リソースID
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            severity: 重要度
            metadata: メタデータ
        """
        try:
            await self.repository.create(
                user_id=user_id,
                event_type=AuditEventType.SECURITY.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                metadata=metadata,
            )
            await self.db.commit()

            logger.warning(
                "セキュリティイベントを記録しました",
                action=action,
                severity=severity,
                user_id=str(user_id) if user_id else None,
            )
        except Exception as e:
            logger.error(
                "セキュリティイベントの記録に失敗しました",
                error=str(e),
                action=action,
            )

    @measure_performance
    async def list_audit_logs(
        self,
        filter_params: AuditLogFilter,
    ) -> AuditLogListResponse:
        """監査ログ一覧を取得します。

        Args:
            filter_params: フィルタパラメータ

        Returns:
            AuditLogListResponse: 監査ログ一覧
        """
        logger.info(
            "監査ログ一覧を取得中",
            filters=filter_params.model_dump(exclude_unset=True),
            action="list_audit_logs",
        )

        logs = await self.repository.list_with_filters(
            event_type=filter_params.event_type,
            user_id=filter_params.user_id,
            resource_type=filter_params.resource_type,
            resource_id=filter_params.resource_id,
            severity=filter_params.severity,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            skip=(filter_params.page - 1) * filter_params.limit,
            limit=filter_params.limit,
        )

        total = await self.repository.count_with_filters(
            event_type=filter_params.event_type,
            user_id=filter_params.user_id,
            resource_type=filter_params.resource_type,
            resource_id=filter_params.resource_id,
            severity=filter_params.severity,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
        )

        total_pages = (total + filter_params.limit - 1) // filter_params.limit

        items = [self._to_response(log) for log in logs]

        return AuditLogListResponse(
            items=items,
            total=total,
            page=filter_params.page,
            limit=filter_params.limit,
            total_pages=total_pages,
        )

    @measure_performance
    async def list_by_event_type(
        self,
        event_type: str,
        filter_params: AuditLogFilter,
    ) -> AuditLogListResponse:
        """イベント種別で監査ログを取得します。

        Args:
            event_type: イベント種別
            filter_params: フィルタパラメータ

        Returns:
            AuditLogListResponse: 監査ログ一覧
        """
        filter_params.event_type = event_type
        return await self.list_audit_logs(filter_params)

    @measure_performance
    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        filter_params: AuditLogFilter,
    ) -> AuditLogListResponse:
        """リソースで監査ログを取得します。

        Args:
            resource_type: リソース種別
            resource_id: リソースID
            filter_params: フィルタパラメータ

        Returns:
            AuditLogListResponse: 監査ログ一覧
        """
        filter_params.resource_type = resource_type
        filter_params.resource_id = resource_id
        return await self.list_audit_logs(filter_params)

    @measure_performance
    async def export(
        self,
        filter_params: AuditLogExportFilter,
    ) -> str:
        """監査ログをエクスポートします。

        Args:
            filter_params: エクスポートフィルタ

        Returns:
            str: エクスポートデータ（CSV or JSON）
        """
        logger.info(
            "監査ログをエクスポート中",
            format=filter_params.format,
            action="export_audit_logs",
        )

        logs = await self.repository.list_with_filters(
            event_type=filter_params.event_type,
            start_date=filter_params.start_date,
            end_date=filter_params.end_date,
            skip=0,
            limit=10000,
        )

        if filter_params.format == "json":
            return self._export_to_json(logs)
        else:
            return self._export_to_csv(logs)

    def _to_response(self, log) -> AuditLogResponse:
        """モデルをレスポンスに変換します。"""
        return AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.display_name if log.user else None,
            user_email=log.user.email if log.user else None,
            event_type=log.event_type,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_value=log.old_value,
            new_value=log.new_value,
            changed_fields=log.changed_fields,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            severity=log.severity,
            metadata=log.metadata,
            created_at=log.created_at,
        )

    def _export_to_csv(self, logs) -> str:
        """CSV形式でエクスポートします。"""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "ID", "日時", "イベント種別", "アクション", "ユーザーID",
            "ユーザー名", "リソース種別", "リソースID", "重要度",
            "変更フィールド", "IPアドレス",
        ])

        for log in logs:
            writer.writerow([
                str(log.id),
                log.created_at.isoformat(),
                log.event_type,
                log.action,
                str(log.user_id) if log.user_id else "",
                log.user.display_name if log.user else "",
                log.resource_type,
                str(log.resource_id) if log.resource_id else "",
                log.severity,
                ",".join(log.changed_fields) if log.changed_fields else "",
                log.ip_address or "",
            ])

        return output.getvalue()

    def _export_to_json(self, logs) -> str:
        """JSON形式でエクスポートします。"""
        data = [
            {
                "id": str(log.id),
                "created_at": log.created_at.isoformat(),
                "event_type": log.event_type,
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "changed_fields": log.changed_fields,
                "severity": log.severity,
                "ip_address": log.ip_address,
                "metadata": log.metadata,
            }
            for log in logs
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)
```

---

### 2.3 SystemSettingService（システム設定サービス）

**ファイル**: `src/app/services/admin/system_setting_service.py`

**対応ユースケース**: SA-017〜SA-020

```python
"""システム設定サービス。

このモジュールは、システム設定の管理機能を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.admin.system_setting_repository import SystemSettingRepository
from app.schemas.admin.system_setting import (
    MaintenanceModeEnable,
    MaintenanceModeResponse,
    SystemSettingResponse,
    SystemSettingsByCategoryResponse,
)

logger = get_logger(__name__)


class SystemSettingService:
    """システム設定サービス。

    システム設定の取得・更新機能を提供します。

    メソッド:
        - get_all_settings: 全設定を取得
        - get_settings_by_category: カテゴリ別設定を取得
        - update_setting: 設定を更新
        - enable_maintenance_mode: メンテナンスモードを有効化
        - disable_maintenance_mode: メンテナンスモードを無効化
        - get_maintenance_status: メンテナンスモード状態を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.repository = SystemSettingRepository(db)

    @measure_performance
    async def get_all_settings(self) -> SystemSettingsByCategoryResponse:
        """全設定をカテゴリ別に取得します。

        Returns:
            SystemSettingsByCategoryResponse: カテゴリ別設定
        """
        logger.info("全設定を取得中", action="get_all_settings")

        grouped = await self.repository.list_all_grouped()

        categories = {}
        for category, settings in grouped.items():
            categories[category] = [
                SystemSettingResponse(
                    key=s.key,
                    value=s.value if not s.is_secret else "***",
                    value_type=s.value_type,
                    description=s.description,
                    is_editable=s.is_editable,
                )
                for s in settings
            ]

        return SystemSettingsByCategoryResponse(categories=categories)

    @measure_performance
    async def get_settings_by_category(
        self,
        category: str,
    ) -> list[SystemSettingResponse]:
        """カテゴリ別設定を取得します。

        Args:
            category: カテゴリ

        Returns:
            list[SystemSettingResponse]: 設定リスト
        """
        logger.info(
            "カテゴリ別設定を取得中",
            category=category,
            action="get_settings_by_category",
        )

        settings = await self.repository.list_by_category(category)

        return [
            SystemSettingResponse(
                key=s.key,
                value=s.value if not s.is_secret else "***",
                value_type=s.value_type,
                description=s.description,
                is_editable=s.is_editable,
            )
            for s in settings
        ]

    @measure_performance
    @transactional
    async def update_setting(
        self,
        category: str,
        key: str,
        value: any,
        updated_by: uuid.UUID,
    ) -> SystemSettingResponse:
        """設定を更新します。

        Args:
            category: カテゴリ
            key: 設定キー
            value: 新しい値
            updated_by: 更新者ID

        Returns:
            SystemSettingResponse: 更新された設定

        Raises:
            NotFoundError: 設定が見つからない場合
            ValidationError: 編集不可の設定の場合
        """
        logger.info(
            "設定を更新中",
            category=category,
            key=key,
            updated_by=str(updated_by),
            action="update_setting",
        )

        setting = await self.repository.get_by_category_and_key(category, key)
        if setting is None:
            raise NotFoundError(
                "設定が見つかりません",
                details={"category": category, "key": key},
            )

        if not setting.is_editable:
            raise ValidationError(
                "この設定は編集できません",
                details={"category": category, "key": key},
            )

        # 型に応じた値の変換・検証
        validated_value = self._validate_value(value, setting.value_type)

        updated = await self.repository.set_value(
            category=category,
            key=key,
            value=validated_value,
            updated_by=updated_by,
        )

        logger.info(
            "設定を更新しました",
            category=category,
            key=key,
        )

        return SystemSettingResponse(
            key=updated.key,
            value=updated.value if not updated.is_secret else "***",
            value_type=updated.value_type,
            description=updated.description,
            is_editable=updated.is_editable,
        )

    @measure_performance
    @transactional
    async def enable_maintenance_mode(
        self,
        params: MaintenanceModeEnable,
        updated_by: uuid.UUID,
    ) -> MaintenanceModeResponse:
        """メンテナンスモードを有効化します。

        Args:
            params: メンテナンスモードパラメータ
            updated_by: 更新者ID

        Returns:
            MaintenanceModeResponse: メンテナンスモード状態
        """
        logger.info(
            "メンテナンスモードを有効化中",
            updated_by=str(updated_by),
            action="enable_maintenance_mode",
        )

        await self.repository.set_value(
            category="MAINTENANCE",
            key="maintenance_mode",
            value=True,
            updated_by=updated_by,
        )

        await self.repository.set_value(
            category="MAINTENANCE",
            key="maintenance_message",
            value=params.message,
            updated_by=updated_by,
        )

        await self.repository.set_value(
            category="MAINTENANCE",
            key="allow_admin_access",
            value=params.allow_admin_access,
            updated_by=updated_by,
        )

        logger.warning(
            "メンテナンスモードが有効化されました",
            message=params.message,
            updated_by=str(updated_by),
        )

        return MaintenanceModeResponse(
            enabled=True,
            message=params.message,
            allow_admin_access=params.allow_admin_access,
        )

    @measure_performance
    @transactional
    async def disable_maintenance_mode(
        self,
        updated_by: uuid.UUID,
    ) -> MaintenanceModeResponse:
        """メンテナンスモードを無効化します。

        Args:
            updated_by: 更新者ID

        Returns:
            MaintenanceModeResponse: メンテナンスモード状態
        """
        logger.info(
            "メンテナンスモードを無効化中",
            updated_by=str(updated_by),
            action="disable_maintenance_mode",
        )

        await self.repository.set_value(
            category="MAINTENANCE",
            key="maintenance_mode",
            value=False,
            updated_by=updated_by,
        )

        logger.info(
            "メンテナンスモードが無効化されました",
            updated_by=str(updated_by),
        )

        return MaintenanceModeResponse(
            enabled=False,
            message=None,
            allow_admin_access=True,
        )

    @measure_performance
    async def get_maintenance_status(self) -> MaintenanceModeResponse:
        """メンテナンスモード状態を取得します。

        Returns:
            MaintenanceModeResponse: メンテナンスモード状態
        """
        enabled = await self.repository.get_value(
            "MAINTENANCE", "maintenance_mode", default=False
        )
        message = await self.repository.get_value(
            "MAINTENANCE", "maintenance_message", default=None
        )
        allow_admin = await self.repository.get_value(
            "MAINTENANCE", "allow_admin_access", default=True
        )

        return MaintenanceModeResponse(
            enabled=enabled,
            message=message if enabled else None,
            allow_admin_access=allow_admin,
        )

    def _validate_value(self, value: any, value_type: str) -> any:
        """値を検証・変換します。"""
        if value_type == "NUMBER":
            try:
                return float(value) if "." in str(value) else int(value)
            except (ValueError, TypeError):
                raise ValidationError(
                    "数値形式が不正です",
                    details={"value": value},
                )
        elif value_type == "BOOLEAN":
            if isinstance(value, bool):
                return value
            if str(value).lower() in ("true", "1", "yes"):
                return True
            if str(value).lower() in ("false", "0", "no"):
                return False
            raise ValidationError(
                "真偽値形式が不正です",
                details={"value": value},
            )
        elif value_type == "JSON":
            if isinstance(value, (dict, list)):
                return value
            raise ValidationError(
                "JSON形式が不正です",
                details={"value": value},
            )
        else:
            return str(value)
```

---

### 2.4 StatisticsService（統計情報サービス）

**ファイル**: `src/app/services/admin/statistics_service.py`

**対応ユースケース**: SA-022〜SA-026

```python
"""統計情報サービス。

このモジュールは、システム統計情報の集計機能を提供します。
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.models import Project, UserAccount
from app.models.audit.user_activity import UserActivity
from app.repositories import ProjectFileRepository, ProjectRepository, UserAccountRepository
from app.schemas.admin.statistics import (
    ApiStatistics,
    ApiStatisticsDetailResponse,
    ErrorStatisticsDetailResponse,
    ProjectStatistics,
    StatisticsOverviewResponse,
    StorageStatistics,
    StorageStatisticsDetailResponse,
    TimeSeriesDataPoint,
    UserStatistics,
    UserStatisticsDetailResponse,
)

logger = get_logger(__name__)


class StatisticsService:
    """統計情報サービス。

    システム統計情報の集計機能を提供します。

    メソッド:
        - get_overview: 統計概要を取得
        - get_user_statistics: ユーザー統計を取得
        - get_storage_statistics: ストレージ統計を取得
        - get_api_statistics: API統計を取得
        - get_error_statistics: エラー統計を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.user_repo = UserAccountRepository(db)
        self.project_repo = ProjectRepository(db)
        self.file_repo = ProjectFileRepository(db)

    @measure_performance
    async def get_overview(
        self,
        period: str = "day",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> StatisticsOverviewResponse:
        """統計概要を取得します。

        Args:
            period: 期間（day/week/month/year）
            start_date: 開始日
            end_date: 終了日

        Returns:
            StatisticsOverviewResponse: 統計概要
        """
        logger.info(
            "統計概要を取得中",
            period=period,
            action="get_statistics_overview",
        )

        # ユーザー統計
        users = await self._get_user_summary()

        # プロジェクト統計
        projects = await self._get_project_summary()

        # ストレージ統計
        storage = await self._get_storage_summary()

        # API統計
        api = await self._get_api_summary()

        return StatisticsOverviewResponse(
            users=users,
            projects=projects,
            storage=storage,
            api=api,
        )

    async def _get_user_summary(self) -> UserStatistics:
        """ユーザー統計サマリーを取得します。"""
        total = await self.user_repo.count()

        # 今日アクティブなユーザー数
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        active_query = (
            select(func.count(func.distinct(UserActivity.user_id)))
            .where(UserActivity.created_at >= today_start)
        )
        result = await self.db.execute(active_query)
        active_today = result.scalar_one() or 0

        # 今月の新規ユーザー数
        month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_query = (
            select(func.count())
            .select_from(UserAccount)
            .where(UserAccount.created_at >= month_start)
        )
        result = await self.db.execute(new_query)
        new_this_month = result.scalar_one() or 0

        return UserStatistics(
            total=total,
            active_today=active_today,
            new_this_month=new_this_month,
        )

    async def _get_project_summary(self) -> ProjectStatistics:
        """プロジェクト統計サマリーを取得します。"""
        total = await self.project_repo.count()

        active_query = (
            select(func.count())
            .select_from(Project)
            .where(Project.is_active == True)
        )
        result = await self.db.execute(active_query)
        active = result.scalar_one() or 0

        month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        created_query = (
            select(func.count())
            .select_from(Project)
            .where(Project.created_at >= month_start)
        )
        result = await self.db.execute(created_query)
        created_this_month = result.scalar_one() or 0

        return ProjectStatistics(
            total=total,
            active=active,
            created_this_month=created_this_month,
        )

    async def _get_storage_summary(self) -> StorageStatistics:
        """ストレージ統計サマリーを取得します。"""
        # TODO: 実際のストレージ使用量を計算
        # ここではプレースホルダー値を返す
        total_bytes = 0
        used_percentage = 0.0

        return StorageStatistics(
            total_bytes=total_bytes,
            total_display=self._format_bytes(total_bytes),
            used_percentage=used_percentage,
        )

    async def _get_api_summary(self) -> ApiStatistics:
        """API統計サマリーを取得します。"""
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # 今日のリクエスト数
        request_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(UserActivity.created_at >= today_start)
        )
        result = await self.db.execute(request_query)
        requests_today = result.scalar_one() or 0

        # 平均レスポンス時間
        avg_query = (
            select(func.avg(UserActivity.duration_ms))
            .where(UserActivity.created_at >= today_start)
        )
        result = await self.db.execute(avg_query)
        average_response_ms = result.scalar_one() or 0

        # エラー率
        error_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(
                UserActivity.created_at >= today_start,
                UserActivity.response_status >= 400,
            )
        )
        result = await self.db.execute(error_query)
        error_count = result.scalar_one() or 0
        error_rate = (error_count / requests_today * 100) if requests_today > 0 else 0

        return ApiStatistics(
            requests_today=requests_today,
            average_response_ms=float(average_response_ms),
            error_rate_percentage=round(error_rate, 2),
        )

    @measure_performance
    async def get_user_statistics(
        self,
        days: int = 30,
    ) -> UserStatisticsDetailResponse:
        """ユーザー統計詳細を取得します。

        Args:
            days: 取得日数

        Returns:
            UserStatisticsDetailResponse: ユーザー統計詳細
        """
        total = await self.user_repo.count()
        active_users = await self._get_active_users_trend(days)
        new_users = await self._get_new_users_trend(days)

        return UserStatisticsDetailResponse(
            total=total,
            active_users=active_users,
            new_users=new_users,
        )

    async def _get_active_users_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """アクティブユーザー推移を取得します。"""
        result = []
        today = date.today()

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=UTC)
            end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=UTC)

            query = (
                select(func.count(func.distinct(UserActivity.user_id)))
                .where(
                    UserActivity.created_at >= start,
                    UserActivity.created_at <= end,
                )
            )
            res = await self.db.execute(query)
            count = res.scalar_one() or 0

            result.append(TimeSeriesDataPoint(date=target_date, value=float(count)))

        return result

    async def _get_new_users_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """新規ユーザー推移を取得します。"""
        result = []
        today = date.today()

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=UTC)
            end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=UTC)

            query = (
                select(func.count())
                .select_from(UserAccount)
                .where(
                    UserAccount.created_at >= start,
                    UserAccount.created_at <= end,
                )
            )
            res = await self.db.execute(query)
            count = res.scalar_one() or 0

            result.append(TimeSeriesDataPoint(date=target_date, value=float(count)))

        return result

    def _format_bytes(self, bytes_value: int) -> str:
        """バイト数を人間が読める形式に変換します。"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} PB"
```

---

### 2.5 SessionManagementService（セッション管理サービス）

**ファイル**: `src/app/services/admin/session_management_service.py`

**対応ユースケース**: SA-035〜SA-036

```python
"""セッション管理サービス。

このモジュールは、ユーザーセッションの管理機能を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin.user_session_repository import UserSessionRepository
from app.schemas.admin.session_management import (
    DeviceInfo,
    SessionFilter,
    SessionListResponse,
    SessionResponse,
    SessionStatistics,
    SessionUserInfo,
)

logger = get_logger(__name__)


class SessionManagementService:
    """セッション管理サービス。

    ユーザーセッションの一覧取得・強制終了機能を提供します。

    メソッド:
        - list_sessions: セッション一覧を取得
        - list_user_sessions: ユーザーのセッション一覧を取得
        - terminate_session: セッションを終了
        - terminate_all_user_sessions: ユーザーの全セッションを終了
        - get_statistics: セッション統計を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.repository = UserSessionRepository(db)

    @measure_performance
    async def list_sessions(
        self,
        filter_params: SessionFilter,
    ) -> SessionListResponse:
        """セッション一覧を取得します。

        Args:
            filter_params: フィルタパラメータ

        Returns:
            SessionListResponse: セッション一覧
        """
        logger.info(
            "セッション一覧を取得中",
            filters=filter_params.model_dump(exclude_unset=True),
            action="list_sessions",
        )

        sessions = await self.repository.list_active(
            user_id=filter_params.user_id,
            ip_address=filter_params.ip_address,
            skip=(filter_params.page - 1) * filter_params.limit,
            limit=filter_params.limit,
        )

        active_count = await self.repository.count_active()
        logins_today = await self.repository.count_logins_today()

        items = [self._to_response(s) for s in sessions]

        return SessionListResponse(
            items=items,
            total=active_count,
            statistics=SessionStatistics(
                active_sessions=active_count,
                logins_today=logins_today,
            ),
        )

    @measure_performance
    async def list_user_sessions(
        self,
        user_id: uuid.UUID,
    ) -> list[SessionResponse]:
        """ユーザーのセッション一覧を取得します。

        Args:
            user_id: ユーザーID

        Returns:
            list[SessionResponse]: セッションリスト
        """
        logger.info(
            "ユーザーのセッション一覧を取得中",
            user_id=str(user_id),
            action="list_user_sessions",
        )

        sessions = await self.repository.list_by_user(user_id, active_only=True)
        return [self._to_response(s) for s in sessions]

    @measure_performance
    @transactional
    async def terminate_session(
        self,
        session_id: uuid.UUID,
        reason: str,
        terminated_by: uuid.UUID,
    ) -> SessionResponse:
        """セッションを終了します。

        Args:
            session_id: セッションID
            reason: 終了理由
            terminated_by: 終了実行者ID

        Returns:
            SessionResponse: 終了したセッション

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        logger.info(
            "セッションを終了中",
            session_id=str(session_id),
            reason=reason,
            terminated_by=str(terminated_by),
            action="terminate_session",
        )

        session = await self.repository.terminate_session(session_id, reason)
        if session is None:
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        logger.warning(
            "セッションを強制終了しました",
            session_id=str(session_id),
            user_id=str(session.user_id),
            terminated_by=str(terminated_by),
        )

        return self._to_response(session)

    @measure_performance
    @transactional
    async def terminate_all_user_sessions(
        self,
        user_id: uuid.UUID,
        reason: str,
        terminated_by: uuid.UUID,
    ) -> int:
        """ユーザーの全セッションを終了します。

        Args:
            user_id: ユーザーID
            reason: 終了理由
            terminated_by: 終了実行者ID

        Returns:
            int: 終了したセッション数
        """
        logger.info(
            "ユーザーの全セッションを終了中",
            user_id=str(user_id),
            reason=reason,
            terminated_by=str(terminated_by),
            action="terminate_all_user_sessions",
        )

        count = await self.repository.terminate_all_user_sessions(user_id, reason)

        logger.warning(
            "ユーザーの全セッションを強制終了しました",
            user_id=str(user_id),
            terminated_count=count,
            terminated_by=str(terminated_by),
        )

        return count

    def _to_response(self, session) -> SessionResponse:
        """モデルをレスポンスに変換します。"""
        device_info = None
        if session.device_info:
            device_info = DeviceInfo(
                os=session.device_info.get("os"),
                browser=session.device_info.get("browser"),
            )

        return SessionResponse(
            id=session.id,
            user=SessionUserInfo(
                id=session.user.id,
                name=session.user.display_name,
                email=session.user.email,
            ),
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_info=device_info,
            login_at=session.login_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            is_active=session.is_active,
        )
```

---

### 2.6 その他のサービス概要

残りのサービスは同様のパターンで実装します。

#### NotificationService（SA-031〜SA-034）

```python
"""通知管理サービス。

主なメソッド:
    - list_alerts: アラート一覧を取得
    - create_alert: アラートを作成
    - update_alert: アラートを更新
    - delete_alert: アラートを削除
    - list_templates: テンプレート一覧を取得
    - update_template: テンプレートを更新
    - list_announcements: お知らせ一覧を取得
    - create_announcement: お知らせを作成
    - update_announcement: お知らせを更新
    - delete_announcement: お知らせを削除
"""
```

#### BulkOperationService（SA-027〜SA-030）

```python
"""一括操作サービス。

主なメソッド:
    - import_users: ユーザーを一括インポート (@transactional)
    - export_users: ユーザーを一括エクスポート
    - deactivate_inactive_users: 非アクティブユーザーを一括無効化 (@transactional)
    - archive_inactive_projects: 非アクティブプロジェクトを一括アーカイブ (@transactional)

注意: 一括操作は複数レコードを変更するため、必ず @transactional デコレータを使用し、
      エラー時に全件ロールバックされることを保証します。
"""

from app.api.decorators import measure_performance, transactional


class BulkOperationService:
    """一括操作サービス。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @measure_performance
    @transactional
    async def import_users(
        self,
        file: UploadFile,
        performed_by: uuid.UUID,
    ) -> BulkImportResponse:
        """ユーザーを一括インポートします。

        トランザクション内で処理し、エラー時は全件ロールバックします。
        """
        ...

    @measure_performance
    async def export_users(
        self,
        filter_params: UserExportFilter,
    ) -> str:
        """ユーザーを一括エクスポートします。

        読み取り専用のため @transactional 不要。
        """
        ...

    @measure_performance
    @transactional
    async def deactivate_inactive_users(
        self,
        inactive_days: int,
        dry_run: bool = False,
        performed_by: uuid.UUID | None = None,
    ) -> BulkDeactivateResponse:
        """非アクティブユーザーを一括無効化します。

        dry_run=True の場合はプレビューのみ（変更なし）。
        dry_run=False の場合はトランザクション内で全ユーザーを無効化。
        """
        ...

    @measure_performance
    @transactional
    async def archive_inactive_projects(
        self,
        inactive_days: int,
        dry_run: bool = False,
        performed_by: uuid.UUID | None = None,
    ) -> BulkArchiveResponse:
        """非アクティブプロジェクトを一括アーカイブします。

        dry_run=True の場合はプレビューのみ（変更なし）。
        dry_run=False の場合はトランザクション内で全プロジェクトをアーカイブ。
        """
        ...
```

#### DataManagementService（SA-037〜SA-040）

```python
"""データ管理サービス。

主なメソッド:
    - preview_cleanup: クリーンアップをプレビュー
    - execute_cleanup: クリーンアップを実行 (@transactional)
    - list_orphan_files: 孤立ファイル一覧を取得
    - cleanup_orphan_files: 孤立ファイルをクリーンアップ (@transactional)
    - get_retention_policy: 保持ポリシーを取得
    - update_retention_policy: 保持ポリシーを更新 (@transactional)

注意: データ削除を伴う操作は @transactional デコレータを使用し、
      エラー時にロールバックされることを保証します。
"""

from app.api.decorators import measure_performance, transactional


class DataManagementService:
    """データ管理サービス。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @measure_performance
    async def preview_cleanup(
        self,
        target_types: list[str],
        retention_days: int,
    ) -> CleanupPreviewResponse:
        """クリーンアップをプレビューします。

        読み取り専用のため @transactional 不要。
        """
        ...

    @measure_performance
    @transactional
    async def execute_cleanup(
        self,
        target_types: list[str],
        retention_days: int,
        performed_by: uuid.UUID,
    ) -> CleanupExecuteResponse:
        """クリーンアップを実行します。

        トランザクション内で処理し、エラー時は全件ロールバックします。
        """
        ...

    @measure_performance
    async def list_orphan_files(self) -> OrphanFileListResponse:
        """孤立ファイル一覧を取得します。

        読み取り専用のため @transactional 不要。
        """
        ...

    @measure_performance
    @transactional
    async def cleanup_orphan_files(
        self,
        file_ids: list[uuid.UUID] | None = None,
        delete_all: bool = False,
        performed_by: uuid.UUID | None = None,
    ) -> OrphanFileCleanupResponse:
        """孤立ファイルをクリーンアップします。

        トランザクション内で処理し、エラー時はロールバックします。
        """
        ...

    @measure_performance
    async def get_retention_policy(self) -> RetentionPolicyResponse:
        """保持ポリシーを取得します。

        読み取り専用のため @transactional 不要。
        """
        ...

    @measure_performance
    @transactional
    async def update_retention_policy(
        self,
        policy: RetentionPolicyUpdate,
        updated_by: uuid.UUID,
    ) -> RetentionPolicyResponse:
        """保持ポリシーを更新します。

        複数設定を一括更新するためトランザクション内で処理します。
        """
        ...
```

#### SupportToolsService（SA-041〜SA-043）

```python
"""サポートツールサービス。

主なメソッド:
    - start_impersonation: ユーザー代行を開始
    - end_impersonation: ユーザー代行を終了
    - enable_debug_mode: デバッグモードを有効化
    - disable_debug_mode: デバッグモードを無効化
    - simple_health_check: 簡易ヘルスチェック
    - detailed_health_check: 詳細ヘルスチェック
"""
```

---

## 3. __init__.py ファイル

### 3.1 admin/__init__.py

```python
"""システム管理サービス。"""

from app.services.admin.activity_tracking_service import ActivityTrackingService
from app.services.admin.audit_log_service import AuditLogService
from app.services.admin.bulk_operation_service import BulkOperationService
from app.services.admin.data_management_service import DataManagementService
from app.services.admin.notification_service import NotificationService
from app.services.admin.session_management_service import SessionManagementService
from app.services.admin.statistics_service import StatisticsService
from app.services.admin.support_tools_service import SupportToolsService
from app.services.admin.system_setting_service import SystemSettingService

__all__ = [
    "ActivityTrackingService",
    "AuditLogService",
    "SystemSettingService",
    "StatisticsService",
    "NotificationService",
    "SessionManagementService",
    "BulkOperationService",
    "DataManagementService",
    "SupportToolsService",
]
```

---

## 4. 依存性注入

### 4.1 サービス依存性の定義

**ファイル**: `src/app/api/core/dependencies/admin.py`

```python
"""システム管理サービスの依存性注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.dependencies.database import get_db
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


async def get_activity_tracking_service(
    db: AsyncSession = Depends(get_db),
) -> ActivityTrackingService:
    return ActivityTrackingService(db)


async def get_audit_log_service(
    db: AsyncSession = Depends(get_db),
) -> AuditLogService:
    return AuditLogService(db)


async def get_system_setting_service(
    db: AsyncSession = Depends(get_db),
) -> SystemSettingService:
    return SystemSettingService(db)


async def get_statistics_service(
    db: AsyncSession = Depends(get_db),
) -> StatisticsService:
    return StatisticsService(db)


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(db)


async def get_session_management_service(
    db: AsyncSession = Depends(get_db),
) -> SessionManagementService:
    return SessionManagementService(db)


async def get_bulk_operation_service(
    db: AsyncSession = Depends(get_db),
) -> BulkOperationService:
    return BulkOperationService(db)


async def get_data_management_service(
    db: AsyncSession = Depends(get_db),
) -> DataManagementService:
    return DataManagementService(db)


async def get_support_tools_service(
    db: AsyncSession = Depends(get_db),
) -> SupportToolsService:
    return SupportToolsService(db)


# 型エイリアス
ActivityTrackingServiceDep = Annotated[
    ActivityTrackingService, Depends(get_activity_tracking_service)
]
AuditLogServiceDep = Annotated[AuditLogService, Depends(get_audit_log_service)]
SystemSettingServiceDep = Annotated[
    SystemSettingService, Depends(get_system_setting_service)
]
StatisticsServiceDep = Annotated[StatisticsService, Depends(get_statistics_service)]
NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]
SessionManagementServiceDep = Annotated[
    SessionManagementService, Depends(get_session_management_service)
]
BulkOperationServiceDep = Annotated[
    BulkOperationService, Depends(get_bulk_operation_service)
]
DataManagementServiceDep = Annotated[
    DataManagementService, Depends(get_data_management_service)
]
SupportToolsServiceDep = Annotated[
    SupportToolsService, Depends(get_support_tools_service)
]
```

---

## 5. 注意事項

### 5.1 トランザクション管理

- `@transactional` デコレータで自動コミット/ロールバック
- 読み取り専用メソッドにはデコレータ不要
- 複数リポジトリを使う場合は同一トランザクション内で処理

### 5.2 エラーハンドリング

- `NotFoundError`: リソースが見つからない場合
- `AuthorizationError`: 権限がない場合
- `ValidationError`: 入力値が不正な場合
- 予期しない例外はロギングして再スロー

### 5.3 ロギング

- 操作開始時に `action` を含むログを出力
- 重要な操作完了時にログを出力
- エラー時は `logger.error` でスタックトレースを含める
- セキュリティイベントは `logger.warning` 以上で記録

### 5.4 パフォーマンス

- `@measure_performance` で処理時間を計測
- 大量データの処理はバッチ処理を検討
- N+1問題を回避するためリポジトリで適切にロード

---

## 6. 一括操作のトレーサビリティ（operation_id）

### 6.1 概要

一括操作（インポート、無効化、アーカイブ等）では、複数のレコードが同時に変更されます。
これらの変更を追跡し、必要に応じてロールバック対象を特定するため、`operation_id` を導入します。

### 6.2 operation_id の設計

```python
"""一括操作のトレーサビリティ機能。

operation_id は一括操作の各処理を紐づけるユニークな識別子です。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class BulkOperationContext:
    """一括操作コンテキスト。

    一括操作の実行情報を保持します。

    Attributes:
        operation_id: 操作を一意に識別するID
        operation_type: 操作種別（IMPORT/DEACTIVATE/ARCHIVE/CLEANUP等）
        started_at: 操作開始日時
        performed_by: 実行者ユーザーID
        target_count: 対象レコード数
        processed_count: 処理済みレコード数
        success_count: 成功件数
        failure_count: 失敗件数
        metadata: 追加メタデータ
    """

    operation_id: uuid.UUID
    operation_type: str
    started_at: datetime
    performed_by: uuid.UUID
    target_count: int = 0
    processed_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        operation_type: str,
        performed_by: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> "BulkOperationContext":
        """新しい操作コンテキストを作成します。"""
        return cls(
            operation_id=uuid.uuid4(),
            operation_type=operation_type,
            started_at=datetime.now(),
            performed_by=performed_by,
            metadata=metadata,
        )
```

### 6.3 サービスでの使用例

```python
class BulkOperationService:
    """一括操作サービス。"""

    @measure_performance
    @transactional
    async def deactivate_inactive_users(
        self,
        inactive_days: int,
        dry_run: bool = False,
        performed_by: uuid.UUID | None = None,
    ) -> BulkDeactivateResponse:
        """非アクティブユーザーを一括無効化します。"""
        # 操作コンテキストを作成
        ctx = BulkOperationContext.create(
            operation_type="USER_DEACTIVATE",
            performed_by=performed_by,
            metadata={"inactive_days": inactive_days, "dry_run": dry_run},
        )

        # 対象ユーザーを取得
        target_users = await self.user_repository.find_inactive_users(inactive_days)
        ctx.target_count = len(target_users)

        if dry_run:
            # プレビューモード：変更なし
            return BulkDeactivateResponse(
                success=True,
                deactivated_count=0,
                operation_id=ctx.operation_id,
                preview_items=[...],
            )

        # 実行モード
        for user in target_users:
            try:
                await self.user_repository.update(
                    user.id,
                    {"status": "INACTIVE", "deactivated_by_operation_id": ctx.operation_id},
                )
                ctx.success_count += 1
            except Exception as e:
                ctx.failure_count += 1
                logger.error(f"Failed to deactivate user {user.id}: {e}")
            ctx.processed_count += 1

        # 操作ログを記録
        await self._record_bulk_operation_log(ctx)

        return BulkDeactivateResponse(
            success=ctx.failure_count == 0,
            deactivated_count=ctx.success_count,
            operation_id=ctx.operation_id,
        )

    async def _record_bulk_operation_log(self, ctx: BulkOperationContext) -> None:
        """一括操作ログを記録します。"""
        await self.audit_log_repository.create(
            AuditLog(
                event_type=AuditEventType.DATA_CHANGE,
                action=ctx.operation_type,
                resource_type="BULK_OPERATION",
                resource_id=ctx.operation_id,
                user_id=ctx.performed_by,
                severity=AuditSeverity.INFO,
                metadata={
                    "operation_id": str(ctx.operation_id),
                    "target_count": ctx.target_count,
                    "success_count": ctx.success_count,
                    "failure_count": ctx.failure_count,
                    "duration_ms": (datetime.now() - ctx.started_at).total_seconds() * 1000,
                    **ctx.metadata,
                },
            )
        )
```

### 6.4 レスポンスへの operation_id 追加

```python
# schemas/admin/bulk_operation.py

class BulkDeactivateResponse(BaseCamelCaseModel):
    """一括無効化レスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    deactivated_count: int = Field(..., description="無効化件数")
    operation_id: uuid.UUID = Field(..., description="操作ID（トレーサビリティ用）")
    preview_items: list[BulkDeactivatePreviewItem] | None = Field(
        default=None, description="プレビューアイテム（dry_run時のみ）"
    )


class BulkArchiveResponse(BaseCamelCaseModel):
    """一括アーカイブレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    archived_count: int = Field(..., description="アーカイブ件数")
    operation_id: uuid.UUID = Field(..., description="操作ID（トレーサビリティ用）")
    preview_items: list[BulkArchivePreviewItem] | None = Field(
        default=None, description="プレビューアイテム（dry_run時のみ）"
    )
```

### 6.5 operation_id による追跡

```python
# 操作履歴から特定の一括操作を追跡
@router.get("/bulk-operations/{operation_id}")
async def get_bulk_operation_details(
    operation_id: uuid.UUID,
    audit_log_service: AuditLogServiceDep,
) -> BulkOperationDetailResponse:
    """一括操作の詳細を取得します。

    operation_id で実行された一括操作の詳細と、
    影響を受けたレコードの一覧を返します。
    """
    # 操作ログを取得
    operation_log = await audit_log_service.get_by_resource_id(
        resource_type="BULK_OPERATION",
        resource_id=operation_id,
    )

    # 影響を受けたレコードを取得
    affected_records = await audit_log_service.find_by_operation_id(operation_id)

    return BulkOperationDetailResponse(
        operation_id=operation_id,
        operation_type=operation_log.action,
        performed_by=operation_log.user_id,
        started_at=operation_log.created_at,
        metadata=operation_log.metadata,
        affected_records=affected_records,
    )
```
