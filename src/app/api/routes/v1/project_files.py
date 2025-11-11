"""プロジェクトファイル管理APIエンドポイント。

このモジュールは、プロジェクトファイルのアップロード、ダウンロード、削除、一覧取得のエンドポイントを提供します。

主なエンドポイント:
    - POST /api/v1/projects/{project_id}/files: ファイルアップロード
    - GET /api/v1/projects/{project_id}/files: ファイル一覧取得
    - GET /api/v1/projects/{project_id}/files/{file_id}: ファイル情報取得
    - GET /api/v1/projects/{project_id}/files/{file_id}/download: ファイルダウンロード
    - DELETE /api/v1/projects/{project_id}/files/{file_id}: ファイル削除

使用例:
    >>> # ファイルアップロード
    >>> files = {"file": ("document.pdf", file_content, "application/pdf")}
    >>> response = await client.post(
    ...     f"/api/v1/projects/{project_id}/files",
    ...     files=files,
    ...     headers={"Authorization": f"Bearer {token}"}
    ... )
"""

import uuid

from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from app.api.core import CurrentUserAzureDep, DatabaseDep
from app.api.decorators import async_timeout, handle_service_errors
from app.core.logging import get_logger
from app.schemas.project_file import (
    ProjectFileDeleteResponse,
    ProjectFileListResponse,
    ProjectFileResponse,
    ProjectFileUploadResponse,
)
from app.services.project_file import ProjectFileService

logger = get_logger(__name__)

router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@router.get(
    "/projects/{project_id}/files",
    response_model=ProjectFileListResponse,
    summary="プロジェクトファイル一覧取得",
    description="""
    プロジェクトのファイル一覧を取得します。

    - **project_id**: プロジェクトID
    - **skip**: スキップするファイル数（デフォルト: 0）
    - **limit**: 返す最大ファイル数（デフォルト: 100）

    権限要件:
    - プロジェクトメンバー（VIEWER以上）

    認証が必要です。
    """,
)
@handle_service_errors
async def list_files(
    project_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
    skip: int = 0,
    limit: int = 100,
) -> ProjectFileListResponse:
    """プロジェクトのファイル一覧を取得します。

    Args:
        project_id: プロジェクトID
        db: データベースセッション（自動注入）
        current_user: 現在のユーザー（自動注入）
        skip: スキップするレコード数
        limit: 取得する最大レコード数

    Returns:
        ProjectFileListResponse: ファイル一覧

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 500: 内部エラー
    """
    logger.info(
        "ファイル一覧取得リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        action="list_files",
    )

    file_service = ProjectFileService(db)
    user_id = current_user.id

    files, total = await file_service.list_project_files(project_id, user_id, skip, limit)

    file_responses = [ProjectFileResponse.model_validate(f) for f in files]

    logger.info(
        "ファイル一覧を取得しました",
        project_id=str(project_id),
        count=len(files),
        total=total,
    )

    return ProjectFileListResponse(files=file_responses, total=total, project_id=project_id)


