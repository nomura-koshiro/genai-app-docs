"""分析セッションAPI v2エンドポイント。

パス変更: /project/{id}/analysis/session → /project/{id}/session
"""

import uuid

from fastapi import APIRouter, Body, Path, Query, status

from app.api.core import AnalysisSessionServiceDep, ProjectMemberDep
from app.api.decorators import async_timeout, handle_service_errors
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisChatCreate,
    AnalysisChatListResponse,
    AnalysisFileConfigResponse,
    AnalysisFileCreate,
    AnalysisFileListResponse,
    AnalysisFileResponse,
    AnalysisFileUpdate,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisSessionListResponse,
    AnalysisSessionResultListResponse,
    AnalysisSessionUpdate,
    AnalysisSnapshotCreate,
    AnalysisSnapshotListResponse,
    AnalysisSnapshotResponse,
    AnalysisStepCreate,
    AnalysisStepResponse,
    AnalysisStepUpdate,
)

logger = get_logger(__name__)

session_router = APIRouter()


# ================================================================================
# セッション CRUD
# ================================================================================


@session_router.get(
    "/project/{project_id}/session",
    response_model=AnalysisSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション一覧取得",
)
@handle_service_errors
async def list_sessions(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    is_active: bool | None = Query(None, description="アクティブフラグフィルタ"),
) -> AnalysisSessionListResponse:
    """分析セッション一覧を取得します。"""
    sessions = await session_service.list_sessions(
        project_id=project_id, skip=skip, limit=limit, is_active=is_active
    )
    return AnalysisSessionListResponse(
        sessions=sessions, total=len(sessions), skip=skip, limit=limit
    )


@session_router.post(
    "/project/{project_id}/session",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析セッション作成",
)
@handle_service_errors
async def create_session(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_create: AnalysisSessionCreate = Body(...),
) -> AnalysisSessionDetailResponse:
    """分析セッションを作成します。"""
    return await session_service.create_session(project_id, member.user_id, session_create)


@session_router.get(
    "/project/{project_id}/session/{session_id}",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション詳細取得",
)
@handle_service_errors
async def get_session(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
) -> AnalysisSessionDetailResponse:
    """分析セッション詳細を取得します。"""
    return await session_service.get_session(project_id, session_id)


@session_router.get(
    "/project/{project_id}/session/{session_id}/result",
    response_model=AnalysisSessionResultListResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション結果取得",
)
@handle_service_errors
async def get_session_result(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
) -> AnalysisSessionResultListResponse:
    """分析結果を取得します。"""
    return await session_service.get_session_result(project_id, session_id)


@session_router.put(
    "/project/{project_id}/session/{session_id}",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション更新",
)
@handle_service_errors
async def update_session(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    session_update: AnalysisSessionUpdate = Body(...),
) -> AnalysisSessionDetailResponse:
    """分析セッションを更新します。"""
    result = None
    if session_update.input_file_id is not None:
        result = await session_service.select_input_file(session_id, session_update.input_file_id)
    if session_update.current_snapshot is not None:
        result = await session_service.restore_snapshot(session_id, session_update.current_snapshot)
    return result


@session_router.delete(
    "/project/{project_id}/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="分析セッション削除",
)
@handle_service_errors
async def delete_session(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
) -> None:
    """分析セッションを削除します。"""
    await session_service.delete_session(project_id, session_id)


@session_router.post(
    "/project/{project_id}/session/{session_id}/duplicate",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析セッション複製",
)
@handle_service_errors
async def duplicate_session(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="複製元セッションID"),
) -> AnalysisSessionDetailResponse:
    """分析セッションを複製します。"""
    return await session_service.duplicate_session(project_id, session_id, member.user_id)


# ================================================================================
# ファイル管理
# ================================================================================


@session_router.get(
    "/project/{project_id}/session/{session_id}/file",
    response_model=AnalysisFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="登録済ファイル一覧取得",
)
@handle_service_errors
async def list_session_files(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
) -> AnalysisFileListResponse:
    """セッションに登録されたファイル一覧を取得します。"""
    files = await session_service.list_session_files(project_id, session_id)
    return AnalysisFileListResponse(files=files, total=len(files))


@session_router.post(
    "/project/{project_id}/session/{session_id}/file",
    response_model=AnalysisFileConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ファイルアップロード",
)
@handle_service_errors
async def upload_session_file(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    analysis_file_create: AnalysisFileCreate = Body(...),
) -> AnalysisFileConfigResponse:
    """セッションにファイルを登録します。"""
    return await session_service.upload_session_file(project_id, session_id, analysis_file_create)


