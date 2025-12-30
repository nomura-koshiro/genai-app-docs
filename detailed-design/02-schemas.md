# システム管理機能 詳細設計書 - スキーマ層

## 1. 概要

本ドキュメントでは、システム管理機能（SA-001〜SA-043）で追加するPydanticスキーマの詳細設計を定義する。

### 1.1 既存パターンへの準拠

既存のスキーマ実装パターンに従い、以下の規約を適用する：

- `BaseCamelCaseModel` を継承（snake_case ↔ camelCase 自動変換）
- `BaseCamelCaseORMModel` をORMレスポンス用に使用（`from_attributes=True`）
- `Field()` でバリデーションと説明を定義
- Base/Create/Update/Response の4層構造

### 1.2 ファイル構成

```
src/app/schemas/admin/
├── __init__.py
├── activity_log.py           # 操作履歴スキーマ
├── audit_log.py              # 監査ログスキーマ
├── system_setting.py         # システム設定スキーマ
├── statistics.py             # 統計情報スキーマ
├── bulk_operation.py         # 一括操作スキーマ
├── announcement.py           # お知らせスキーマ
├── notification_template.py  # 通知テンプレートスキーマ
├── system_alert.py           # アラートスキーマ
├── session_management.py     # セッション管理スキーマ
├── data_management.py        # データ管理スキーマ
├── support_tools.py          # サポートツールスキーマ
├── project_admin.py          # 管理者用プロジェクトスキーマ
└── health_check.py           # ヘルスチェックスキーマ
```

---

## 2. スキーマ詳細設計

### 2.1 操作履歴スキーマ（activity_log.py）

**対応ユースケース**: SA-001〜SA-006

```python
"""操作履歴スキーマ。

このモジュールは、ユーザー操作履歴のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# フィルタ・クエリスキーマ
# ================================================================================


class ActivityLogFilter(BaseCamelCaseModel):
    """操作履歴フィルタスキーマ。

    Attributes:
        user_id (UUID | None): ユーザーIDで絞り込み
        action_type (str | None): 操作種別で絞り込み
        resource_type (str | None): リソース種別で絞り込み
        start_date (datetime | None): 開始日時
        end_date (datetime | None): 終了日時
        has_error (bool | None): エラーのみ取得
        page (int): ページ番号
        limit (int): 取得件数
    """

    user_id: uuid.UUID | None = Field(default=None, description="ユーザーIDで絞り込み")
    action_type: str | None = Field(default=None, description="操作種別で絞り込み")
    resource_type: str | None = Field(default=None, description="リソース種別で絞り込み")
    start_date: datetime | None = Field(default=None, description="開始日時")
    end_date: datetime | None = Field(default=None, description="終了日時")
    has_error: bool | None = Field(default=None, description="エラーのみ取得")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class ActivityLogUserInfo(BaseCamelCaseModel):
    """操作履歴のユーザー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: str | None = Field(default=None, description="メールアドレス")


class ActivityLogResponse(BaseCamelCaseORMModel):
    """操作履歴レスポンススキーマ。

    Attributes:
        id (UUID): 操作履歴ID
        user_id (UUID | None): ユーザーID
        user_name (str | None): ユーザー名
        action_type (str): 操作種別
        resource_type (str | None): リソース種別
        resource_id (UUID | None): リソースID
        endpoint (str): APIエンドポイント
        method (str): HTTPメソッド
        response_status (int): HTTPステータス
        error_message (str | None): エラーメッセージ
        error_code (str | None): エラーコード
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        duration_ms (int): 処理時間
        created_at (datetime): 作成日時
    """

    id: uuid.UUID = Field(..., description="操作履歴ID")
    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    user_name: str | None = Field(default=None, description="ユーザー名")
    action_type: str = Field(..., description="操作種別")
    resource_type: str | None = Field(default=None, description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    endpoint: str = Field(..., description="APIエンドポイント")
    method: str = Field(..., description="HTTPメソッド")
    response_status: int = Field(..., description="HTTPステータス")
    error_message: str | None = Field(default=None, description="エラーメッセージ")
    error_code: str | None = Field(default=None, description="エラーコード")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    duration_ms: int = Field(..., description="処理時間（ミリ秒）")
    created_at: datetime = Field(..., description="作成日時")


class ActivityLogDetailResponse(ActivityLogResponse):
    """操作履歴詳細レスポンススキーマ。

    ActivityLogResponseに加え、リクエストボディとユーザー詳細情報を含む。
    """

    user_email: str | None = Field(default=None, description="ユーザーメールアドレス")
    request_body: dict | None = Field(default=None, description="リクエストボディ")


class ActivityLogListResponse(BaseCamelCaseModel):
    """操作履歴一覧レスポンススキーマ。

    Attributes:
        items (list[ActivityLogResponse]): 操作履歴リスト
        total (int): 総件数
        page (int): ページ番号
        limit (int): 取得件数
        total_pages (int): 総ページ数
    """

    items: list[ActivityLogResponse] = Field(..., description="操作履歴リスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    limit: int = Field(..., description="取得件数")
    total_pages: int = Field(..., description="総ページ数")
```

---

### 2.2 監査ログスキーマ（audit_log.py）

**対応ユースケース**: SA-012〜SA-016

