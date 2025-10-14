"""ファイルアップロード/ダウンロードAPIルート。"""

from io import BytesIO

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import CurrentUserOptionalDep, FileServiceDep
from app.schemas.file import FileDeleteResponse, FileInfo, FileListResponse, FileUploadResponse

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileUploadResponse:
    """
    ファイルをアップロードします。

    Args:
        file: アップロードするファイル
        file_service: ファイルサービスインスタンス
        current_user: オプションの現在のユーザー

    Returns:
        ファイル情報を含むファイルアップロードレスポンス
    """
    # Reset file pointer
    await file.seek(0)

    # Upload file using service
    user_id = current_user.id if current_user else None
    db_file = await file_service.upload_file(file, user_id)

    return FileUploadResponse(
        file_id=db_file.file_id,
        filename=db_file.original_filename,
        size=db_file.size,
        content_type=db_file.content_type,
        message="File uploaded successfully",
    )


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    file_service: FileServiceDep = None,
) -> StreamingResponse:
    """
    ファイルをダウンロードします。

    Args:
        file_id: ファイル識別子
        file_service: ファイルサービスインスタンス

    Returns:
        ファイル内容を含むストリーミングレスポンス
    """
    # Download file using service
    contents, filename, content_type = await file_service.download_file(file_id)

    # Return as streaming response
    return StreamingResponse(
        BytesIO(contents),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    file_service: FileServiceDep = None,
) -> FileDeleteResponse:
    """
    ファイルを削除します。

    Args:
        file_id: ファイル識別子
        file_service: ファイルサービスインスタンス

    Returns:
        ファイル削除レスポンス
    """
    await file_service.delete_file(file_id)
    return FileDeleteResponse(
        file_id=file_id,
        message=f"File {file_id} deleted successfully",
    )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    skip: int = 0,
    limit: int = 100,
    file_service: FileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileListResponse:
    """
    アップロードされた全てのファイルを一覧表示します。

    Args:
        skip: スキップするファイル数
        limit: 返す最大ファイル数
        file_service: ファイルサービスインスタンス
        current_user: オプションの現在のユーザー

    Returns:
        ファイル情報を含むファイルのリスト
    """
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    # List files using service
    files = await file_service.list_files(user_id=user_id, skip=skip, limit=limit)

    # Convert to FileInfo schemas
    file_infos = [
        FileInfo(
            file_id=f.file_id,
            filename=f.original_filename,
            size=f.size,
            content_type=f.content_type,
            created_at=f.created_at,
        )
        for f in files
    ]

    return FileListResponse(files=file_infos, total=len(file_infos))
