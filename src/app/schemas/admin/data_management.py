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

    file_ids: list[uuid.UUID] | None = Field(
        default=None, description="削除するファイルID"
    )
    delete_all: bool = Field(default=False, description="全件削除")


class RetentionPolicyUpdate(BaseCamelCaseModel):
    """保持ポリシー更新リクエストスキーマ。"""

    activity_logs_days: int | None = Field(
        default=None, ge=1, description="操作履歴保持期間"
    )
    audit_logs_days: int | None = Field(
        default=None, ge=1, description="監査ログ保持期間"
    )
    deleted_projects_days: int | None = Field(
        default=None, ge=1, description="削除プロジェクト保持期間"
    )
    session_logs_days: int | None = Field(
        default=None, ge=1, description="セッションログ保持期間"
    )


# ================================================================================
# レスポンススキーマ
# ================================================================================


class CleanupPreviewItem(BaseCamelCaseModel):
    """クリーンアッププレビューアイテム。"""

    target_type: str = Field(..., description="対象種別")
    target_type_display: str = Field(..., description="対象種別（表示用）")
    record_count: int = Field(..., description="レコード数")
    oldest_record_at: datetime | None = Field(
        default=None, description="最古レコード日時"
    )
    newest_record_at: datetime | None = Field(
        default=None, description="最新レコード日時"
    )
    estimated_size_bytes: int = Field(..., description="推定サイズ（バイト）")
    estimated_size_display: str = Field(..., description="推定サイズ（表示用）")


class CleanupPreviewResponse(BaseCamelCaseModel):
    """クリーンアッププレビューレスポンス。"""

    preview: list[CleanupPreviewItem] = Field(..., description="プレビュー")
    total_record_count: int = Field(..., description="合計レコード数")
    total_estimated_size_bytes: int = Field(..., description="合計推定サイズ")
    total_estimated_size_display: str = Field(
        ..., description="合計推定サイズ（表示用）"
    )
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
    last_accessed_at: datetime | None = Field(
        default=None, description="最終アクセス日時"
    )
    original_project_id: uuid.UUID | None = Field(
        default=None, description="元プロジェクトID"
    )
    original_project_name: str | None = Field(
        default=None, description="元プロジェクト名"
    )


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
