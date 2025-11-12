"""セッションとメッセージ関連のスキーマ。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SampleMessageResponse(BaseModel):
    """メッセージレスポンススキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    role: str = Field(..., description="メッセージの役割（user/assistant/system）")
    content: str = Field(..., description="メッセージの内容")
    timestamp: datetime = Field(..., description="メッセージ作成日時")


class SampleSessionResponse(BaseModel):
    """セッションレスポンススキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(..., description="セッション識別子")
    created_at: datetime = Field(..., description="セッション作成日時")
    updated_at: datetime = Field(..., description="最終更新日時")
    messages: list[SampleMessageResponse] = Field(..., description="メッセージのリスト")
    metadata: dict | None = Field(default=None, description="セッションのメタデータ")


class SampleSessionListResponse(BaseModel):
    """セッション一覧レスポンススキーマ。"""

    sessions: list[SampleSessionResponse] = Field(..., description="セッションのリスト")
    total: int = Field(..., description="総セッション数")


class SampleSessionCreateRequest(BaseModel):
    """セッション作成リクエストスキーマ。"""

    metadata: dict | None = Field(default=None, description="セッションのメタデータ")


class SampleSessionUpdateRequest(BaseModel):
    """セッション更新リクエストスキーマ。"""

    metadata: dict | None = Field(default=None, description="更新するメタデータ")


class SampleDeleteResponse(BaseModel):
    """削除レスポンススキーマ。"""

    message: str = Field(..., description="削除成功メッセージ")