```python
"""監査ログスキーマ。

このモジュールは、監査ログのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# フィルタ・クエリスキーマ
# ================================================================================


class AuditLogFilter(BaseCamelCaseModel):
    """監査ログフィルタスキーマ。

    Attributes:
        event_type (str | None): イベント種別
        user_id (UUID | None): ユーザーID
        resource_type (str | None): リソース種別
        resource_id (UUID | None): リソースID
        severity (str | None): 重要度
        start_date (datetime | None): 開始日時
        end_date (datetime | None): 終了日時
        page (int): ページ番号
        limit (int): 取得件数
    """

    event_type: str | None = Field(default=None, description="イベント種別")
    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    resource_type: str | None = Field(default=None, description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    severity: str | None = Field(default=None, description="重要度")
    start_date: datetime | None = Field(default=None, description="開始日時")
    end_date: datetime | None = Field(default=None, description="終了日時")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


class AuditLogExportFilter(BaseCamelCaseModel):
    """監査ログエクスポートフィルタスキーマ。"""

    format: str = Field(default="csv", description="出力形式（csv/json）")
    event_type: str | None = Field(default=None, description="イベント種別フィルタ")
    start_date: datetime | None = Field(default=None, description="開始日時")
    end_date: datetime | None = Field(default=None, description="終了日時")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class AuditLogResponse(BaseCamelCaseORMModel):
    """監査ログレスポンススキーマ。

    Attributes:
        id (UUID): 監査ログID
        user_id (UUID | None): ユーザーID
        user_name (str | None): ユーザー名
        user_email (str | None): ユーザーメール
        event_type (str): イベント種別
        action (str): アクション
        resource_type (str): リソース種別
        resource_id (UUID | None): リソースID
        old_value (dict | None): 変更前の値
        new_value (dict | None): 変更後の値
        changed_fields (list | None): 変更フィールド
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        severity (str): 重要度
        metadata (dict | None): メタデータ
        created_at (datetime): 作成日時
    """

    id: uuid.UUID = Field(..., description="監査ログID")
    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    user_name: str | None = Field(default=None, description="ユーザー名")
    user_email: str | None = Field(default=None, description="ユーザーメール")
    event_type: str = Field(..., description="イベント種別")
    action: str = Field(..., description="アクション")
    resource_type: str = Field(..., description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    old_value: dict | None = Field(default=None, description="変更前の値")
    new_value: dict | None = Field(default=None, description="変更後の値")
    changed_fields: list | None = Field(default=None, description="変更フィールド")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    severity: str = Field(..., description="重要度")
    metadata: dict | None = Field(default=None, description="メタデータ")
    created_at: datetime = Field(..., description="作成日時")


class AuditLogListResponse(BaseCamelCaseModel):
    """監査ログ一覧レスポンススキーマ。"""

    items: list[AuditLogResponse] = Field(..., description="監査ログリスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    limit: int = Field(..., description="取得件数")
    total_pages: int = Field(..., description="総ページ数")
```

---

### 2.3 システム設定スキーマ（system_setting.py）

**対応ユースケース**: SA-017〜SA-020

```python
"""システム設定スキーマ。

このモジュールは、システム設定のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class SystemSettingUpdate(BaseCamelCaseModel):
    """システム設定更新リクエストスキーマ。"""

    value: Any = Field(..., description="設定値")


class MaintenanceModeEnable(BaseCamelCaseModel):
    """メンテナンスモード有効化リクエストスキーマ。"""

    message: str = Field(..., min_length=1, max_length=500, description="メンテナンスメッセージ")
    allow_admin_access: bool = Field(default=True, description="管理者アクセス許可")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class SystemSettingResponse(BaseCamelCaseORMModel):
    """システム設定レスポンススキーマ。

    Attributes:
        key (str): 設定キー
        value (Any): 設定値
        value_type (str): 値の型
        description (str | None): 説明
        is_editable (bool): 編集可能フラグ
    """

    key: str = Field(..., description="設定キー")
    value: Any = Field(..., description="設定値")
    value_type: str = Field(..., description="値の型")
    description: str | None = Field(default=None, description="説明")
    is_editable: bool = Field(..., description="編集可能フラグ")


class SystemSettingDetailResponse(SystemSettingResponse):
    """システム設定詳細レスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="設定ID")
    category: str = Field(..., description="カテゴリ")
    is_secret: bool = Field(..., description="機密設定フラグ")
    updated_by: uuid.UUID | None = Field(default=None, description="更新者ID")
    updated_at: datetime = Field(..., description="更新日時")


class SystemSettingsByCategoryResponse(BaseCamelCaseModel):
    """カテゴリ別システム設定レスポンススキーマ。"""

    categories: dict[str, list[SystemSettingResponse]] = Field(
        ..., description="カテゴリ別設定"
    )


class MaintenanceModeResponse(BaseCamelCaseModel):
    """メンテナンスモードレスポンススキーマ。"""

    enabled: bool = Field(..., description="メンテナンスモード状態")
    message: str | None = Field(default=None, description="メンテナンスメッセージ")
    allow_admin_access: bool = Field(default=True, description="管理者アクセス許可")
```

---

### 2.4 統計情報スキーマ（statistics.py）

**対応ユースケース**: SA-022〜SA-026

```python
"""システム統計スキーマ。

このモジュールは、システム統計情報のレスポンススキーマを定義します。
"""

from datetime import date, datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# サブスキーマ
# ================================================================================


class UserStatistics(BaseCamelCaseModel):
    """ユーザー統計情報。"""

    total: int = Field(..., description="総ユーザー数")
    active_today: int = Field(..., description="本日のアクティブユーザー数")
    new_this_month: int = Field(..., description="今月の新規ユーザー数")


class ProjectStatistics(BaseCamelCaseModel):
    """プロジェクト統計情報。"""

    total: int = Field(..., description="総プロジェクト数")
    active: int = Field(..., description="アクティブプロジェクト数")
    created_this_month: int = Field(..., description="今月の作成数")


class StorageStatistics(BaseCamelCaseModel):
    """ストレージ統計情報。"""

    total_bytes: int = Field(..., description="総使用量（バイト）")
    total_display: str = Field(..., description="総使用量（表示用）")
    used_percentage: float = Field(..., description="使用率（%）")


class ApiStatistics(BaseCamelCaseModel):
    """API統計情報。"""

    requests_today: int = Field(..., description="本日のリクエスト数")
    average_response_ms: float = Field(..., description="平均レスポンス時間（ミリ秒）")
    error_rate_percentage: float = Field(..., description="エラー率（%）")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class StatisticsOverviewResponse(BaseCamelCaseModel):
    """統計概要レスポンススキーマ。

    Attributes:
        users (UserStatistics): ユーザー統計
        projects (ProjectStatistics): プロジェクト統計
        storage (StorageStatistics): ストレージ統計
        api (ApiStatistics): API統計
    """

    users: UserStatistics = Field(..., description="ユーザー統計")
    projects: ProjectStatistics = Field(..., description="プロジェクト統計")
    storage: StorageStatistics = Field(..., description="ストレージ統計")
    api: ApiStatistics = Field(..., description="API統計")


class TimeSeriesDataPoint(BaseCamelCaseModel):
    """時系列データポイント。"""

    date: date = Field(..., description="日付")
    value: float = Field(..., description="値")


class UserStatisticsDetailResponse(BaseCamelCaseModel):
    """ユーザー統計詳細レスポンススキーマ。"""

    total: int = Field(..., description="総ユーザー数")
    active_users: list[TimeSeriesDataPoint] = Field(..., description="アクティブユーザー推移")
    new_users: list[TimeSeriesDataPoint] = Field(..., description="新規ユーザー推移")


class StorageStatisticsDetailResponse(BaseCamelCaseModel):
    """ストレージ統計詳細レスポンススキーマ。"""

    total_bytes: int = Field(..., description="総使用量（バイト）")
    total_display: str = Field(..., description="総使用量（表示用）")
    usage_trend: list[TimeSeriesDataPoint] = Field(..., description="使用量推移")


class ApiStatisticsDetailResponse(BaseCamelCaseModel):
    """API統計詳細レスポンススキーマ。"""

    total_requests: int = Field(..., description="総リクエスト数")
    request_trend: list[TimeSeriesDataPoint] = Field(..., description="リクエスト数推移")
    average_response_ms: float = Field(..., description="平均レスポンス時間")


class ErrorStatisticsDetailResponse(BaseCamelCaseModel):
    """エラー統計詳細レスポンススキーマ。"""

    total_errors: int = Field(..., description="総エラー数")
    error_rate: float = Field(..., description="エラー率")
    error_trend: list[TimeSeriesDataPoint] = Field(..., description="エラー率推移")
    error_by_type: dict[str, int] = Field(..., description="種別ごとのエラー数")
```

