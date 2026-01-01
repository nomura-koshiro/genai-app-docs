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


class BulkImportResult(BaseCamelCaseModel):
    """一括インポート結果（内部処理用）。"""

    row: int = Field(..., description="行番号")
    email: str = Field(..., description="メールアドレス")
    success: bool = Field(..., description="成功フラグ")
    message: str | None = Field(default=None, description="メッセージ")


class BulkImportResponse(BaseCamelCaseModel):
    """一括インポートレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    imported_count: int = Field(..., description="インポート件数")
    error_count: int = Field(default=0, description="エラー件数")
    operation_id: uuid.UUID = Field(..., description="操作ID")
    results: list[BulkImportResult] = Field(default_factory=list, description="結果一覧")
    errors: list[str] | None = Field(default=None, description="エラーメッセージ一覧")


class BulkDeactivatePreviewItem(BaseCamelCaseModel):
    """無効化プレビューアイテム。"""

    user_id: uuid.UUID = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    display_name: str = Field(..., description="表示名")
    last_activity_at: datetime | None = Field(default=None, description="最終アクティビティ")


class BulkDeactivateResponse(BaseCamelCaseModel):
    """一括無効化レスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    deactivated_count: int = Field(..., description="無効化件数")
    operation_id: uuid.UUID = Field(..., description="操作ID")
    preview_items: list[BulkDeactivatePreviewItem] | None = Field(default=None, description="プレビューアイテム（dry_run時のみ）")


class BulkArchivePreviewItem(BaseCamelCaseModel):
    """アーカイブプレビューアイテム。"""

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    name: str = Field(..., description="プロジェクト名")
    last_updated_at: datetime | None = Field(default=None, description="最終更新日時")


class BulkArchiveResponse(BaseCamelCaseModel):
    """一括アーカイブレスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    archived_count: int = Field(..., description="アーカイブ件数")
    operation_id: uuid.UUID = Field(..., description="操作ID")
    preview_items: list[BulkArchivePreviewItem] | None = Field(default=None, description="プレビューアイテム（dry_run時のみ）")
