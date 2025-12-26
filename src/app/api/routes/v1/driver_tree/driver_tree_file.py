"""ドライバーツリー ファイル管理APIエンドポイント。

このモジュールは、ドライバーツリーのファイル管理に関するAPIエンドポイントを定義します。

主な機能:
    - ファイルアップロード（POST /api/v1/project/{project_id}/driver-tree/file）
    - アップロード済みファイル削除（DELETE /api/v1/project/{project_id}/driver-tree/file/{file_id}）
    - アップロード済みファイル一覧取得（GET /api/v1/project/{project_id}/driver-tree/file）
    - 選択済みシート一覧取得（GET /api/v1/project/{project_id}/driver-tree/sheet）
    - シート選択送信（POST /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}）
    - 選択済みシート削除（DELETE /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}）
    - データカラム設定送信（PATCH /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column）
"""

import uuid

from fastapi import APIRouter, File, UploadFile, status

from app.api.core import CurrentUserAccountDep, DriverTreeFileServiceDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.driver_tree import (
    DriverTreeColumnSetupRequest,
    DriverTreeColumnSetupResponse,
    DriverTreeFileDeleteResponse,
    DriverTreeFileUploadResponse,
    DriverTreeSelectedSheetListResponse,
    DriverTreeSheetDeleteResponse,
    DriverTreeSheetSelectResponse,
    DriverTreeUploadedFileListResponse,
)

logger = get_logger(__name__)

