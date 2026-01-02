"""プロジェクトファイル管理APIエンドポイント。

このモジュールは、プロジェクトファイルのアップロード、ダウンロード、削除、一覧取得のエンドポイントを提供します。

主な機能:
    - ファイル一覧取得（GET /api/v1/project/{project_id}/file）
    - ファイル情報取得（GET /api/v1/project/{project_id}/file/{file_id}）
    - ファイルダウンロード（GET /api/v1/project/{project_id}/file/{file_id}/download）
    - ファイルアップロード（POST /api/v1/project/{project_id}/file）
    - ファイル削除（DELETE /api/v1/project/{project_id}/file/{file_id}）
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.core import CurrentUserAccountDep, ProjectFileServiceDep
from app.core.decorators import async_timeout, handle_service_errors
from app.core.logging import get_logger
from app.schemas import (
    ProjectFileDeleteResponse,
    ProjectFileListResponse,
    ProjectFileResponse,
    ProjectFileUploadResponse,
)
from app.schemas.project.project_file import (
    ProjectFileUsageResponse,
    ProjectFileVersionHistoryResponse,
)

logger = get_logger(__name__)

project_files_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@project_files_router.get(
    "/project/{project_id}/file",
    response_model=ProjectFileListResponse,
    summary="プロジェクトファイル一覧取得",
    description="""
    プロジェクトのファイル一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    クエリパラメータ:
        - skip: int - スキップするファイル数（デフォルト: 0）
        - limit: int - 返す最大ファイル数（デフォルト: 100）
        - mime_type: str | None - MIMEタイプでフィルタ（部分一致、例: "image/", "application/pdf"）

    レスポンス:
        - ProjectFileListResponse: プロジェクトファイル一覧レスポンス
            - files (list[ProjectFileResponse]): ファイルリスト
                - id (uuid): ファイルID
                - project_id (uuid): プロジェクトID
                - filename (str): 保存ファイル名
                - original_filename (str): 元のファイル名
                - file_path (str): ファイルパス
                - file_size (int): ファイルサイズ（バイト）
                - mime_type (str | None): MIMEタイプ
                - uploaded_by (uuid): アップロード者のユーザーID
                - uploaded_at (datetime): アップロード日時
                - uploader (UserAccountResponse | None): アップロード者のユーザー情報
            - total (int): 総件数
            - project_id (uuid): プロジェクトID

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_files(
    project_id: uuid.UUID,
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = 0,
    limit: int = 100,
    mime_type: str | None = Query(None, description="MIMEタイプでフィルタ（部分一致、例: 'image/', 'application/pdf'）"),
) -> ProjectFileListResponse:
    """プロジェクトのファイル一覧を取得します。"""
    logger.info(
        "ファイル一覧取得リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        mime_type=mime_type,
        action="list_files",
    )

    user_id = current_user.id

    files, total = await file_service.list_project_files(project_id, user_id, skip, limit, mime_type)

    file_responses = [ProjectFileResponse.model_validate(f) for f in files]

    logger.info(
        "ファイル一覧を取得しました",
        project_id=str(project_id),
        count=len(files),
        total=total,
    )

    return ProjectFileListResponse(files=file_responses, total=total, project_id=project_id)


@project_files_router.get(
    "/project/{project_id}/file/{file_id}",
    response_model=ProjectFileResponse,
    summary="プロジェクトファイル情報取得",
    description="""
    プロジェクトのファイル情報を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）

    レスポンス:
        - ProjectFileResponse: プロジェクトファイル情報
            - id (uuid): ファイルID
            - project_id (uuid): プロジェクトID
            - filename (str): 保存ファイル名
            - original_filename (str): 元のファイル名
            - file_path (str): ファイルパス
            - file_size (int): ファイルサイズ（バイト）
            - mime_type (str | None): MIMEタイプ
            - uploaded_by (uuid): アップロード者のユーザーID
            - uploaded_at (datetime): アップロード日時
            - uploader (UserAccountResponse | None): アップロード者のユーザー情報

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルが見つからない
    """,
)
@handle_service_errors
async def get_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectFileResponse:
    """プロジェクトのファイル情報を取得します。"""
    logger.info(
        "ファイル情報取得リクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="get_file",
    )

    user_id = current_user.id

    file = await file_service.get_file(file_id, user_id)

    logger.info(
        "ファイル情報を取得しました",
        file_id=str(file.id),
        filename=file.filename,
    )

    return ProjectFileResponse.model_validate(file)


