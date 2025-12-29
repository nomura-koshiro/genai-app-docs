"""ダッシュボードスキーマ。

このモジュールは、ダッシュボードAPIのスキーマを定義します。
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# 統計情報スキーマ
# ================================================================================
class ProjectStats(BaseCamelCaseModel):
    """プロジェクト統計。

    Attributes:
        total: 総プロジェクト数
        active: アクティブなプロジェクト数
        archived: アーカイブされたプロジェクト数
    """

    total: int = Field(..., description="総プロジェクト数")
    active: int = Field(..., description="アクティブなプロジェクト数")
    archived: int = Field(..., description="アーカイブされたプロジェクト数")


class SessionStats(BaseCamelCaseModel):
    """セッション統計。

    Attributes:
        total: 総セッション数
        draft: 下書きセッション数
        active: アクティブセッション数
        completed: 完了セッション数
    """

    total: int = Field(..., description="総セッション数")
    draft: int = Field(default=0, description="下書きセッション数")
    active: int = Field(default=0, description="アクティブセッション数")
    completed: int = Field(default=0, description="完了セッション数")


class TreeStats(BaseCamelCaseModel):
    """ツリー統計。

    Attributes:
        total: 総ツリー数
        draft: 下書きツリー数
        active: アクティブツリー数
        completed: 完了ツリー数
    """

    total: int = Field(..., description="総ツリー数")
    draft: int = Field(default=0, description="下書きツリー数")
    active: int = Field(default=0, description="アクティブツリー数")
    completed: int = Field(default=0, description="完了ツリー数")


class UserStats(BaseCamelCaseModel):
    """ユーザー統計。

    Attributes:
        total: 総ユーザー数
        active: アクティブユーザー数
    """

    total: int = Field(..., description="総ユーザー数")
    active: int = Field(..., description="アクティブユーザー数")


class FileStats(BaseCamelCaseModel):
    """ファイル統計。

    Attributes:
        total: 総ファイル数
        total_size_bytes: 総ファイルサイズ（バイト）
    """

    total: int = Field(..., description="総ファイル数")
    total_size_bytes: int = Field(default=0, description="総ファイルサイズ（バイト）")


class DashboardStatsResponse(BaseCamelCaseModel):
    """ダッシュボード統計レスポンス。

    Attributes:
        projects: プロジェクト統計
        sessions: セッション統計
        trees: ツリー統計
        users: ユーザー統計
        files: ファイル統計
        generated_at: 統計生成日時
    """

    projects: ProjectStats = Field(..., description="プロジェクト統計")
    sessions: SessionStats = Field(..., description="セッション統計")
    trees: TreeStats = Field(..., description="ツリー統計")
    users: UserStats = Field(..., description="ユーザー統計")
    files: FileStats = Field(..., description="ファイル統計")
    generated_at: datetime = Field(..., description="統計生成日時")


# ================================================================================
# アクティビティログスキーマ
# ================================================================================
class ActivityLogResponse(BaseCamelCaseModel):
    """アクティビティログレスポンス。

    Attributes:
        id: アクティビティID
        user_id: ユーザーID
        user_name: ユーザー名
        action: アクション（created/updated/deleted/accessed）
        resource_type: リソースタイプ（project/session/tree/file）
        resource_id: リソースID
        resource_name: リソース名
        details: 詳細情報
        created_at: 作成日時
    """

    id: uuid.UUID = Field(..., description="アクティビティID")
    user_id: uuid.UUID = Field(..., description="ユーザーID")
    user_name: str = Field(..., description="ユーザー名")
    action: str = Field(..., description="アクション（created/updated/deleted/accessed）")
    resource_type: str = Field(..., description="リソースタイプ（project/session/tree/file）")
    resource_id: uuid.UUID = Field(..., description="リソースID")
    resource_name: str = Field(..., description="リソース名")
    details: dict[str, Any] | None = Field(default=None, description="詳細情報")
    created_at: datetime = Field(..., description="作成日時")


class DashboardActivitiesResponse(BaseCamelCaseModel):
    """ダッシュボードアクティビティレスポンス。

    Attributes:
        activities: アクティビティリスト
        total: 総件数
        skip: スキップ数
        limit: 取得件数
    """

    activities: list[ActivityLogResponse] = Field(default=[], description="アクティビティリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")


# ================================================================================
# チャートデータスキーマ
# ================================================================================
class ChartDataPoint(BaseCamelCaseModel):
    """チャートデータポイント。

    Attributes:
        label: ラベル
        value: 値
    """

    label: str = Field(..., description="ラベル")
    value: float = Field(..., description="値")


class ChartDataResponse(BaseCamelCaseModel):
    """チャートデータレスポンス。

    Attributes:
        chart_type: チャートタイプ（line/bar/pie/area）
        title: チャートタイトル
        data: データポイントリスト
        x_axis_label: X軸ラベル
        y_axis_label: Y軸ラベル
    """

    chart_type: str = Field(..., description="チャートタイプ（line/bar/pie/area）")
    title: str = Field(..., description="チャートタイトル")
    data: list[ChartDataPoint] = Field(default=[], description="データポイントリスト")
    x_axis_label: str | None = Field(default=None, description="X軸ラベル")
    y_axis_label: str | None = Field(default=None, description="Y軸ラベル")


class DashboardChartsResponse(BaseCamelCaseModel):
    """ダッシュボードチャートレスポンス。

    Attributes:
        session_trend: セッション作成トレンド
        tree_trend: ツリー作成トレンド
        project_distribution: プロジェクト状態分布
        user_activity: ユーザーアクティビティ
        generated_at: 統計生成日時
    """

    session_trend: ChartDataResponse = Field(..., description="セッション作成トレンド")
    tree_trend: ChartDataResponse = Field(..., description="ツリー作成トレンド")
    project_distribution: ChartDataResponse = Field(..., description="プロジェクト状態分布")
    user_activity: ChartDataResponse = Field(..., description="ユーザーアクティビティ")
    generated_at: datetime = Field(..., description="統計生成日時")
