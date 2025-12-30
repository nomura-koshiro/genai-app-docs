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
    last_activity_at: datetime | None = Field(
        default=None, description="最終アクティビティ"
    )
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

    items: list[ProjectStorageResponse] = Field(
        ..., description="ストレージ使用量リスト"
    )
    total_storage_bytes: int = Field(..., description="合計ストレージ使用量（バイト）")
    total_storage_display: str = Field(
        ..., description="合計ストレージ使用量（表示用）"
    )