@project_files_router.get(
    "/project/{project_id}/file/{file_id}/download",
    response_class=FileResponse,
    summary="プロジェクトファイルダウンロード",
    description="""
    プロジェクトのファイルをダウンロードします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）

    レスポンス:
        - バイナリストリーム（ファイルデータ）

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルが見つからない
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（ファイルダウンロード）
async def download_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> FileResponse:
    """プロジェクトのファイルをダウンロードします。"""
    logger.info(
        "ファイルダウンロードリクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="download_file",
    )

    user_id = current_user.id

    filepath = await file_service.download_file(file_id, user_id)

    # ファイルメタデータを取得（ファイル名とMIMEタイプ用）
    file_metadata = await file_service.get_file(file_id, user_id)

    logger.info(
        "ファイルをダウンロードしました",
        file_id=str(file_id),
        filename=file_metadata.filename,
        file_size=file_metadata.file_size,
    )

    return FileResponse(
        path=filepath,
        media_type=file_metadata.mime_type or "application/octet-stream",
        filename=file_metadata.original_filename,
    )


# ================================================================================
# POST Endpoints
# ================================================================================


@project_files_router.post(
    "/project/{project_id}/file",
    response_model=ProjectFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトファイルアップロード",
    description="""
    プロジェクトにファイルをアップロードします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - Content-Type: multipart/form-data
        - file: File - アップロードするファイル

    レスポンス:
        - ProjectFileUploadResponse: ファイルアップロード成功レスポンス
            - id (uuid): ファイルID
            - project_id (uuid): プロジェクトID
            - filename (str): ファイル名
            - original_filename (str): 元のファイル名
            - file_path (str): ファイルパス
            - file_size (int): ファイルサイズ
            - mime_type (str): MIMEタイプ
            - uploaded_by (uuid): アップロードユーザーID
            - uploaded_at (datetime): アップロード日時
            - message (str): メッセージ

    ステータスコード:
        - 201: アップロード成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 413: ファイルサイズ超過
        - 422: ファイルが無効
    """,
    openapi_extra={
        "requestBody": {"content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/ProjectFileUploadRequest"}}}}
    },
)
@handle_service_errors
@async_timeout(60.0)  # 60秒タイムアウト
async def upload_file(
    project_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="アップロードするファイル")],
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectFileUploadResponse:
    """プロジェクトにファイルをアップロードします。"""
    logger.info(
        "ファイルアップロードリクエスト",
        project_id=str(project_id),
        filename=file.filename,
        content_type=file.content_type,
        user_id=str(current_user.id),
        action="upload_file",
    )

    user_id = current_user.id

    uploaded_file = await file_service.upload_file(project_id, file, uploaded_by=user_id)

    logger.info(
        "ファイルをアップロードしました",
        file_id=str(uploaded_file.id),
        filename=uploaded_file.filename,
        file_size=uploaded_file.file_size,
    )

    return ProjectFileUploadResponse(
        id=uploaded_file.id,
        project_id=uploaded_file.project_id,
        filename=uploaded_file.filename,
        original_filename=uploaded_file.original_filename,
        file_path=uploaded_file.file_path,
        file_size=uploaded_file.file_size,
        mime_type=uploaded_file.mime_type,
        uploaded_by=uploaded_file.uploaded_by,
        uploaded_at=uploaded_file.uploaded_at,
        message="File uploaded successfully",
    )


# ================================================================================
# DELETE Endpoints
# ================================================================================


@project_files_router.delete(
    "/project/{project_id}/file/{file_id}",
    response_model=ProjectFileDeleteResponse,
    summary="プロジェクトファイル削除",
    description="""
    プロジェクトのファイルを削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）

    レスポンス:
        - ProjectFileDeleteResponse: ファイル削除成功レスポンス
            - file_id (uuid): 削除されたファイルID
            - message (str): メッセージ

    ステータスコード:
        - 200: 削除成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルが見つからない
    """,
)
@handle_service_errors
async def delete_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectFileDeleteResponse:
    """プロジェクトのファイルを削除します。"""
    logger.info(
        "ファイル削除リクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="delete_file",
    )

    user_id = current_user.id

    await file_service.delete_file(file_id, user_id)

    logger.info(
        "ファイルを削除しました",
        file_id=str(file_id),
    )

    return ProjectFileDeleteResponse(file_id=file_id, message=f"File {file_id} deleted successfully")


@project_files_router.get(
    "/project/{project_id}/file/{file_id}/usage",
    response_model=ProjectFileUsageResponse,
    summary="プロジェクトファイル使用状況取得",
    description="""
    プロジェクトのファイルがどこで使用されているかを取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）

    レスポンス:
        - ProjectFileUsageResponse: ファイル使用状況
            - file_id (uuid): ファイルID
            - filename (str): ファイル名
            - analysis_session_count (int): 分析セッションでの使用数
            - driver_tree_count (int): ドライバーツリーでの使用数
            - total_usage_count (int): 総使用数
            - usages (list[FileUsageItem]): 使用情報リスト

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルが見つからない
    """,
)
@handle_service_errors
async def get_file_usage(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectFileUsageResponse:
    """プロジェクトのファイル使用状況を取得します。"""
    logger.info(
        "ファイル使用状況取得リクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="get_file_usage",
    )

    user_id = current_user.id

    usage = await file_service.get_file_usage(file_id, user_id)

    logger.info(
        "ファイル使用状況を取得しました",
        file_id=str(file_id),
        analysis_session_count=usage.analysis_session_count,
        driver_tree_count=usage.driver_tree_count,
        total_usage_count=usage.total_usage_count,
    )

    return usage


@project_files_router.get(
    "/project/{project_id}/file/{file_id}/versions",
    response_model=ProjectFileVersionHistoryResponse,
    summary="プロジェクトファイルバージョン履歴取得",
    description="""
    プロジェクトのファイルのバージョン履歴を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須、任意のバージョンを指定可能）

    レスポンス:
        - ProjectFileVersionHistoryResponse: バージョン履歴
            - file_id (uuid): 最新バージョンのファイルID
            - original_filename (str): 元のファイル名
            - total_versions (int): 総バージョン数
            - versions (list[ProjectFileVersionItem]): バージョンリスト

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルが見つからない
    """,
)
@handle_service_errors
async def get_file_version_history(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectFileVersionHistoryResponse:
    """プロジェクトのファイルバージョン履歴を取得します。"""
    logger.info(
        "ファイルバージョン履歴取得リクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="get_file_version_history",
    )

    user_id = current_user.id

    version_history = await file_service.get_version_history(file_id, user_id)

    logger.info(
        "ファイルバージョン履歴を取得しました",
        file_id=str(file_id),
        total_versions=version_history.total_versions,
    )

    return version_history


@project_files_router.post(
    "/project/{project_id}/file/{file_id}/version",
    response_model=ProjectFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトファイル新バージョンアップロード",
    description="""
    既存ファイルの新しいバージョンをアップロードします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - 親ファイルID（必須、新バージョンの元となるファイル）

    リクエストボディ:
        - Content-Type: multipart/form-data
        - file: File - アップロードするファイル

    レスポンス:
        - ProjectFileUploadResponse: ファイルアップロード成功レスポンス

    ステータスコード:
        - 201: アップロード成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: 親ファイルが見つからない
        - 413: ファイルサイズ超過
        - 422: ファイルが無効
    """,
    openapi_extra={
        "requestBody": {"content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/ProjectFileUploadRequest"}}}}
    },
)
@handle_service_errors
@async_timeout(60.0)
async def upload_file_version(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="アップロードするファイル")],
    file_service: ProjectFileServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectFileUploadResponse:
    """既存ファイルの新しいバージョンをアップロードします。"""
    logger.info(
        "ファイル新バージョンアップロードリクエスト",
        project_id=str(project_id),
        parent_file_id=str(file_id),
        filename=file.filename,
        content_type=file.content_type,
        user_id=str(current_user.id),
        action="upload_file_version",
    )

    user_id = current_user.id

    uploaded_file = await file_service.upload_new_version(
        parent_file_id=file_id,
        file=file,
        uploaded_by=user_id,
    )

    logger.info(
        "ファイル新バージョンをアップロードしました",
        file_id=str(uploaded_file.id),
        parent_file_id=str(file_id),
        version=uploaded_file.version,
        filename=uploaded_file.filename,
        file_size=uploaded_file.file_size,
    )

    return ProjectFileUploadResponse(
        id=uploaded_file.id,
        project_id=uploaded_file.project_id,
        filename=uploaded_file.filename,
        original_filename=uploaded_file.original_filename,
        file_path=uploaded_file.file_path,
        file_size=uploaded_file.file_size,
        mime_type=uploaded_file.mime_type,
        uploaded_by=uploaded_file.uploaded_by,
        uploaded_at=uploaded_file.uploaded_at,
        version=uploaded_file.version,
        parent_file_id=uploaded_file.parent_file_id,
        is_latest=uploaded_file.is_latest,
        message=f"File version {uploaded_file.version} uploaded successfully",
    )
