"""サンプルエージェントAPIエンドポイント。

このモジュールは、AIエージェントとのチャットとセッション管理のサンプルエンドポイントを提供します。
"""

from fastapi import APIRouter

from app.api.core import AgentServiceDep, CurrentUserDep, CurrentUserOptionalDep
from app.api.decorators import async_timeout, handle_service_errors, validate_permissions
from app.core.logging import get_logger
from app.schemas.sample_agents import (
    SampleChatRequest,
    SampleChatResponse,
)
from app.schemas.sample_sessions import (
    SampleDeleteResponse,
    SampleMessageResponse,
    SampleSessionResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/sample-chat",
    response_model=SampleChatResponse,
    summary="サンプルAIエージェントとチャット",
    description="""
    サンプルAIエージェントとチャットします。

    - **message**: ユーザーメッセージ（1-10000文字）
    - **session_id**: セッション識別子（新規の場合は省略）
    - **context**: 追加コンテキスト情報（オプション）

    認証はオプションです。認証済みユーザーの場合、セッションがユーザーに紐付けられます。
    """,
)
@handle_service_errors
@async_timeout(300.0)  # 5分タイムアウト（AI処理時間）
async def chat(
    request: SampleChatRequest,
    agent_service: AgentServiceDep,
    current_user: CurrentUserOptionalDep = None,
) -> SampleChatResponse:
    """AIエージェントとチャットします。

    Args:
        request: チャットリクエスト
        agent_service: エージェントサービス（自動注入）
        current_user: 現在のユーザー（オプション、自動注入）

    Returns:
        ChatResponse: エージェントのレスポンス

    Raises:
        HTTPException:
            - 400: メッセージが無効
            - 404: セッションが見つからない
            - 500: 内部エラー
    """
    user_id = current_user.id if current_user else None

    logger.info(
        "サンプルチャットリクエスト",
        session_id=request.session_id,
        user_id=user_id,
        message_length=len(request.message),
        action="sample_chat",
    )

    result = await agent_service.chat(
        message=request.message,
        session_id=request.session_id,
        user_id=user_id,
        context=request.context,
    )

    logger.info(
        "サンプルチャット完了",
        session_id=result.get("session_id"),
        response_length=len(result.get("response", "")),
    )

    return SampleChatResponse(**result)


@router.get(
    "/sample-sessions/{session_id}",
    response_model=SampleSessionResponse,
    summary="サンプルセッション情報取得",
    description="""
    サンプルセッション情報と会話履歴を取得します。

    認証が必要です。セッションの所有者またはスーパーユーザーのみ取得可能です。
    """,
)
@handle_service_errors
@validate_permissions("session", "read")
async def get_session(
    session_id: str,
    agent_service: AgentServiceDep,
    current_user: CurrentUserDep,
    session_service: AgentServiceDep,  # validate_permissionsが session_service を要求
) -> SampleSessionResponse:
    """セッション情報と会話履歴を取得します。

    Args:
        session_id: セッション識別子
        agent_service: エージェントサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）
        session_service: セッションサービス（権限検証用、自動注入）

    Returns:
        SessionResponse: セッション情報

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: セッションが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "サンプルセッション取得リクエスト",
        session_id=session_id,
        user_id=current_user.id,
        action="get_sample_session",
    )

    # validate_permissionsデコレータで権限検証済み
    session = await agent_service.get_session(session_id)

    # メッセージをSampleMessageResponseに変換
    messages = [SampleMessageResponse(role=msg.role, content=msg.content, timestamp=msg.created_at) for msg in session.messages]

    logger.info(
        "サンプルセッションを取得しました",
        session_id=session_id,
        message_count=len(messages),
    )

    return SampleSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
        metadata=session.session_metadata,
    )


@router.delete(
    "/sample-sessions/{session_id}",
    response_model=SampleDeleteResponse,
    summary="サンプルセッション削除",
    description="""
    サンプルセッションと関連するメッセージを削除します。

    認証が必要です。セッションの所有者またはスーパーユーザーのみ削除可能です。
    """,
)
@handle_service_errors
@validate_permissions("session", "delete")
async def delete_session(
    session_id: str,
    agent_service: AgentServiceDep,
    current_user: CurrentUserDep,
    session_service: AgentServiceDep,  # validate_permissionsが session_service を要求
) -> SampleDeleteResponse:
    """セッションと関連するメッセージを削除します。

    Args:
        session_id: セッション識別子
        agent_service: エージェントサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）
        session_service: セッションサービス（権限検証用、自動注入）

    Returns:
        DeleteResponse: 削除成功メッセージ

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: セッションが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "サンプルセッション削除リクエスト",
        session_id=session_id,
        user_id=current_user.id,
        action="delete_sample_session",
    )

    # validate_permissionsデコレータで権限検証済み
    await agent_service.delete_session(session_id)

    logger.info(
        "サンプルセッションを削除しました",
        session_id=session_id,
    )

    return SampleDeleteResponse(message=f"Session {session_id} deleted successfully")