driver_tree_files_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@driver_tree_files_router.get(
    "/project/{project_id}/driver-tree/file",
    response_model=DriverTreeUploadedFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="アップロード済みファイル一覧取得",
    description="""
    ユーザーがアップロードした全ファイルの一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - DriverTreeUploadedFileListResponse: アップロード済みファイル一覧レスポンス
            - files (list): アップロード済みファイル一覧
                - file_id (uuid): ファイルID
                - filename (str): ファイル名
                - file_size (int): ファイルサイズ（バイト）
                - uploaded_at (datetime): アップロード日時
                - sheets (list): シート一覧
                    - sheet_id (uuid): シートID
                    - sheet_name (str): シート名

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_uploaded_files(
    project_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
) -> DriverTreeUploadedFileListResponse:
    """アップロード済みファイル一覧を取得します。"""
    logger.info(
        "アップロード済みファイル一覧取得リクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="list_uploaded_files",
    )

    result = await file_service.list_uploaded_files(project_id, current_user.id)

    logger.info(
        "アップロード済みファイル一覧を取得しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        count=len(result.get("files", [])),
    )

    return DriverTreeUploadedFileListResponse(**result)


@driver_tree_files_router.get(
    "/project/{project_id}/driver-tree/sheet",
    response_model=DriverTreeSelectedSheetListResponse,
    status_code=status.HTTP_200_OK,
    summary="選択済みシート一覧取得",
    description="""
    選択済みシートの一覧を取得します。

    シート選択API（POST /sheet/{sheet_id}）で選択されたシートのみを返します。
    各シートのカラム情報（軸設定）も含まれます。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - DriverTreeSelectedSheetListResponse: 選択済みシート一覧レスポンス
            - files (list): ファイル一覧（選択済みシートを含むファイルのみ）
                - file_id (uuid): ファイルID
                - filename (str): ファイル名
                - uploaded_at (datetime): アップロード日時
                - sheets (list): 選択済みシート一覧
                    - sheet_id (uuid): シートID
                    - sheet_name (str): シート名
                    - columns (list): カラムリスト
                        - column_id (uuid): カラムID（一意識別子）
                        - column_name (str): カラム名
                        - role (str): カラムの役割（推移|軸|値|利用しない）
                        - items (list[str]): 項目例（最大5件）

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_selected_sheets(
    project_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
) -> DriverTreeSelectedSheetListResponse:
    """選択済みシート一覧を取得します。"""
    logger.info(
        "選択済みシート一覧取得リクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="list_selected_sheets",
    )

    result = await file_service.list_selected_sheets(project_id, current_user.id)

    logger.info(
        "選択済みシート一覧を取得しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        count=len(result.get("files", [])),
    )

    return DriverTreeSelectedSheetListResponse(**result)


# ================================================================================
# POST Endpoints
# ================================================================================


@driver_tree_files_router.post(
    "/project/{project_id}/driver-tree/file",
    response_model=DriverTreeFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ファイルアップロード",
    description="""
    Excelファイルをアップロードします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - Content-Type: multipart/form-data
        - file: File - Excelファイル（.xlsx/.xls）

    レスポンス:
        - DriverTreeFileUploadResponse: ドライバーツリーファイルアップロードレスポンス
            - files (list): アップロード済みファイル一覧
                - file_id (uuid): ファイルID
                - filename (str): ファイル名
                - file_size (int): ファイルサイズ（バイト）
                - uploaded_at (datetime): アップロード日時
                - sheets (list): シート一覧
                    - sheet_id (uuid): シートID
                    - sheet_name (str): シート名

    ステータスコード:
        - 201: アップロード成功
        - 400: 不正なファイル形式
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 413: ファイルサイズ超過
    """,
)
@handle_service_errors
async def upload_file(
    project_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
    file: UploadFile = File(...),
) -> DriverTreeFileUploadResponse:
    """ファイルをアップロードします。"""
    logger.info(
        "ファイルアップロードリクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        filename=file.filename,
        content_type=file.content_type,
        action="upload_file",
    )

    uploaded = await file_service.upload_file(project_id, file, current_user.id)

    logger.info(
        "ファイルをアップロードしました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        filename=file.filename,
    )

    return DriverTreeFileUploadResponse(**uploaded)


@driver_tree_files_router.post(
    "/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}",
    response_model=DriverTreeSheetSelectResponse,
    status_code=status.HTTP_200_OK,
    summary="シート選択送信",
    description="""
    シートを選択して送信します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）
        - sheet_id: uuid - シートID（必須）

    レスポンス:
        - DriverTreeSheetSelectResponse: ドライバーツリーシート選択レスポンス
            - success (bool) : 成功フラグ (選択済みの場合False)
            - files (list): ファイル一覧（選択済みシートを含むファイルのみ）
                - file_id (uuid): ファイルID
                - filename (str): ファイル名
                - uploaded_at (datetime): アップロード日時
                - sheets (list): 選択済みシート一覧
                    - sheet_id (uuid): シートID
                    - sheet_name (str): シート名
                    - columns (list): カラムリスト
                        - column_id (uuid): カラムID（一意識別子）
                        - column_name (str): カラム名
                        - role (str): カラムの役割（推移|軸|値|利用しない）
                        - items (list[str]): 項目例（最大5件）

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルまたはシートが見つからない
    """,
)
@handle_service_errors
async def select_sheet(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    sheet_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
) -> DriverTreeSheetSelectResponse:
    """シートを選択します。"""
    logger.info(
        "シート選択送信リクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        sheet_id=sheet_id,
        action="select_sheet",
    )

    result = await file_service.select_sheet(project_id, file_id, sheet_id, current_user.id)

    logger.info(
        "シートを選択しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        sheet_id=sheet_id,
    )

    return DriverTreeSheetSelectResponse(**result)


# ================================================================================
# PATCH Endpoints
# ================================================================================


@driver_tree_files_router.patch(
    "/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column",
    response_model=DriverTreeColumnSetupResponse,
    status_code=status.HTTP_200_OK,
    summary="データカラム設定送信",
    description="""
    各シートのデータカラムの役割を設定します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）
        - sheet_id: uuid - シートID（必須）

    リクエストボディ:
        - columns: list[DriverTreeColumnSetupItem] - カラム情報リスト
            - column_id: uuid - カラムID（一意識別子）
            - role: DriverTreeColumnRoleEnum - カラム設定（"推移"|"軸"|"値"|"利用しない"）

    レスポンス:
        - DriverTreeColumnSetupResponse: カラム設定更新結果
            - success (bool): 成功フラグ
            - columns (list): カラム情報リスト
                - column_id (uuid): カラムID（一意識別子）
                - column_name (str): カラム名
                - role (str): カラムの役割
                - items (list[str]): 項目例

    ステータスコード:
        - 200: 成功
        - 400: 不正なカラム設定
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルまたはシートが見つからない
    """,
)
@handle_service_errors
async def update_column_config(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    sheet_id: uuid.UUID,
    request: DriverTreeColumnSetupRequest,
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
) -> DriverTreeColumnSetupResponse:
    """カラム設定を更新します。"""
    logger.info(
        "データカラム設定送信リクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        sheet_id=str(sheet_id),
        column_count=len(request.columns),
        action="update_column_config",
    )

    result = await file_service.update_column_config(project_id, file_id, sheet_id, request.columns, current_user.id)

    logger.info(
        "カラム設定を更新しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        sheet_id=str(sheet_id),
    )

    return DriverTreeColumnSetupResponse(**result)


# ================================================================================
# DELETE Endpoints
# ================================================================================


@driver_tree_files_router.delete(
    "/project/{project_id}/driver-tree/file/{file_id}",
    response_model=DriverTreeFileDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="ファイル削除",
    description="""
    アップロード済みファイルを削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）

    レスポンス:
        - DriverTreeFileDeleteResponse: ファイル削除レスポンス
            - files (list): 削除後のアップロード済みファイル一覧
                - file_id (uuid): ファイルID
                - filename (str): ファイル名
                - file_size (int): ファイルサイズ（バイト）
                - uploaded_at (datetime): アップロード日時
                - sheets (list): シート一覧
                    - sheet_id (uuid): シートID
                    - sheet_name (str): シート名

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
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
) -> DriverTreeFileDeleteResponse:
    """ファイルを削除します。"""
    logger.info(
        "ファイル削除リクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        action="delete_file",
    )

    result = await file_service.delete_file(project_id, file_id, current_user.id)

    logger.info(
        "ファイルを削除しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
    )

    return DriverTreeFileDeleteResponse(**result)


@driver_tree_files_router.delete(
    "/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}",
    response_model=DriverTreeSheetDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="選択済みシート削除",
    description="""
    選択済みシートを削除します。

    シート選択を解除し、関連するDataFrameとaxis_configを削除します。
    物理ファイルやシート自体は削除されません。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - file_id: uuid - ファイルID（必須）
        - sheet_id: uuid - シートID（必須）

    レスポンス:
        - DriverTreeSheetDeleteResponse: シート削除レスポンス
            - success (bool): 成功フラグ
            - files (list): 削除後の選択済みシート一覧
                - file_id (uuid): ファイルID
                - filename (str): ファイル名
                - uploaded_at (datetime): アップロード日時
                - sheets (list): 選択済みシート一覧
                    - sheet_id (uuid): シートID
                    - sheet_name (str): シート名
                    - columns (list): カラムリスト

    ステータスコード:
        - 200: 削除成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ファイルまたはシートが見つからない
    """,
)
@handle_service_errors
async def delete_sheet(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    sheet_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    file_service: DriverTreeFileServiceDep,
) -> DriverTreeSheetDeleteResponse:
    """選択済みシートを削除します。"""
    logger.info(
        "シート削除リクエスト",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        sheet_id=str(sheet_id),
        action="delete_sheet",
    )

    result = await file_service.delete_sheet(project_id, file_id, sheet_id, current_user.id)

    logger.info(
        "シートを削除しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
        file_id=str(file_id),
        sheet_id=str(sheet_id),
    )

    return DriverTreeSheetDeleteResponse(**result)
