"""AIエージェント/チャット関連のスキーマ。"""

from pydantic import BaseModel, Field


class SampleChatRequest(BaseModel):
    """チャットリクエストスキーマ。"""

    message: str = Field(..., min_length=1, max_length=10000, description="ユーザーメッセージ")
    session_id: str | None = Field(None, description="セッション識別子（新規の場合は省略）")
    context: dict | None = Field(None, description="追加コンテキスト情報")


class SampleChatResponse(BaseModel):
    """チャットレスポンススキーマ。"""

    response: str = Field(..., description="エージェントの応答メッセージ")
    session_id: str = Field(..., description="セッション識別子")
    tokens_used: int | None = Field(None, description="使用されたトークン数")
    model: str | None = Field(None, description="使用されたモデル名")
