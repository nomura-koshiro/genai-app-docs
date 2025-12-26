"""サンプルファイル管理APIエンドポイント。

このモジュールは、ファイルのアップロード、ダウンロード、削除、一覧取得のサンプルエンドポイントを提供します。
"""

from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from app.api.core import CurrentUserDep, CurrentUserOptionalDep, FileServiceDep
from app.api.decorators import async_timeout, handle_service_errors, validate_permissions
from app.core.logging import get_logger
from app.schemas import (
    SampleFileDeleteResponse,
    SampleFileListResponse,
    SampleFileUploadResponse,
)
from app.schemas import (
    SampleFileResponse as SampleFileResponseSchema,
)

logger = get_logger(__name__)

sample_files_router = APIRouter()


@sample_files_router.post(
    "/sample-upload",
    response_model=SampleFileUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="サンプルファイルアップロード",
    description="""
    サンプルファイルをアップロードします。

    - **file**: アップロードするファイル（バイナリ）

    制限事項:
    - 最大ファイルサイズ: 10MB
    - 許可されるMIMEタイプ: text/plain, text/csv, application/pdf, application/json, 画像ファイル等

    認証はオプションです。認証済みユーザーの場合、ファイルがユーザーに紐付けられます。
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（Azure Blob Storage アップロード）
async def upload_file(
    file: UploadFile,
    file_service: FileServiceDep,
    current_user: CurrentUserOptionalDep = None,
) -> SampleFileUploadResponse:
    """ファイルをアップロードします。

    Args:
        file: アップロードするファイル
        file_service: ファイルサービス（自動注入）
        current_user: 現在のユーザー（オプション、自動注入）

    Returns:
        FileUploadResponse: アップロード成功レスポンス

    Raises:
        HTTPException:
            - 400: ファイルが無効
            - 500: 内部エラー
    """
    user_id = current_user.id if current_user else None

    logger.info(
        "サンプルファイルアップロードリクエスト",
        filename=file.filename,
        content_type=file.content_type,
        user_id=user_id,
        action="sample_upload_file",
    )

    uploaded_file = await file_service.upload_file(file, user_id=user_id)

    logger.info(
        "サンプルファイルをアップロードしました",
        file_id=uploaded_file.file_id,
        filename=uploaded_file.filename,
        size=uploaded_file.size,
    )

    return SampleFileUploadResponse(
        file_id=uploaded_file.file_id,
        filename=uploaded_file.filename,
        size=uploaded_file.size,
        content_type=uploaded_file.content_type,
        message="File uploaded successfully",
    )


@sample_files_router.get(
    "/sample-download/{file_id}",
    response_class=FileResponse,
    summary="サンプルファイルダウンロード",
    description="""
    サンプルファイルをダウンロードします。

    バイナリストリームとして返却されます。

    認証が必要です。ファイルの所有者またはスーパーユーザーのみダウンロード可能です。
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（ファイルダウンロード）
@validate_permissions("file", "download")
async def download_file(
    file_id: str,
    file_service: FileServiceDep,
    current_user: CurrentUserDep,
) -> FileResponse:
    """ファイルをダウンロードします。

    Args:
        file_id: ファイル識別子
        file_service: ファイルサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）

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
        "サンプルファイルダウンロードリクエスト",
        file_id=file_id,
        user_id=current_user.id,
        action="sample_download_file",
    )

    # validate_permissionsデコレータで権限検証済み
    file_metadata = await file_service.get_file(file_id)

    logger.info(
        "サンプルファイルをダウンロードしました",
        file_id=file_id,
        filename=file_metadata.filename,
        size=file_metadata.size,
    )

    return FileResponse(
        path=file_metadata.filepath,
        media_type=file_metadata.content_type,
        filename=file_metadata.filename,
    )


@sample_files_router.delete(
    "/sample-files/{file_id}",
    response_model=SampleFileDeleteResponse,
    summary="サンプルファイル削除",
    description="""
    サンプルファイルを削除します。

    認証が必要です。ファイルの所有者またはスーパーユーザーのみ削除可能です。
    """,
)
@handle_service_errors
@validate_permissions("file", "delete")
async def delete_file(
    file_id: str,
    file_service: FileServiceDep,
    current_user: CurrentUserDep,
) -> SampleFileDeleteResponse:
    """ファイルを削除します。

    Args:
        file_id: ファイル識別子
        file_service: ファイルサービス（自動注入）
        current_user: 現在のユーザー（必須、自動注入）

    Returns:
        FileDeleteResponse: 削除成功レスポンス

    Raises:
        HTTPException:
            - 401: 認証が必要
            - 403: アクセス権限なし
            - 404: ファイルが見つからない
            - 500: 内部エラー
    """
    logger.info(
        "サンプルファイル削除リクエスト",
        file_id=file_id,
        user_id=current_user.id,
        action="sample_delete_file",
    )

    # validate_permissionsデコレータで権限検証済み
    await file_service.delete_file(file_id)

    logger.info(
        "サンプルファイルを削除しました",
        file_id=file_id,
    )

    return SampleFileDeleteResponse(file_id=file_id, message=f"File {file_id} deleted successfully")


@sample_files_router.get(
    "/sample-list",
    response_model=SampleFileListResponse,
    summary="サンプルファイル一覧取得",
    description="""
    アップロードされたサンプルファイル一覧を取得します。

    - **skip**: スキップするファイル数（デフォルト: 0）
    - **limit**: 返す最大ファイル数（デフォルト: 100）

    認証はオプションです。認証済みユーザーの場合、そのユーザーのファイルのみ返します。
    """,
)
@handle_service_errors
async def list_files(
    file_service: FileServiceDep,
    current_user: CurrentUserOptionalDep = None,
    skip: int = 0,
    limit: int = 100,
) -> SampleFileListResponse:
    """ファイル一覧を取得します。

    Args:
        file_service: ファイルサービス（自動注入）
        current_user: 現在のユーザー（オプション、自動注入）
        skip: スキップするレコード数
        limit: 取得する最大レコード数

    Returns:
        FileListResponse: ファイル一覧

    Raises:
        HTTPException:
            - 500: 内部エラー
    """
    user_id = current_user.id if current_user else None

    logger.info(
        "サンプルファイル一覧取得リクエスト",
        user_id=user_id,
        skip=skip,
        limit=limit,
        action="sample_list_files",
    )

    files = await file_service.list_files(user_id=user_id, skip=skip, limit=limit)

    file_responses = [
        SampleFileResponseSchema(
            file_id=f.file_id,
            filename=f.filename,
            size=f.size,
            content_type=f.content_type,
            created_at=f.created_at,
        )
        for f in files
    ]

    logger.info(
        "サンプルファイル一覧を取得しました",
        count=len(file_responses),
    )

    return SampleFileListResponse(files=file_responses, total=len(file_responses))