---

### 2.5 一括操作スキーマ（bulk_operation.py）

**対応ユースケース**: SA-027〜SA-030

```python
"""一括操作スキーマ。

このモジュールは、一括操作のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class BulkUserDeactivateRequest(BaseCamelCaseModel):
    """非アクティブユーザー一括無効化リクエスト。"""

    inactive_days: int = Field(..., ge=1, description="非アクティブ日数")
    dry_run: bool = Field(default=False, description="プレビューのみ")


class BulkProjectArchiveRequest(BaseCamelCaseModel):
    """古いプロジェクト一括アーカイブリクエスト。"""

    inactive_days: int = Field(..., ge=1, description="非アクティブ日数")
    dry_run: bool = Field(default=False, description="プレビューのみ")


class UserExportFilter(BaseCamelCaseModel):
    """ユーザーエクスポートフィルタ。"""

    status: str | None = Field(default=None, description="ステータスフィルタ")
    role: str | None = Field(default=None, description="ロールフィルタ")
    format: str = Field(default="csv", description="出力形式（csv/xlsx）")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class ImportErrorDetail(BaseCamelCaseModel):
    """インポートエラー詳細。"""

    row: int = Field(..., description="行番号")
    error: str = Field(..., description="エラー内容")


class BulkImportResponse(BaseCamelCaseModel):
    """一括インポートレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    imported_count: int = Field(..., description="インポート件数")
    skipped_count: int = Field(..., description="スキップ件数")
    errors: list[ImportErrorDetail] = Field(default_factory=list, description="エラー一覧")


class BulkDeactivatePreviewItem(BaseCamelCaseModel):
    """無効化プレビューアイテム。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: str = Field(..., description="メールアドレス")
    last_activity_at: datetime | None = Field(default=None, description="最終アクティビティ")


class BulkDeactivateResponse(BaseCamelCaseModel):
    """一括無効化レスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    deactivated_count: int = Field(..., description="無効化件数")
    preview_items: list[BulkDeactivatePreviewItem] | None = Field(
        default=None, description="プレビューアイテム（dry_run時のみ）"
    )


class BulkArchivePreviewItem(BaseCamelCaseModel):
    """アーカイブプレビューアイテム。"""

    id: uuid.UUID = Field(..., description="プロジェクトID")
    name: str = Field(..., description="プロジェクト名")
    code: str = Field(..., description="プロジェクトコード")
    last_activity_at: datetime | None = Field(default=None, description="最終アクティビティ")


class BulkArchiveResponse(BaseCamelCaseModel):
    """一括アーカイブレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    archived_count: int = Field(..., description="アーカイブ件数")
    preview_items: list[BulkArchivePreviewItem] | None = Field(
        default=None, description="プレビューアイテム（dry_run時のみ）"
    )
```

---

### 2.6 お知らせスキーマ（announcement.py）

**対応ユースケース**: SA-033〜SA-034

```python
"""システムお知らせスキーマ。

このモジュールは、システムお知らせのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class AnnouncementCreate(BaseCamelCaseModel):
    """お知らせ作成リクエストスキーマ。

    Attributes:
        title (str): タイトル
        content (str): 本文
        announcement_type (str): 種別
        priority (int): 優先度
        start_at (datetime): 表示開始日時
        end_at (datetime | None): 表示終了日時
        target_roles (list | None): 対象ロール
    """

    title: str = Field(..., min_length=1, max_length=200, description="タイトル")
    content: str = Field(..., min_length=1, description="本文")
    announcement_type: str = Field(..., description="種別（INFO/WARNING/MAINTENANCE）")
    priority: int = Field(default=5, ge=1, le=10, description="優先度（1が最高）")
    start_at: datetime = Field(..., description="表示開始日時")
    end_at: datetime | None = Field(default=None, description="表示終了日時")
    target_roles: list[str] | None = Field(default=None, description="対象ロール")


class AnnouncementUpdate(BaseCamelCaseModel):
    """お知らせ更新リクエストスキーマ。"""

    title: str | None = Field(default=None, max_length=200, description="タイトル")
    content: str | None = Field(default=None, description="本文")
    announcement_type: str | None = Field(default=None, description="種別")
    priority: int | None = Field(default=None, ge=1, le=10, description="優先度")
    start_at: datetime | None = Field(default=None, description="表示開始日時")
    end_at: datetime | None = Field(default=None, description="表示終了日時")
    is_active: bool | None = Field(default=None, description="有効フラグ")
    target_roles: list[str] | None = Field(default=None, description="対象ロール")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class AnnouncementResponse(BaseCamelCaseORMModel):
    """お知らせレスポンススキーマ。

    Attributes:
        id (UUID): お知らせID
        title (str): タイトル
        content (str): 本文
        announcement_type (str): 種別
        priority (int): 優先度
        start_at (datetime): 表示開始日時
        end_at (datetime | None): 表示終了日時
        is_active (bool): 有効フラグ
        target_roles (list | None): 対象ロール
        created_by (UUID): 作成者ID
        created_by_name (str | None): 作成者名
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
    """

    id: uuid.UUID = Field(..., description="お知らせID")
    title: str = Field(..., description="タイトル")
    content: str = Field(..., description="本文")
    announcement_type: str = Field(..., description="種別")
    priority: int = Field(..., description="優先度")
    start_at: datetime = Field(..., description="表示開始日時")
    end_at: datetime | None = Field(default=None, description="表示終了日時")
    is_active: bool = Field(..., description="有効フラグ")
    target_roles: list[str] | None = Field(default=None, description="対象ロール")
    created_by: uuid.UUID = Field(..., description="作成者ID")
    created_by_name: str | None = Field(default=None, description="作成者名")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnnouncementListResponse(BaseCamelCaseModel):
    """お知らせ一覧レスポンススキーマ。"""

    items: list[AnnouncementResponse] = Field(..., description="お知らせリスト")
    total: int = Field(..., description="総件数")
```

---

### 2.7 通知テンプレートスキーマ（notification_template.py）