@router.get(
    "/projects/{project_id}/files/{file_id}",
    response_model=ProjectFileResponse,
    summary="プロジェクトファイル情報取得",
    description="""
    プロジェクトのファイル情報を取得します。

    - **project_id**: プロジェクトID
    - **file_id**: ファイルID

    権限要件:
    - プロジェクトメンバー（VIEWER以上）

    認証が必要です。
    """,
)
@handle_service_errors
async def get_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> ProjectFileResponse:
    """プロジェクトのファイル情報を取得します。

    Args:
        project_id: プロジェクトID
        file_id: ファイルID
        db: データベースセッション（自動注入）
        current_user: 現在のユーザー（自動注入）

    Returns:
        ProjectFileResponse: ファイル情報

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: ファイルが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "ファイル情報取得リクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="get_file",
    )

    file_service = ProjectFileService(db)
    user_id = current_user.id

    file = await file_service.get_file(file_id, user_id)

    logger.info(
        "ファイル情報を取得しました",
        file_id=str(file.id),
        filename=file.filename,
    )

    return ProjectFileResponse.model_validate(file)


@router.get(
    "/projects/{project_id}/files/{file_id}/download",
    response_class=FileResponse,
    summary="プロジェクトファイルダウンロード",
    description="""
    プロジェクトのファイルをダウンロードします。

    - **project_id**: プロジェクトID
    - **file_id**: ファイルID

    権限要件:
    - プロジェクトメンバー（VIEWER以上）

    バイナリストリームとして返却されます。

    認証が必要です。
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（ファイルダウンロード）
async def download_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> FileResponse:
    """プロジェクトのファイルをダウンロードします。

    Args:
        project_id: プロジェクトID
        file_id: ファイルID
        db: データベースセッション（自動注入）
        current_user: 現在のユーザー（自動注入）

    Returns:
        FileResponse: ファイルのバイナリストリーム

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: ファイルが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "ファイルダウンロードリクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="download_file",
    )

    file_service = ProjectFileService(db)
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
        path=str(filepath),
        media_type=file_metadata.mime_type or "application/octet-stream",
        filename=file_metadata.original_filename,
    )


# ================================================================================
# POST Endpoints
# ================================================================================


@router.post(
    "/projects/{project_id}/files",
    response_model=ProjectFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトファイルアップロード",
    description="""
    プロジェクトにファイルをアップロードします。

    - **project_id**: プロジェクトID
    - **file**: アップロードするファイル（バイナリ）

    権限要件:
    - プロジェクトメンバー（MEMBER以上）

    制限事項:
    - 最大ファイルサイズ: 50MB
    - 許可されるMIMEタイプ: image/*, application/pdf, text/*, .docx, .xlsx

    認証が必要です。アップロードされたファイルはユーザーに紐付けられます。
    """,
)
@handle_service_errors
@async_timeout(60.0)  # 60秒タイムアウト
async def upload_file(
    project_id: uuid.UUID,
    file: UploadFile,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> ProjectFileUploadResponse:
    """プロジェクトにファイルをアップロードします。

    Args:
        project_id: プロジェクトID
        file: アップロードするファイル
        db: データベースセッション（自動注入）
        current_user: 現在のユーザー（自動注入）

    Returns:
        ProjectFileUploadResponse: アップロード成功レスポンス

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 422: ファイルが無効
            - 500: 内部エラー
    """
    logger.info(
        "ファイルアップロードリクエスト",
        project_id=str(project_id),
        filename=file.filename,
        content_type=file.content_type,
        user_id=str(current_user.id),
        action="upload_file",
    )

    file_service = ProjectFileService(db)
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


@router.delete(
    "/projects/{project_id}/files/{file_id}",
    response_model=ProjectFileDeleteResponse,
    summary="プロジェクトファイル削除",
    description="""
    プロジェクトのファイルを削除します。

    - **project_id**: プロジェクトID
    - **file_id**: ファイルID

    権限要件:
    - ファイルのアップロード者本人、またはプロジェクトADMIN/OWNER

    認証が必要です。
    """,
)
@handle_service_errors
async def delete_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> ProjectFileDeleteResponse:
    """プロジェクトのファイルを削除します。

    Args:
        project_id: プロジェクトID
        file_id: ファイルID
        db: データベースセッション（自動注入）
        current_user: 現在のユーザー（自動注入）

    Returns:
        ProjectFileDeleteResponse: 削除成功レスポンス

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: ファイルが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "ファイル削除リクエスト",
        project_id=str(project_id),
        file_id=str(file_id),
        user_id=str(current_user.id),
        action="delete_file",
    )

    file_service = ProjectFileService(db)
    user_id = current_user.id

    await file_service.delete_file(file_id, user_id)

    logger.info(
        "ファイルを削除しました",
        file_id=str(file_id),
    )

    return ProjectFileDeleteResponse(file_id=file_id, message=f"File {file_id} deleted successfully")
