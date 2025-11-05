"""サンプルセッション管理APIエンドポイント。

このモジュールは、チャットセッションの管理エンドポイントを提供します。
セッション一覧、作成、取得、更新、削除の機能を含みます。
"""

import uuid

from fastapi import APIRouter, Query

from app.api.core import CurrentUserDep, CurrentUserOptionalDep, SessionServiceDep
from app.api.decorators import handle_service_errors, validate_permissions
from app.core.logging import get_logger
from app.schemas.sample_sessions import (
    SampleDeleteResponse,
    SampleMessageResponse,
    SampleSessionCreateRequest,
    SampleSessionListResponse,
    SampleSessionResponse,
    SampleSessionUpdateRequest,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/sample-sessions",
    response_model=SampleSessionListResponse,
    summary="サンプルセッション一覧取得",
    description="""
    セッション一覧を取得します。

    - **user_id**: ユーザーID（指定した場合、該当ユーザーのセッションのみ）
    - **skip**: スキップするセッション数（ページネーション）
    - **limit**: 返却する最大セッション数（ページネーション）

    認証はオプションです。
    """,
)
@handle_service_errors
async def list_sessions(
    session_service: SessionServiceDep,
    current_user: CurrentUserOptionalDep = None,
    user_id: uuid.UUID | None = Query(None, description="ユーザーID"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="最大取得数"),
) -> SampleSessionListResponse:
    """セッション一覧を取得します。

    Args:
        session_service: セッションサービス（自動注入）
        current_user: 現在のユーザー（オプション、自動注入）
        user_id: ユーザーID（オプション）
        skip: スキップするセッション数
        limit: 返却する最大セッション数

    Returns:
        SampleSessionListResponse: セッション一覧
    """
    logger.info(
        "サンプルセッション一覧取得リクエスト",
        user_id=user_id,
        skip=skip,
        limit=limit,
        action="sample_list_sessions",
    )

    sessions, total = await session_service.list_sessions(
        user_id=user_id,
        skip=skip,
        limit=limit,
    )

    # セッションをレスポンススキーマに変換
    session_responses = [
        SampleSessionResponse(
            session_id=session.session_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[
                SampleMessageResponse(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.created_at,
                )
                for msg in session.messages
            ],
            metadata=session.session_metadata,
        )
        for session in sessions
    ]

    logger.info(
        "サンプルセッション一覧を取得しました",
        count=len(session_responses),
        total=total,
    )

    return SampleSessionListResponse(
        sessions=session_responses,
        total=total,
    )


@router.get(
    "/sample-sessions/{session_id}",
    response_model=SampleSessionResponse,
    summary="サンプルセッション詳細取得",
    description="""
    セッション情報と会話履歴を取得します。

    認証が必要です。セッションの所有者またはスーパーユーザーのみ取得可能です。
    """,
)
@handle_service_errors
@validate_permissions("session", "read")
async def get_session(
    session_id: str,
    session_service: SessionServiceDep,
    current_user: CurrentUserDep,
) -> SampleSessionResponse:
    """セッション情報と会話履歴を取得します。

    Args:
        session_id: セッション識別子
        session_service: セッションサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）

    Returns:
        SampleSessionResponse: セッション詳細情報

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: セッションが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "サンプルセッション詳細取得リクエスト",
        session_id=session_id,
        user_id=current_user.id,
        action="sample_get_session",
    )

    # validate_permissionsデコレータで権限検証済み
    session = await session_service.get_session(session_id)

    # メッセージをSampleMessageResponseに変換
    messages = [
        SampleMessageResponse(
            role=msg.role,
            content=msg.content,
            timestamp=msg.created_at,
        )
        for msg in session.messages
    ]

    logger.info(
        "サンプルセッション詳細を取得しました",
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


@router.post(
    "/sample-sessions",
    response_model=SampleSessionResponse,
    summary="サンプルセッション作成",
    description="""
    新しいセッションを作成します。

    - **metadata**: セッションのメタデータ（オプション）

    認証はオプションです。認証済みユーザーの場合、セッションがユーザーに紐付けられます。
    """,
)
@handle_service_errors
async def create_session(
    request: SampleSessionCreateRequest,
    session_service: SessionServiceDep,
    current_user: CurrentUserOptionalDep = None,
) -> SampleSessionResponse:
    """新しいセッションを作成します。

    Args:
        request: セッション作成リクエスト
        session_service: セッションサービス（自動注入）
        current_user: 現在のユーザー（オプション、自動注入）

    Returns:
        SampleSessionResponse: 作成されたセッション

    Raises:
        HTTPException:
            - 500: 内部エラー
    """
    user_id = current_user.id if current_user else None

    logger.info(
        "サンプルセッション作成リクエスト",
        user_id=user_id,
        has_metadata=request.metadata is not None,
        action="sample_create_session",
    )

    session = await session_service.create_session(
        user_id=user_id,
        metadata=request.metadata,
    )

    logger.info(
        "サンプルセッションを作成しました",
        session_id=session.session_id,
    )

    return SampleSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[],
        metadata=session.session_metadata,
    )


@router.patch(
    "/sample-sessions/{session_id}",
    response_model=SampleSessionResponse,
    summary="サンプルセッション更新",
    description="""
    セッション情報を更新します。

    - **metadata**: 更新するメタデータ

    認証が必要です。セッションの所有者またはスーパーユーザーのみ更新可能です。
    """,
)
@handle_service_errors
@validate_permissions("session", "update")
async def update_session(
    session_id: str,
    request: SampleSessionUpdateRequest,
    session_service: SessionServiceDep,
    current_user: CurrentUserDep,
) -> SampleSessionResponse:
    """セッション情報を更新します。

    Args:
        session_id: セッション識別子
        request: セッション更新リクエスト
        session_service: セッションサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）

    Returns:
        SampleSessionResponse: 更新されたセッション

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: セッションが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "サンプルセッション更新リクエスト",
        session_id=session_id,
        user_id=current_user.id,
        has_metadata=request.metadata is not None,
        action="sample_update_session",
    )

    # validate_permissionsデコレータで権限検証済み
    session = await session_service.update_session(
        session_id=session_id,
        metadata=request.metadata,
    )

    # メッセージをSampleMessageResponseに変換
    messages = [
        SampleMessageResponse(
            role=msg.role,
            content=msg.content,
            timestamp=msg.created_at,
        )
        for msg in session.messages
    ]

    logger.info(
        "サンプルセッションを更新しました",
        session_id=session_id,
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
    セッションと関連するメッセージを削除します。

    認証が必要です。セッションの所有者またはスーパーユーザーのみ削除可能です。
    """,
)
@handle_service_errors
@validate_permissions("session", "delete")
async def delete_session(
    session_id: str,
    session_service: SessionServiceDep,
    current_user: CurrentUserDep,
) -> SampleDeleteResponse:
    """セッションと関連するメッセージを削除します。

    Args:
        session_id: セッション識別子
        session_service: セッションサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）

    Returns:
        SampleDeleteResponse: 削除成功メッセージ

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
        action="sample_delete_session",
    )

    # validate_permissionsデコレータで権限検証済み
    await session_service.delete_session(session_id)

    logger.info(
        "サンプルセッションを削除しました",
        session_id=session_id,
    )

    return SampleDeleteResponse(message=f"Session {session_id} deleted successfully")