**対応ユースケース**: SA-032

```python
"""通知テンプレートスキーマ。

このモジュールは、通知テンプレートのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class NotificationTemplateCreate(BaseCamelCaseModel):
    """通知テンプレート作成リクエストスキーマ。"""

    name: str = Field(..., min_length=1, max_length=100, description="テンプレート名")
    event_type: str = Field(..., min_length=1, max_length=50, description="イベント種別")
    subject: str = Field(..., min_length=1, max_length=200, description="件名テンプレート")
    body: str = Field(..., min_length=1, description="本文テンプレート")
    variables: list[str] = Field(default_factory=list, description="利用可能変数リスト")
    is_active: bool = Field(default=True, description="有効フラグ")


class NotificationTemplateUpdate(BaseCamelCaseModel):
    """通知テンプレート更新リクエストスキーマ。"""

    name: str | None = Field(default=None, max_length=100, description="テンプレート名")
    subject: str | None = Field(default=None, max_length=200, description="件名テンプレート")
    body: str | None = Field(default=None, description="本文テンプレート")
    variables: list[str] | None = Field(default=None, description="利用可能変数リスト")
    is_active: bool | None = Field(default=None, description="有効フラグ")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class NotificationTemplateResponse(BaseCamelCaseORMModel):
    """通知テンプレートレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="テンプレートID")
    name: str = Field(..., description="テンプレート名")
    event_type: str = Field(..., description="イベント種別")
    subject: str = Field(..., description="件名テンプレート")
    body: str = Field(..., description="本文テンプレート")
    variables: list[str] = Field(..., description="利用可能変数リスト")
    is_active: bool = Field(..., description="有効フラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class NotificationTemplateListResponse(BaseCamelCaseModel):
    """通知テンプレート一覧レスポンススキーマ。"""

    items: list[NotificationTemplateResponse] = Field(..., description="テンプレートリスト")
    total: int = Field(..., description="総件数")
```

---

### 2.8 システムアラートスキーマ（system_alert.py）

**対応ユースケース**: SA-031

```python
"""システムアラートスキーマ。

このモジュールは、システムアラートのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class SystemAlertCreate(BaseCamelCaseModel):
    """システムアラート作成リクエストスキーマ。"""

    name: str = Field(..., min_length=1, max_length=100, description="アラート名")
    condition_type: str = Field(..., description="条件種別")
    threshold: dict[str, Any] = Field(..., description="閾値設定")
    comparison_operator: str = Field(..., description="比較演算子")
    notification_channels: list[str] = Field(..., description="通知先")
    is_enabled: bool = Field(default=True, description="有効フラグ")


class SystemAlertUpdate(BaseCamelCaseModel):
    """システムアラート更新リクエストスキーマ。"""

    name: str | None = Field(default=None, max_length=100, description="アラート名")
    threshold: dict[str, Any] | None = Field(default=None, description="閾値設定")
    comparison_operator: str | None = Field(default=None, description="比較演算子")
    notification_channels: list[str] | None = Field(default=None, description="通知先")
    is_enabled: bool | None = Field(default=None, description="有効フラグ")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class SystemAlertResponse(BaseCamelCaseORMModel):
    """システムアラートレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="アラートID")
    name: str = Field(..., description="アラート名")
    condition_type: str = Field(..., description="条件種別")
    threshold: dict[str, Any] = Field(..., description="閾値設定")
    comparison_operator: str = Field(..., description="比較演算子")
    notification_channels: list[str] = Field(..., description="通知先")
    is_enabled: bool = Field(..., description="有効フラグ")
    last_triggered_at: datetime | None = Field(default=None, description="最終発火日時")
    trigger_count: int = Field(..., description="発火回数")
    created_by: uuid.UUID = Field(..., description="作成者ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class SystemAlertListResponse(BaseCamelCaseModel):
    """システムアラート一覧レスポンススキーマ。"""

    items: list[SystemAlertResponse] = Field(..., description="アラートリスト")
    total: int = Field(..., description="総件数")
```

---

### 2.9 セッション管理スキーマ（session_management.py）

**対応ユースケース**: SA-035〜SA-036

```python
"""セッション管理スキーマ。

このモジュールは、ユーザーセッション管理のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# フィルタスキーマ
# ================================================================================


class SessionFilter(BaseCamelCaseModel):
    """セッションフィルタスキーマ。"""

    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


# ================================================================================
# リクエストスキーマ
# ================================================================================


class SessionTerminateRequest(BaseCamelCaseModel):
    """セッション終了リクエストスキーマ。"""

    reason: str = Field(default="FORCED", description="終了理由")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class SessionUserInfo(BaseCamelCaseModel):
    """セッションのユーザー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: str = Field(..., description="メールアドレス")


class DeviceInfo(BaseCamelCaseModel):
    """デバイス情報。"""

    os: str | None = Field(default=None, description="OS")
    browser: str | None = Field(default=None, description="ブラウザ")


class SessionResponse(BaseCamelCaseORMModel):
    """セッションレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="セッションID")
    user: SessionUserInfo = Field(..., description="ユーザー情報")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    device_info: DeviceInfo | None = Field(default=None, description="デバイス情報")
    login_at: datetime = Field(..., description="ログイン日時")
    last_activity_at: datetime = Field(..., description="最終アクティビティ日時")
    expires_at: datetime = Field(..., description="有効期限")
    is_active: bool = Field(..., description="アクティブフラグ")


class SessionStatistics(BaseCamelCaseModel):
    """セッション統計情報。"""

    active_sessions: int = Field(..., description="アクティブセッション数")
    logins_today: int = Field(..., description="本日のログイン数")


class SessionListResponse(BaseCamelCaseModel):
    """セッション一覧レスポンススキーマ。"""

    items: list[SessionResponse] = Field(..., description="セッションリスト")
    total: int = Field(..., description="総件数")
    statistics: SessionStatistics = Field(..., description="統計情報")
```

---

### 2.10 データ管理スキーマ（data_management.py）

**対応ユースケース**: SA-037〜SA-040

