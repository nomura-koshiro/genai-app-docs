"""ファイル関連のPydanticスキーマ."""

from datetime import datetime

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """ファイル情報スキーマ."""

    file_id: str = Field(..., description="一意のファイル識別子")
    filename: str = Field(..., description="元のファイル名")
    size: int = Field(..., ge=0, description="ファイルサイズ（バイト）")
    content_type: str | None = Field(None, description="ファイルのMIMEタイプ")
    created_at: datetime | None = Field(None, description="アップロード時刻")


class FileUploadResponse(BaseModel):
    """ファイルアップロードレスポンススキーマ."""

    file_id: str = Field(..., description="一意のファイル識別子")
    filename: str = Field(..., description="元のファイル名")
    size: int = Field(..., ge=0, description="ファイルサイズ（バイト）")
    content_type: str | None = Field(None, description="ファイルのMIMEタイプ")
    message: str = Field(..., description="成功メッセージ")


class FileListResponse(BaseModel):
    """ファイルリストレスポンススキーマ."""

    files: list[FileInfo] = Field(..., description="ファイルのリスト")
    total: int = Field(..., ge=0, description="ファイルの総数")


class FileDeleteResponse(BaseModel):
    """ファイル削除レスポンススキーマ."""

    file_id: str = Field(..., description="削除されたファイル識別子")
    message: str = Field(..., description="成功メッセージ")
