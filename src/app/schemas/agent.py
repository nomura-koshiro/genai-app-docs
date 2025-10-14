"""エージェント関連のPydanticスキーマ."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """チャットリクエストスキーマ."""

    message: str = Field(..., min_length=1, max_length=10000, description="ユーザーメッセージ")
    session_id: str | None = Field(None, description="オプションのセッション識別子")
    context: dict[str, str] | None = Field(
        None, description="会話の追加コンテキスト"
    )


class ChatResponse(BaseModel):
    """チャットレスポンススキーマ."""

    response: str = Field(..., description="エージェントの応答メッセージ")
    session_id: str = Field(..., description="セッション識別子")
    tokens_used: int | None = Field(None, description="使用されたトークン数")
    model: str | None = Field(None, description="生成に使用されたモデル")


class Message(BaseModel):
    """会話内の個別メッセージ."""

    role: str = Field(..., description="メッセージロール (user/assistant/system)")
    content: str = Field(..., description="メッセージ内容")
    timestamp: datetime = Field(..., description="メッセージタイムスタンプ")


class SessionResponse(BaseModel):
    """セッション情報レスポンス."""

    session_id: str = Field(..., description="セッション識別子")
    created_at: datetime = Field(..., description="セッション作成時刻")
    updated_at: datetime = Field(..., description="最終更新時刻")
    messages: list[Message] = Field(default_factory=list, description="会話メッセージ")
    metadata: dict[str, str] | None = Field(None, description="セッションメタデータ")


class SessionCreate(BaseModel):
    """新規セッション作成."""

    metadata: dict[str, str] | None = Field(None, description="オプションのセッションメタデータ")


class SessionList(BaseModel):
    """セッションリスト."""

    sessions: list[SessionResponse] = Field(..., description="セッションのリスト")
    total: int = Field(..., ge=0, description="セッションの総数")