```python
"""データ管理スキーマ。

このモジュールは、データ管理のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class CleanupPreviewRequest(BaseCamelCaseModel):
    """クリーンアッププレビューリクエストスキーマ。"""

    target_types: list[str] = Field(..., description="対象種別")
    retention_days: int = Field(..., ge=1, description="保持日数")


class CleanupExecuteRequest(BaseCamelCaseModel):
    """クリーンアップ実行リクエストスキーマ。"""

    target_types: list[str] = Field(..., description="対象種別")
    retention_days: int = Field(..., ge=1, description="保持日数")
    dry_run: bool = Field(default=False, description="プレビューのみ")


class OrphanFileCleanupRequest(BaseCamelCaseModel):
    """孤立ファイルクリーンアップリクエストスキーマ。"""

    file_ids: list[uuid.UUID] | None = Field(default=None, description="削除するファイルID")
    delete_all: bool = Field(default=False, description="全件削除")


class RetentionPolicyUpdate(BaseCamelCaseModel):
    """保持ポリシー更新リクエストスキーマ。"""

    activity_logs_days: int | None = Field(default=None, ge=1, description="操作履歴保持期間")
    audit_logs_days: int | None = Field(default=None, ge=1, description="監査ログ保持期間")
    deleted_projects_days: int | None = Field(default=None, ge=1, description="削除プロジェクト保持期間")
    session_logs_days: int | None = Field(default=None, ge=1, description="セッションログ保持期間")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class CleanupPreviewItem(BaseCamelCaseModel):
    """クリーンアッププレビューアイテム。"""

    target_type: str = Field(..., description="対象種別")
    target_type_display: str = Field(..., description="対象種別（表示用）")
    record_count: int = Field(..., description="レコード数")
    oldest_record_at: datetime | None = Field(default=None, description="最古レコード日時")
    newest_record_at: datetime | None = Field(default=None, description="最新レコード日時")
    estimated_size_bytes: int = Field(..., description="推定サイズ（バイト）")
    estimated_size_display: str = Field(..., description="推定サイズ（表示用）")


class CleanupPreviewResponse(BaseCamelCaseModel):
    """クリーンアッププレビューレスポンス。"""

    preview: list[CleanupPreviewItem] = Field(..., description="プレビュー")
    total_record_count: int = Field(..., description="合計レコード数")
    total_estimated_size_bytes: int = Field(..., description="合計推定サイズ")
    total_estimated_size_display: str = Field(..., description="合計推定サイズ（表示用）")
    retention_days: int = Field(..., description="保持日数")
    cutoff_date: datetime = Field(..., description="カットオフ日")


class CleanupResultItem(BaseCamelCaseModel):
    """クリーンアップ結果アイテム。"""

    target_type: str = Field(..., description="対象種別")
    deleted_count: int = Field(..., description="削除件数")
    freed_bytes: int = Field(..., description="解放サイズ（バイト）")


class CleanupExecuteResponse(BaseCamelCaseModel):
    """クリーンアップ実行レスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    results: list[CleanupResultItem] = Field(..., description="結果")
    total_deleted_count: int = Field(..., description="合計削除件数")
    total_freed_bytes: int = Field(..., description="合計解放サイズ")
    total_freed_display: str = Field(..., description="合計解放サイズ（表示用）")
    executed_at: datetime = Field(..., description="実行日時")


class OrphanFileResponse(BaseCamelCaseModel):
    """孤立ファイルレスポンス。"""

    id: uuid.UUID = Field(..., description="ファイルID")
    file_name: str = Field(..., description="ファイル名")
    file_path: str = Field(..., description="ファイルパス")
    size_bytes: int = Field(..., description="サイズ（バイト）")
    size_display: str = Field(..., description="サイズ（表示用）")
    mime_type: str | None = Field(default=None, description="MIMEタイプ")
    created_at: datetime = Field(..., description="作成日時")
    last_accessed_at: datetime | None = Field(default=None, description="最終アクセス日時")
    original_project_id: uuid.UUID | None = Field(default=None, description="元プロジェクトID")
    original_project_name: str | None = Field(default=None, description="元プロジェクト名")


class OrphanFileListResponse(BaseCamelCaseModel):
    """孤立ファイル一覧レスポンス。"""

    items: list[OrphanFileResponse] = Field(..., description="孤立ファイルリスト")
    total: int = Field(..., description="総件数")
    total_size_bytes: int = Field(..., description="合計サイズ（バイト）")
    total_size_display: str = Field(..., description="合計サイズ（表示用）")


class OrphanFileCleanupResponse(BaseCamelCaseModel):
    """孤立ファイルクリーンアップレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    deleted_count: int = Field(..., description="削除件数")
    freed_bytes: int = Field(..., description="解放サイズ（バイト）")
    freed_display: str = Field(..., description="解放サイズ（表示用）")


class RetentionPolicyResponse(BaseCamelCaseModel):
    """保持ポリシーレスポンス。"""

    activity_logs_days: int = Field(..., description="操作履歴保持期間")
    audit_logs_days: int = Field(..., description="監査ログ保持期間")
    deleted_projects_days: int = Field(..., description="削除プロジェクト保持期間")
    session_logs_days: int = Field(..., description="セッションログ保持期間")
```

---

### 2.11 サポートツールスキーマ（support_tools.py）

**対応ユースケース**: SA-041〜SA-043

```python
"""サポートツールスキーマ。

このモジュールは、サポートツールのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class ImpersonateRequest(BaseCamelCaseModel):
    """ユーザー代行開始リクエストスキーマ。"""

    reason: str = Field(..., min_length=1, max_length=500, description="代行理由")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class ImpersonateUserInfo(BaseCamelCaseModel):
    """代行対象ユーザー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")


class ImpersonateResponse(BaseCamelCaseModel):
    """ユーザー代行レスポンス。"""

    impersonation_token: str = Field(..., description="代行トークン")
    target_user: ImpersonateUserInfo = Field(..., description="対象ユーザー")
    expires_at: datetime = Field(..., description="有効期限")


class ImpersonateEndResponse(BaseCamelCaseModel):
    """ユーザー代行終了レスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    message: str = Field(..., description="メッセージ")


class DebugModeResponse(BaseCamelCaseModel):
    """デバッグモードレスポンス。"""

    enabled: bool = Field(..., description="デバッグモード状態")
    message: str = Field(..., description="メッセージ")
```

---

### 2.12 ヘルスチェックスキーマ（health_check.py）

**対応ユースケース**: SA-043

