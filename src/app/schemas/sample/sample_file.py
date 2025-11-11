"""ファイル関連のスキーマ。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SampleFileUploadResponse(BaseModel):
    """ファイルアップロードレスポンススキーマ。"""

    file_id: str = Field(..., description="一意のファイル識別子")
    filename: str = Field(..., description="元のファイル名")
    size: int = Field(..., description="ファイルサイズ（バイト）")
    content_type: str = Field(..., description="ファイルのMIMEタイプ")
    message: str = Field(..., description="アップロード成功メッセージ")


class SampleFileResponse(BaseModel):
    """ファイル情報レスポンススキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    file_id: str = Field(..., description="ファイル識別子")
    filename: str = Field(..., description="ファイル名")
    size: int = Field(..., description="ファイルサイズ（バイト）")
    content_type: str = Field(..., description="ファイルのMIMEタイプ")
    created_at: datetime = Field(..., description="アップロード日時")


class SampleFileListResponse(BaseModel):
    """ファイル一覧レスポンススキーマ。"""

    files: list[SampleFileResponse] = Field(..., description="ファイルのリスト")
    total: int = Field(..., description="総ファイル数")


class SampleFileDeleteResponse(BaseModel):
    """ファイル削除レスポンススキーマ。"""

    file_id: str = Field(..., description="削除されたファイルのID")
    message: str = Field(..., description="削除成功メッセージ")
