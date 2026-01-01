"""システム統計スキーマ。

このモジュールは、システム統計情報のレスポンススキーマを定義します。
"""

import datetime

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

    date: datetime.date = Field(..., description="日付")
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
