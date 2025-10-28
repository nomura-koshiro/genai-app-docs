"""APIリクエスト/レスポンス検証のためのPydanticスキーマ。"""

from app.schemas.common import ErrorResponse, HealthResponse, MessageResponse
from app.schemas.sample_agents import (
    SampleChatRequest,
    SampleChatResponse,
)
from app.schemas.sample_file import (
    SampleFileDeleteResponse,
    SampleFileListResponse,
    SampleFileResponse,
    SampleFileUploadResponse,
)
from app.schemas.sample_sessions import (
    SampleDeleteResponse,
    SampleMessageResponse,
    SampleSessionCreateRequest,
    SampleSessionListResponse,
    SampleSessionResponse,
    SampleSessionUpdateRequest,
)
from app.schemas.sample_user import (
    SampleToken,
    SampleUserCreate,
    SampleUserLogin,
    SampleUserResponse,
)

__all__ = [
    # 共通スキーマ
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    # ユーザースキーマ
    "SampleToken",
    "SampleUserCreate",
    "SampleUserLogin",
    "SampleUserResponse",
    # ファイルスキーマ
    "SampleFileUploadResponse",
    "SampleFileResponse",
    "SampleFileListResponse",
    "SampleFileDeleteResponse",
    # エージェント/チャットスキーマ
    "SampleChatRequest",
    "SampleChatResponse",
    # セッションスキーマ
    "SampleMessageResponse",
    "SampleSessionResponse",
    "SampleSessionListResponse",
    "SampleSessionCreateRequest",
    "SampleSessionUpdateRequest",
    "SampleDeleteResponse",
]