```python
"""ヘルスチェックスキーマ。

このモジュールは、ヘルスチェックのレスポンススキーマを定義します。
システム管理者向けの詳細なシステム状態情報を提供します。
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# Enum定義
# ================================================================================


class HealthStatus(StrEnum):
    """ヘルスステータス。"""

    HEALTHY = "healthy"      # 正常
    DEGRADED = "degraded"    # 一部問題あり（動作可能）
    UNHEALTHY = "unhealthy"  # 異常


# ================================================================================
# サブスキーマ
# ================================================================================


class HealthCheckItem(BaseCamelCaseModel):
    """ヘルスチェック項目。

    各コンポーネントのヘルス状態を表します。

    Attributes:
        status: ステータス（healthy/unhealthy/degraded）
        response_time_ms: レスポンス時間（ミリ秒）
        message: 状態説明メッセージ
        details: 詳細情報（コンポーネント固有の情報）
        last_checked_at: 最終チェック日時
    """

    status: HealthStatus = Field(..., description="ステータス")
    response_time_ms: int = Field(..., description="レスポンス時間（ミリ秒）")
    message: str | None = Field(default=None, description="状態説明メッセージ")
    details: dict[str, Any] | None = Field(default=None, description="詳細情報")
    last_checked_at: datetime = Field(..., description="最終チェック日時")


class DatabaseHealth(BaseCamelCaseModel):
    """データベースヘルス情報。

    PostgreSQLデータベースの詳細な状態を表します。
    """

    status: HealthStatus = Field(..., description="ステータス")
    response_time_ms: int = Field(..., description="接続レスポンス時間")
    active_connections: int = Field(..., description="アクティブ接続数")
    max_connections: int = Field(..., description="最大接続数")
    connection_usage_percent: float = Field(..., description="接続使用率（%）")
    database_size_bytes: int = Field(..., description="データベースサイズ（バイト）")
    database_size_display: str = Field(..., description="データベースサイズ（表示用）")
    oldest_transaction_age_seconds: int | None = Field(
        default=None, description="最古トランザクション経過時間（秒）"
    )
    replication_lag_seconds: float | None = Field(
        default=None, description="レプリケーション遅延（秒）"
    )


class CacheHealth(BaseCamelCaseModel):
    """キャッシュ（Redis）ヘルス情報。"""

    status: HealthStatus = Field(..., description="ステータス")
    response_time_ms: int = Field(..., description="接続レスポンス時間")
    used_memory_bytes: int = Field(..., description="使用メモリ（バイト）")
    used_memory_display: str = Field(..., description="使用メモリ（表示用）")
    max_memory_bytes: int = Field(..., description="最大メモリ（バイト）")
    memory_usage_percent: float = Field(..., description="メモリ使用率（%）")
    connected_clients: int = Field(..., description="接続クライアント数")
    hit_rate_percent: float = Field(..., description="キャッシュヒット率（%）")


class StorageHealth(BaseCamelCaseModel):
    """ストレージヘルス情報。"""

    status: HealthStatus = Field(..., description="ステータス")
    total_bytes: int = Field(..., description="総容量（バイト）")
    used_bytes: int = Field(..., description="使用量（バイト）")
    available_bytes: int = Field(..., description="空き容量（バイト）")
    usage_percent: float = Field(..., description="使用率（%）")
    total_display: str = Field(..., description="総容量（表示用）")
    used_display: str = Field(..., description="使用量（表示用）")
    available_display: str = Field(..., description="空き容量（表示用）")


class ExternalApiHealth(BaseCamelCaseModel):
    """外部APIヘルス情報。"""

    azure_ad: HealthCheckItem | None = Field(default=None, description="Azure AD認証")
    openai: HealthCheckItem | None = Field(default=None, description="OpenAI API")


class SystemResourceHealth(BaseCamelCaseModel):
    """システムリソースヘルス情報。

    サーバーのCPU、メモリ等のリソース状態を表します。
    """

    cpu_usage_percent: float = Field(..., description="CPU使用率（%）")
    memory_usage_percent: float = Field(..., description="メモリ使用率（%）")
    memory_used_bytes: int = Field(..., description="使用メモリ（バイト）")
    memory_total_bytes: int = Field(..., description="総メモリ（バイト）")
    disk_usage_percent: float = Field(..., description="ディスク使用率（%）")
    load_average_1m: float | None = Field(default=None, description="ロードアベレージ（1分）")
    load_average_5m: float | None = Field(default=None, description="ロードアベレージ（5分）")
    load_average_15m: float | None = Field(default=None, description="ロードアベレージ（15分）")
    uptime_seconds: int = Field(..., description="稼働時間（秒）")
    uptime_display: str = Field(..., description="稼働時間（表示用）")


class ApplicationHealth(BaseCamelCaseModel):
    """アプリケーションヘルス情報。"""

    version: str = Field(..., description="アプリケーションバージョン")
    environment: str = Field(..., description="実行環境（development/staging/production）")
    active_workers: int = Field(..., description="アクティブワーカー数")
    pending_tasks: int = Field(..., description="待機中タスク数")
    error_rate_percent: float = Field(..., description="直近1時間のエラー率（%）")
    avg_response_time_ms: float = Field(..., description="平均レスポンス時間（ミリ秒）")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class HealthCheckSimpleResponse(BaseCamelCaseModel):
    """簡易ヘルスチェックレスポンス。

    ロードバランサーやモニタリングツール向けのシンプルなレスポンス。
    /health エンドポイントで使用します。

    Example:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """

    status: HealthStatus = Field(..., description="全体ステータス")
    timestamp: datetime = Field(..., description="チェック日時")


class HealthCheckDetailedResponse(BaseCamelCaseModel):
    """詳細ヘルスチェックレスポンス。

    システム管理者向けの詳細なヘルス情報。
    /admin/health/detailed エンドポイントで使用します。

    Attributes:
        status: 全体ステータス
        timestamp: チェック日時
        database: データベースヘルス
        cache: キャッシュ（Redis）ヘルス
        storage: ストレージヘルス
        external_apis: 外部APIヘルス
        system_resources: システムリソースヘルス
        application: アプリケーションヘルス
        checks: 個別チェック結果（後方互換性のため維持）

    Example:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "database": {
                "status": "healthy",
                "responseTimeMs": 5,
                "activeConnections": 10,
                "maxConnections": 100,
                ...
            },
            ...
        }
    """

    status: HealthStatus = Field(..., description="全体ステータス")
    timestamp: datetime = Field(..., description="チェック日時")

    # 詳細情報
    database: DatabaseHealth = Field(..., description="データベースヘルス")
    cache: CacheHealth | None = Field(default=None, description="キャッシュヘルス")
    storage: StorageHealth = Field(..., description="ストレージヘルス")
    external_apis: ExternalApiHealth = Field(..., description="外部APIヘルス")
    system_resources: SystemResourceHealth = Field(..., description="システムリソースヘルス")
    application: ApplicationHealth = Field(..., description="アプリケーションヘルス")

    # 後方互換性のための個別チェック結果
    checks: dict[str, HealthCheckItem] = Field(
        default_factory=dict, description="個別チェック結果"
    )


class HealthCheckHistoryItem(BaseCamelCaseModel):
    """ヘルスチェック履歴アイテム。"""

    timestamp: datetime = Field(..., description="チェック日時")
    status: HealthStatus = Field(..., description="ステータス")
    response_time_ms: int = Field(..., description="レスポンス時間")
    failed_components: list[str] = Field(
        default_factory=list, description="障害コンポーネント"
    )


class HealthCheckHistoryResponse(BaseCamelCaseModel):
    """ヘルスチェック履歴レスポンス。

    直近のヘルスチェック結果の履歴を返します。
    """

    items: list[HealthCheckHistoryItem] = Field(..., description="履歴アイテム")
    total: int = Field(..., description="総件数")
    uptime_percent_24h: float = Field(..., description="24時間稼働率（%）")
    uptime_percent_7d: float = Field(..., description="7日間稼働率（%）")
    uptime_percent_30d: float = Field(..., description="30日間稼働率（%）")
```

