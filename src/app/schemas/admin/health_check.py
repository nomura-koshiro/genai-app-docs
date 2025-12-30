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

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ================================================================================
# サブスキーマ
# ================================================================================


class HealthCheckItem(BaseCamelCaseModel):
    """ヘルスチェック項目。

    各コンポーネントのヘルス状態を表します。
    """

    status: HealthStatus = Field(..., description="ステータス")
    response_time_ms: int = Field(..., description="レスポンス時間（ミリ秒）")
    message: str | None = Field(default=None, description="状態説明メッセージ")
    details: dict[str, Any] | None = Field(default=None, description="詳細情報")
    last_checked_at: datetime = Field(..., description="最終チェック日時")


class DatabaseHealth(BaseCamelCaseModel):
    """データベースヘルス情報。"""

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
    """システムリソースヘルス情報。"""

    cpu_usage_percent: float = Field(..., description="CPU使用率（%）")
    memory_usage_percent: float = Field(..., description="メモリ使用率（%）")
    memory_used_bytes: int = Field(..., description="使用メモリ（バイト）")
    memory_total_bytes: int = Field(..., description="総メモリ（バイト）")
    disk_usage_percent: float = Field(..., description="ディスク使用率（%）")
    load_average_1m: float | None = Field(
        default=None, description="ロードアベレージ（1分）"
    )
    load_average_5m: float | None = Field(
        default=None, description="ロードアベレージ（5分）"
    )
    load_average_15m: float | None = Field(
        default=None, description="ロードアベレージ（15分）"
    )
    uptime_seconds: int = Field(..., description="稼働時間（秒）")
    uptime_display: str = Field(..., description="稼働時間（表示用）")


class ApplicationHealth(BaseCamelCaseModel):
    """アプリケーションヘルス情報。"""

    version: str = Field(..., description="アプリケーションバージョン")
    environment: str = Field(
        ..., description="実行環境（development/staging/production）"
    )
    active_workers: int = Field(..., description="アクティブワーカー数")
    pending_tasks: int = Field(..., description="待機中タスク数")
    error_rate_percent: float = Field(..., description="直近1時間のエラー率（%）")
    avg_response_time_ms: float = Field(..., description="平均レスポンス時間（ミリ秒）")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class HealthCheckSimpleResponse(BaseCamelCaseModel):
    """簡易ヘルスチェックレスポンス。"""

    status: HealthStatus = Field(..., description="全体ステータス")
    timestamp: datetime = Field(..., description="チェック日時")


class HealthCheckDetailedResponse(BaseCamelCaseModel):
    """詳細ヘルスチェックレスポンス。"""

    status: HealthStatus = Field(..., description="全体ステータス")
    timestamp: datetime = Field(..., description="チェック日時")

    database: DatabaseHealth = Field(..., description="データベースヘルス")
    cache: CacheHealth | None = Field(default=None, description="キャッシュヘルス")
    storage: StorageHealth = Field(..., description="ストレージヘルス")
    external_apis: ExternalApiHealth = Field(..., description="外部APIヘルス")
    system_resources: SystemResourceHealth = Field(
        ..., description="システムリソースヘルス"
    )
    application: ApplicationHealth = Field(..., description="アプリケーションヘルス")

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
    """ヘルスチェック履歴レスポンス。"""

    items: list[HealthCheckHistoryItem] = Field(..., description="履歴アイテム")
    total: int = Field(..., description="総件数")
    uptime_percent_24h: float = Field(..., description="24時間稼働率（%）")
    uptime_percent_7d: float = Field(..., description="7日間稼働率（%）")
    uptime_percent_30d: float = Field(..., description="30日間稼働率（%）")


# ================================================================================
# 互換性エイリアス
# ================================================================================


# サービス層で使用される名前のエイリアス
ComponentHealth = HealthCheckItem
HealthCheckResponse = HealthCheckSimpleResponse
HealthCheckDetailResponse = HealthCheckDetailedResponse
