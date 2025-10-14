"""エージェントAPIルート。"""

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUserOptionalDep, SessionServiceDep
from app.schemas.agent import ChatRequest, ChatResponse, SessionResponse
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="AIエージェントとチャット",
    description="AIエージェントとの会話を行います。新しい会話を開始するか、既存のセッションを継続できます。",
    response_description="エージェントからの応答とセッション情報",
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
                        "response": "こんにちは！何かお手伝いできることはありますか？",
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            },
        },
        404: {
            "description": "セッションが見つかりません",
            "content": {
                "application/json": {
                    "example": {"error": "Session not found", "details": {}}
                }
            },
        },
        422: {
            "description": "バリデーションエラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "message"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def chat(
    request: ChatRequest,
    session_service: SessionServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> ChatResponse:
    """
    AIエージェントとチャットします。

    ## 機能
    - 新しい会話セッションの作成
    - 既存セッションでの会話継続
    - ゲストユーザー対応（認証なし）
    - 認証済みユーザーとセッションの紐付け

    ## リクエスト例
    ```json
    {
        "message": "こんにちは",
        "session_id": null,
        "context": {"source": "web"}
    }
    ```

    Args:
        request: メッセージとオプションのsession_idを含むチャットリクエスト
        session_service: セッションサービスインスタンス
        current_user: オプションの現在のユーザー

    Returns:
        エージェントの応答とsession_idを含むChatResponse
    """
    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
    else:
        user_id = current_user.id if current_user else None
        session = await session_service.create_session(
            user_id=user_id, metadata=request.context
        )

    # Add user message to session
    await session_service.add_message(
        session_id=session.session_id,
        role="user",
        content=request.message,
    )

    # TODO: Implement actual agent logic using LangGraph
    # For now, just echo the message
    agent_response = f"Echo: {request.message}"

    # Add assistant message to session
    await session_service.add_message(
        session_id=session.session_id,
        role="assistant",
        content=agent_response,
    )

    return ChatResponse(
        response=agent_response,
        session_id=session.session_id,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionServiceDep = None,
) -> SessionResponse:
    """
    セッション情報を取得します。

    Args:
        session_id: セッション識別子
        session_service: セッションサービスインスタンス

    Returns:
        メッセージを含むセッション情報
    """
    session = await session_service.get_session(session_id)

    # Convert messages to schema
    from app.schemas.agent import Message

    messages = [
        Message(role=msg.role, content=msg.content, timestamp=msg.created_at)
        for msg in session.messages
    ]

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
        metadata=session.metadata,
    )


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def delete_session(
    session_id: str,
    session_service: SessionServiceDep = None,
) -> MessageResponse:
    """
    セッションを削除します。

    Args:
        session_id: セッション識別子
        session_service: セッションサービスインスタンス

    Returns:
        成功メッセージ
    """
    await session_service.delete_session(session_id)
    return MessageResponse(message=f"Session {session_id} deleted successfully")
