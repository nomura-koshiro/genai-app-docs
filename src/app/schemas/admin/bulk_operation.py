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
    errors: list[ImportErrorDetail] = Field(
        default_factory=list, description="エラー一覧"
    )


class BulkDeactivatePreviewItem(BaseCamelCaseModel):
    """無効化プレビューアイテム。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: str = Field(..., description="メールアドレス")
    last_activity_at: datetime | None = Field(
        default=None, description="最終アクティビティ"
    )


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
    last_activity_at: datetime | None = Field(
        default=None, description="最終アクティビティ"
    )


class BulkArchiveResponse(BaseCamelCaseModel):
    """一括アーカイブレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    archived_count: int = Field(..., description="アーカイブ件数")
    preview_items: list[BulkArchivePreviewItem] | None = Field(
        default=None, description="プレビューアイテム（dry_run時のみ）"
    )