@session_router.patch(
    "/project/{project_id}/session/{session_id}/file/{file_id}",
    response_model=AnalysisFileResponse,
    status_code=status.HTTP_200_OK,
    summary="ファイル設定更新",
)
@handle_service_errors
async def update_file_config(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    file_id: uuid.UUID = Path(..., description="ファイルID"),
    analysis_file_update: AnalysisFileUpdate = Body(...),
) -> AnalysisFileResponse:
    """ファイルの設定を更新します。"""
    return await session_service.update_file_config(
        project_id, session_id, file_id, analysis_file_update
    )


# ================================================================================
# スナップショット管理
# ================================================================================


@session_router.get(
    "/project/{project_id}/session/{session_id}/snapshot",
    response_model=AnalysisSnapshotListResponse,
    status_code=status.HTTP_200_OK,
    summary="スナップショット一覧取得",
)
@handle_service_errors
async def list_snapshots(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
) -> AnalysisSnapshotListResponse:
    """スナップショット一覧を取得します。"""
    snapshots = await session_service.list_snapshots(project_id, session_id)
    return AnalysisSnapshotListResponse(snapshots=snapshots, total=len(snapshots))


@session_router.post(
    "/project/{project_id}/session/{session_id}/snapshot",
    response_model=AnalysisSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="手動スナップショット保存",
)
@handle_service_errors
async def create_snapshot(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    snapshot_create: AnalysisSnapshotCreate = Body(...),
) -> AnalysisSnapshotResponse:
    """手動でスナップショットを保存します。"""
    return await session_service.create_snapshot(project_id, session_id, snapshot_create)


# ================================================================================
# チャット
# ================================================================================


@session_router.get(
    "/project/{project_id}/session/{session_id}/message",
    response_model=AnalysisChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="チャットメッセージ履歴取得",
)
@handle_service_errors
async def get_chat_messages(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=500, description="取得件数"),
) -> AnalysisChatListResponse:
    """チャットメッセージ履歴を取得します。"""
    messages = await session_service.get_chat_messages(project_id, session_id, skip, limit)
    return AnalysisChatListResponse(messages=messages, total=len(messages), skip=skip, limit=limit)


@session_router.post(
    "/project/{project_id}/session/{session_id}/chat",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="AIチャット実行",
)
@handle_service_errors
@async_timeout(600.0)
async def execute_chat(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    chat_create: AnalysisChatCreate = Body(...),
) -> AnalysisSessionDetailResponse:
    """AIチャットを実行します。"""
    return await session_service.execute_chat(project_id, session_id, chat_create)


# ================================================================================
# 分析ステップ管理
# ================================================================================


@session_router.post(
    "/project/{project_id}/session/{session_id}/step",
    response_model=AnalysisStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析ステップ作成",
)
@handle_service_errors
async def create_step(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    analysis_step_create: AnalysisStepCreate = Body(...),
) -> AnalysisStepResponse:
    """分析ステップを作成します。"""
    return await session_service.create_step(
        project_id=project_id,
        session_id=session_id,
        step_name=analysis_step_create.name,
        step_type=analysis_step_create.type,
        data_source=analysis_step_create.input,
    )


@session_router.put(
    "/project/{project_id}/session/{session_id}/step/{step_id}",
    response_model=AnalysisStepResponse,
    status_code=status.HTTP_200_OK,
    summary="分析ステップ更新",
)
@handle_service_errors
async def update_step(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    step_id: uuid.UUID = Path(..., description="ステップID"),
    analysis_step_update: AnalysisStepUpdate = Body(...),
) -> AnalysisStepResponse:
    """分析ステップを更新します。"""
    return await session_service.update_step(
        project_id=project_id,
        session_id=session_id,
        step_id=step_id,
        step_name=analysis_step_update.name,
        step_type=analysis_step_update.type,
        data_source=analysis_step_update.input,
        config=analysis_step_update.config,
    )


@session_router.delete(
    "/project/{project_id}/session/{session_id}/step/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="分析ステップ削除",
)
@handle_service_errors
async def delete_step(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="セッションID"),
    step_id: uuid.UUID = Path(..., description="ステップID"),
) -> None:
    """分析ステップを削除します。"""
    await session_service.delete_step(project_id, session_id, step_id)


__all__ = ["session_router"]