---

### 2.13 管理者用プロジェクトスキーマ（project_admin.py）

**対応ユースケース**: SA-007〜SA-011

```python
"""管理者用プロジェクトスキーマ。

このモジュールは、管理者向けプロジェクト管理のスキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# フィルタスキーマ
# ================================================================================


class AdminProjectFilter(BaseCamelCaseModel):
    """管理者用プロジェクトフィルタスキーマ。"""

    status: str | None = Field(default=None, description="ステータス")
    owner_id: uuid.UUID | None = Field(default=None, description="オーナーID")
    inactive_days: int | None = Field(default=None, ge=1, description="非アクティブ日数")
    search: str | None = Field(default=None, description="検索キーワード")
    sort_by: str | None = Field(default=None, description="ソート項目")
    sort_order: str | None = Field(default="desc", description="ソート順")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class ProjectOwnerInfo(BaseCamelCaseModel):
    """プロジェクトオーナー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")


class AdminProjectResponse(BaseCamelCaseORMModel):
    """管理者用プロジェクトレスポンス。"""

    id: uuid.UUID = Field(..., description="プロジェクトID")
    name: str = Field(..., description="プロジェクト名")
    owner: ProjectOwnerInfo = Field(..., description="オーナー情報")
    status: str = Field(..., description="ステータス")
    member_count: int = Field(..., description="メンバー数")
    storage_used_bytes: int = Field(..., description="ストレージ使用量（バイト）")
    storage_used_display: str = Field(..., description="ストレージ使用量（表示用）")
    last_activity_at: datetime | None = Field(default=None, description="最終アクティビティ")
    created_at: datetime = Field(..., description="作成日時")


class AdminProjectStatistics(BaseCamelCaseModel):
    """管理者用プロジェクト統計。"""

    total_projects: int = Field(..., description="総プロジェクト数")
    active_projects: int = Field(..., description="アクティブ数")
    archived_projects: int = Field(..., description="アーカイブ数")
    deleted_projects: int = Field(..., description="削除済み数")
    total_storage_bytes: int = Field(..., description="総ストレージ使用量（バイト）")
    total_storage_display: str = Field(..., description="総ストレージ使用量（表示用）")


class AdminProjectListResponse(BaseCamelCaseModel):
    """管理者用プロジェクト一覧レスポンス。"""

    items: list[AdminProjectResponse] = Field(..., description="プロジェクトリスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    limit: int = Field(..., description="取得件数")
    statistics: AdminProjectStatistics = Field(..., description="統計情報")


class ProjectStorageResponse(BaseCamelCaseModel):
    """プロジェクトストレージ使用量レスポンス。"""

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    project_name: str = Field(..., description="プロジェクト名")
    storage_used_bytes: int = Field(..., description="ストレージ使用量（バイト）")
    storage_used_display: str = Field(..., description="ストレージ使用量（表示用）")
    file_count: int = Field(..., description="ファイル数")


class ProjectStorageListResponse(BaseCamelCaseModel):
    """プロジェクトストレージ一覧レスポンス。"""

    items: list[ProjectStorageResponse] = Field(..., description="ストレージ使用量リスト")
    total_storage_bytes: int = Field(..., description="合計ストレージ使用量（バイト）")
    total_storage_display: str = Field(..., description="合計ストレージ使用量（表示用）")
```

---

## 3. __init__.py ファイル

### 3.1 admin/__init__.py

```python
"""システム管理スキーマ。"""

from app.schemas.admin.activity_log import (
    ActivityLogDetailResponse,
    ActivityLogFilter,
    ActivityLogListResponse,
    ActivityLogResponse,
)
from app.schemas.admin.announcement import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.schemas.admin.audit_log import (
    AuditLogExportFilter,
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogResponse,
)
from app.schemas.admin.bulk_operation import (
    BulkArchiveResponse,
    BulkDeactivateResponse,
    BulkImportResponse,
    BulkProjectArchiveRequest,
    BulkUserDeactivateRequest,
    UserExportFilter,
)
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
from app.schemas.admin.health_check import (
    HealthCheckDetailedResponse,
    HealthCheckSimpleResponse,
)
from app.schemas.admin.notification_template import (
    NotificationTemplateCreate,
    NotificationTemplateListResponse,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
)
from app.schemas.admin.project_admin import (
    AdminProjectFilter,
    AdminProjectListResponse,
    AdminProjectResponse,
    ProjectStorageListResponse,
)
from app.schemas.admin.session_management import (
    SessionFilter,
    SessionListResponse,
    SessionResponse,
    SessionTerminateRequest,
)
from app.schemas.admin.statistics import (
    ApiStatisticsDetailResponse,
    ErrorStatisticsDetailResponse,
    StatisticsOverviewResponse,
    StorageStatisticsDetailResponse,
    UserStatisticsDetailResponse,
)
from app.schemas.admin.support_tools import (
    DebugModeResponse,
    ImpersonateEndResponse,
    ImpersonateRequest,
    ImpersonateResponse,
)
from app.schemas.admin.system_alert import (
    SystemAlertCreate,
    SystemAlertListResponse,
    SystemAlertResponse,
    SystemAlertUpdate,
)
from app.schemas.admin.system_setting import (
    MaintenanceModeEnable,
    MaintenanceModeResponse,
    SystemSettingsByCategoryResponse,
    SystemSettingUpdate,
)

__all__ = [
    # Activity Log
    "ActivityLogFilter",
    "ActivityLogResponse",
    "ActivityLogDetailResponse",
    "ActivityLogListResponse",
    # Audit Log
    "AuditLogFilter",
    "AuditLogExportFilter",
    "AuditLogResponse",
    "AuditLogListResponse",
    # System Setting
    "SystemSettingUpdate",
    "SystemSettingsByCategoryResponse",
    "MaintenanceModeEnable",
    "MaintenanceModeResponse",
    # Statistics
    "StatisticsOverviewResponse",
    "UserStatisticsDetailResponse",
    "StorageStatisticsDetailResponse",
    "ApiStatisticsDetailResponse",
    "ErrorStatisticsDetailResponse",
    # Bulk Operation
    "BulkUserDeactivateRequest",
    "BulkProjectArchiveRequest",
    "UserExportFilter",
    "BulkImportResponse",
    "BulkDeactivateResponse",
    "BulkArchiveResponse",
    # Announcement
    "AnnouncementCreate",
    "AnnouncementUpdate",
    "AnnouncementResponse",
    "AnnouncementListResponse",
    # Notification Template
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "NotificationTemplateListResponse",
    # System Alert
    "SystemAlertCreate",
    "SystemAlertUpdate",
    "SystemAlertResponse",
    "SystemAlertListResponse",
    # Session Management
    "SessionFilter",
    "SessionTerminateRequest",
    "SessionResponse",
    "SessionListResponse",
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
    # Support Tools
    "ImpersonateRequest",
    "ImpersonateResponse",
    "ImpersonateEndResponse",
    "DebugModeResponse",
    # Health Check
    "HealthCheckSimpleResponse",
    "HealthCheckDetailedResponse",
    # Project Admin
    "AdminProjectFilter",
    "AdminProjectResponse",
    "AdminProjectListResponse",
    "ProjectStorageListResponse",
]
```

