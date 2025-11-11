"""サンプルAPIスキーマ。

このパッケージには、サンプルアプリケーション用のPydanticスキーマが含まれています。
APIリクエスト/レスポンスの検証とシリアライゼーションの参考実装として利用できます。

提供されるスキーマ:
    - sample_user: ユーザー関連（登録、ログイン、レスポンス）
    - sample_file: ファイル操作（アップロード、リスト、削除）
    - sample_sessions: セッション管理（作成、更新、メッセージ）
    - sample_agents: AIエージェント（チャットリクエスト/レスポンス）

使用例:
    >>> from app.schemas.sample import SampleUserCreate, SampleToken
    >>> from app.schemas.sample import SampleChatRequest, SampleChatResponse
    >>>
    >>> # ユーザー作成リクエスト
    >>> user_data = SampleUserCreate(email="user@example.com", password="...")
    >>>
    >>> # チャットリクエスト
    >>> chat_data = SampleChatRequest(message="Hello", session_id=...)

Note:
    これらはサンプル実装です。本番環境に適用する際は、
    プロジェクトの要件に合わせてカスタマイズしてください。
"""

from app.schemas.sample.sample_agents import SampleChatRequest, SampleChatResponse
from app.schemas.sample.sample_file import (
    SampleFileDeleteResponse,
    SampleFileListResponse,
    SampleFileResponse,
    SampleFileUploadResponse,
)
from app.schemas.sample.sample_sessions import (
    SampleDeleteResponse,
    SampleMessageResponse,
    SampleSessionCreateRequest,
    SampleSessionListResponse,
    SampleSessionResponse,
    SampleSessionUpdateRequest,
)
from app.schemas.sample.sample_user import (
    SampleToken,
    SampleUserCreate,
    SampleUserLogin,
    SampleUserResponse,
)

__all__ = [
    # ユーザースキーマ
    "SampleToken",
    "SampleUserCreate",
    "SampleUserLogin",
    "SampleUserResponse",
    # ファイルスキーマ
    "SampleFileDeleteResponse",
    "SampleFileListResponse",
    "SampleFileResponse",
    "SampleFileUploadResponse",
    # セッションスキーマ
    "SampleDeleteResponse",
    "SampleMessageResponse",
    "SampleSessionCreateRequest",
    "SampleSessionListResponse",
    "SampleSessionResponse",
    "SampleSessionUpdateRequest",
    # エージェントスキーマ
    "SampleChatRequest",
    "SampleChatResponse",
]