---

## 4. 注意事項

### 4.1 命名規則

- Filter: クエリパラメータ用スキーマ
- Create: POST リクエストボディ用スキーマ
- Update: PATCH リクエストボディ用スキーマ
- Response: レスポンス用スキーマ
- ListResponse: 一覧レスポンス用スキーマ（items + total + page情報）

### 4.2 バリデーション

- `Field()` で `min_length`, `max_length`, `ge`, `le` を適切に設定
- 必須フィールドは `...` で指定、オプションは `default=None` または `default_factory`
- 日時フィールドは `datetime` 型（タイムゾーン情報あり）

### 4.3 camelCase変換

- フロントエンドとの通信は自動的にcamelCaseに変換される
- Python内部ではsnake_caseで処理

---

## 5. エラーレスポンス標準化

### 5.1 共通エラーレスポンススキーマ

全APIエンドポイントで統一されたエラーレスポンス形式を使用します。

**ファイル**: `src/app/schemas/common/error.py`

```python
"""共通エラーレスポンススキーマ。

このモジュールは、全APIで使用する標準エラーレスポンスを定義します。
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


class ErrorDetail(BaseCamelCaseModel):
    """エラー詳細情報。

    Attributes:
        field (str | None): エラーが発生したフィールド名
        message (str): エラーメッセージ
        code (str | None): エラーコード
    """

    field: str | None = Field(default=None, description="エラーが発生したフィールド名")
    message: str = Field(..., description="エラーメッセージ")
    code: str | None = Field(default=None, description="エラーコード")


class ErrorResponse(BaseCamelCaseModel):
    """標準エラーレスポンススキーマ。

    全APIエンドポイントで統一されたエラーレスポンス形式。

    Attributes:
        error (str): エラー種別（NotFound, ValidationError, AuthorizationError等）
        message (str): ユーザー向けエラーメッセージ
        details (list[ErrorDetail] | None): 詳細エラー情報（バリデーションエラー等）
        request_id (str | None): リクエストID（トレーシング用）
        timestamp (datetime): エラー発生日時

    Example:
        {
            "error": "ValidationError",
            "message": "入力値が不正です",
            "details": [
                {"field": "email", "message": "メールアドレスの形式が不正です", "code": "INVALID_FORMAT"}
            ],
            "requestId": "req-123456",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """

    error: str = Field(..., description="エラー種別")
    message: str = Field(..., description="ユーザー向けエラーメッセージ")
    details: list[ErrorDetail] | None = Field(default=None, description="詳細エラー情報")
    request_id: str | None = Field(default=None, description="リクエストID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="エラー発生日時")


class NotFoundErrorResponse(ErrorResponse):
    """リソース未発見エラーレスポンス。

    HTTP 404 エラー用のレスポンス。
    """

    error: str = Field(default="NotFound", description="エラー種別")


class ValidationErrorResponse(ErrorResponse):
    """バリデーションエラーレスポンス。

    HTTP 400/422 エラー用のレスポンス。
    """

    error: str = Field(default="ValidationError", description="エラー種別")


class AuthorizationErrorResponse(ErrorResponse):
    """認可エラーレスポンス。

    HTTP 403 エラー用のレスポンス。
    """

    error: str = Field(default="AuthorizationError", description="エラー種別")


class AuthenticationErrorResponse(ErrorResponse):
    """認証エラーレスポンス。

    HTTP 401 エラー用のレスポンス。
    """

    error: str = Field(default="AuthenticationError", description="エラー種別")


class ConflictErrorResponse(ErrorResponse):
    """競合エラーレスポンス。

    HTTP 409 エラー用のレスポンス。
    """

    error: str = Field(default="ConflictError", description="エラー種別")


class InternalErrorResponse(ErrorResponse):
    """内部エラーレスポンス。

    HTTP 500 エラー用のレスポンス。
    """

    error: str = Field(default="InternalError", description="エラー種別")
    message: str = Field(
        default="サーバー内部でエラーが発生しました",
        description="ユーザー向けエラーメッセージ",
    )
```

### 5.2 エラーレスポンスの使用例

```python
# APIルートでの使用例
from fastapi import APIRouter, HTTPException, status
from app.schemas.common.error import ErrorResponse, NotFoundErrorResponse

router = APIRouter()


@router.get(
    "/{user_id}",
    responses={
        404: {"model": NotFoundErrorResponse, "description": "ユーザーが見つかりません"},
        403: {"model": ErrorResponse, "description": "アクセス権限がありません"},
    },
)
async def get_user(user_id: uuid.UUID) -> UserResponse:
    ...
```

### 5.3 エラーコード一覧

| エラーコード | 説明 | HTTPステータス |
|-------------|------|---------------|
| `NOT_FOUND` | リソースが見つからない | 404 |
| `VALIDATION_ERROR` | 入力値が不正 | 400/422 |
| `AUTHENTICATION_ERROR` | 認証に失敗 | 401 |
| `AUTHORIZATION_ERROR` | 権限がない | 403 |
| `CONFLICT_ERROR` | 競合が発生 | 409 |
| `INTERNAL_ERROR` | サーバー内部エラー | 500 |
| `INVALID_FORMAT` | フォーマットが不正 | 400 |
| `REQUIRED_FIELD` | 必須フィールドが未入力 | 400 |
| `MAX_LENGTH_EXCEEDED` | 最大長を超過 | 400 |
| `DUPLICATE_ENTRY` | 重複エントリ | 409 |
| `RESOURCE_IN_USE` | リソースが使用中 | 409 |
