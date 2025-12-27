"""ドライバーツリーAPI v2エンドポイント。

パス変更:
    - /project/{id}/driver-tree/tree → /project/{id}/tree
    - /project/{id}/driver-tree/node → /project/{id}/node
    - /project/{id}/driver-tree/file → /project/{id}/tree-file
    - /project/{id}/driver-tree/category → /project/{id}/tree-category
    - /project/{id}/driver-tree/formula → /project/{id}/tree-formula
"""

import uuid

from fastapi import APIRouter, Body, Path, Query, status
from fastapi.responses import StreamingResponse

from app.api.core import DriverTreeServiceDep, ProjectMemberDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.driver_tree import (
    DriverTreeCategoryResponse,
    DriverTreeCreate,
    DriverTreeDataFrameListResponse,
    DriverTreeFileCreate,
    DriverTreeFileListResponse,
    DriverTreeFileResponse,
    DriverTreeFileSheetColumnUpdate,
    DriverTreeFileSheetCreate,
    DriverTreeFileSheetListResponse,
    DriverTreeFileSheetResponse,
    DriverTreeFormulaListResponse,
    DriverTreeImportRequest,
    DriverTreeListResponse,
    DriverTreeNodeCreate,
    DriverTreeNodeResponse,
    DriverTreeNodeUpdate,
    DriverTreePolicyCreate,
    DriverTreePolicyListResponse,
    DriverTreePolicyResponse,
    DriverTreePolicyUpdate,
    DriverTreeResponse,
)

logger = get_logger(__name__)

tree_router = APIRouter()
tree_file_router = APIRouter()
tree_node_router = APIRouter()


# ================================================================================
# ツリー CRUD
# ================================================================================


@tree_router.post(
    "/project/{project_id}/tree",
    response_model=DriverTreeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新規ツリー作成",
)
@handle_service_errors
async def create_tree(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_create: DriverTreeCreate = Body(...),
) -> DriverTreeResponse:
    """新規ドライバーツリーを作成します。"""
    return await tree_service.create_tree(project_id, tree_create)


@tree_router.get(
    "/project/{project_id}/tree",
    response_model=DriverTreeListResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリー一覧取得",
)
@handle_service_errors
async def list_trees(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
) -> DriverTreeListResponse:
    """ツリー一覧を取得します。"""
    return await tree_service.list_trees(project_id, skip, limit)


@tree_router.get(
    "/project/{project_id}/tree/{tree_id}",
    response_model=DriverTreeResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリー詳細取得",
)
@handle_service_errors
async def get_tree(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
) -> DriverTreeResponse:
    """ツリー詳細を取得します。"""
    return await tree_service.get_tree(project_id, tree_id)


@tree_router.post(
    "/project/{project_id}/tree/{tree_id}/import",
    response_model=DriverTreeResponse,
    status_code=status.HTTP_200_OK,
    summary="数式/データインポート",
)
@handle_service_errors
async def import_tree(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
    import_request: DriverTreeImportRequest = Body(...),
) -> DriverTreeResponse:
    """数式とデータをインポートします。"""
    return await tree_service.import_tree(project_id, tree_id, import_request)


@tree_router.post(
    "/project/{project_id}/tree/{tree_id}/reset",
    response_model=DriverTreeResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリーリセット",
)
@handle_service_errors
async def reset_tree(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
) -> DriverTreeResponse:
    """ツリーをリセットします。"""
    return await tree_service.reset_tree(project_id, tree_id)


@tree_router.delete(
    "/project/{project_id}/tree/{tree_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ツリー削除",
)
@handle_service_errors
async def delete_tree(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
) -> None:
    """ツリーを削除します。"""
    await tree_service.delete_tree(project_id, tree_id)


@tree_router.post(
    "/project/{project_id}/tree/{tree_id}/duplicate",
    response_model=DriverTreeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ツリー複製",
)
@handle_service_errors
async def duplicate_tree(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="複製元ツリーID"),
) -> DriverTreeResponse:
    """ツリーを複製します。"""
    return await tree_service.duplicate_tree(project_id, tree_id)


# ================================================================================
# カテゴリ・数式
# ================================================================================


@tree_router.get(
    "/project/{project_id}/tree-category",
    response_model=DriverTreeCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="カテゴリ取得",
)
@handle_service_errors
async def get_categories(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
) -> DriverTreeCategoryResponse:
    """業界分類/業界/ドライバーツリー型/KPI選択肢を取得します。"""
    return await tree_service.get_categories(project_id)


@tree_router.get(
    "/project/{project_id}/tree-formula",
    response_model=DriverTreeFormulaListResponse,
    status_code=status.HTTP_200_OK,
    summary="数式取得",
)
@handle_service_errors
async def get_formulas(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    category_id: uuid.UUID | None = Query(None, description="カテゴリID"),
) -> DriverTreeFormulaListResponse:
    """数式一覧を取得します。"""
    return await tree_service.get_formulas(project_id, category_id)


# ================================================================================
# 計算結果・出力
# ================================================================================


@tree_router.get(
    "/project/{project_id}/tree/{tree_id}/data",
    response_model=DriverTreeDataFrameListResponse,
    status_code=status.HTTP_200_OK,
    summary="計算結果取得",
)
@handle_service_errors
async def get_tree_data(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
) -> DriverTreeDataFrameListResponse:
    """ツリーの計算結果を取得します。"""
    return await tree_service.get_tree_data(project_id, tree_id)


@tree_router.get(
    "/project/{project_id}/tree/{tree_id}/output",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="シミュレーションファイルダウンロード",
)
@handle_service_errors
async def download_tree_output(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
) -> StreamingResponse:
    """シミュレーション結果ファイルをダウンロードします。"""
    return await tree_service.download_tree_output(project_id, tree_id)


# ================================================================================
# ファイル管理
# ================================================================================


@tree_file_router.get(
    "/project/{project_id}/tree-file",
    response_model=DriverTreeFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="アップロード済みファイル一覧取得",
)
@handle_service_errors
async def list_tree_files(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
) -> DriverTreeFileListResponse:
    """アップロード済みファイル一覧を取得します。"""
    return await tree_service.list_tree_files(project_id)


@tree_file_router.get(
    "/project/{project_id}/tree-sheet",
    response_model=DriverTreeFileSheetListResponse,
    status_code=status.HTTP_200_OK,
    summary="選択済みシート一覧取得",
)
@handle_service_errors
async def list_tree_sheets(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
) -> DriverTreeFileSheetListResponse:
    """選択済みシート一覧を取得します。"""
    return await tree_service.list_tree_sheets(project_id)


@tree_file_router.post(
    "/project/{project_id}/tree-file",
    response_model=DriverTreeFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ファイルアップロード",
)
@handle_service_errors
async def upload_tree_file(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    file_create: DriverTreeFileCreate = Body(...),
) -> DriverTreeFileResponse:
    """ファイルをアップロードします。"""
    return await tree_service.upload_tree_file(project_id, file_create)


@tree_file_router.post(
    "/project/{project_id}/tree-file/{file_id}/sheet/{sheet_id}",
    response_model=DriverTreeFileSheetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="シート選択送信",
)
@handle_service_errors
async def select_tree_sheet(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    file_id: uuid.UUID = Path(..., description="ファイルID"),
    sheet_id: uuid.UUID = Path(..., description="シートID"),
    sheet_create: DriverTreeFileSheetCreate = Body(...),
) -> DriverTreeFileSheetResponse:
    """シートを選択します。"""
    return await tree_service.select_tree_sheet(project_id, file_id, sheet_id, sheet_create)


@tree_file_router.patch(
    "/project/{project_id}/tree-file/{file_id}/sheet/{sheet_id}/column",
    response_model=DriverTreeFileSheetResponse,
    status_code=status.HTTP_200_OK,
    summary="データカラム設定送信",
)
@handle_service_errors
async def update_tree_sheet_column(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    file_id: uuid.UUID = Path(..., description="ファイルID"),
    sheet_id: uuid.UUID = Path(..., description="シートID"),
    column_update: DriverTreeFileSheetColumnUpdate = Body(...),
) -> DriverTreeFileSheetResponse:
    """データカラム設定を更新します。"""
    return await tree_service.update_tree_sheet_column(
        project_id, file_id, sheet_id, column_update
    )


@tree_file_router.delete(
    "/project/{project_id}/tree-file/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="アップロード済みファイル削除",
)
@handle_service_errors
async def delete_tree_file(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    file_id: uuid.UUID = Path(..., description="ファイルID"),
) -> None:
    """アップロード済みファイルを削除します。"""
    await tree_service.delete_tree_file(project_id, file_id)


@tree_file_router.delete(
    "/project/{project_id}/tree-file/{file_id}/sheet/{sheet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="選択済みシート削除",
)
@handle_service_errors
async def delete_tree_sheet(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    file_id: uuid.UUID = Path(..., description="ファイルID"),
    sheet_id: uuid.UUID = Path(..., description="シートID"),
) -> None:
    """選択済みシートを削除します。"""
    await tree_service.delete_tree_sheet(project_id, file_id, sheet_id)


# ================================================================================
# ノード管理
# ================================================================================


@tree_node_router.post(
    "/project/{project_id}/tree/{tree_id}/node",
    response_model=DriverTreeNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ノード作成",
)
@handle_service_errors
async def create_node(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    tree_id: uuid.UUID = Path(..., description="ツリーID"),
    node_create: DriverTreeNodeCreate = Body(...),
) -> DriverTreeNodeResponse:
    """ノードを作成します。"""
    return await tree_service.create_node(project_id, tree_id, node_create)


@tree_node_router.get(
    "/project/{project_id}/node/{node_id}",
    response_model=DriverTreeNodeResponse,
    status_code=status.HTTP_200_OK,
    summary="ノード詳細取得",
)
@handle_service_errors
async def get_node(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
) -> DriverTreeNodeResponse:
    """ノード詳細を取得します。"""
    return await tree_service.get_node(project_id, node_id)


@tree_node_router.patch(
    "/project/{project_id}/node/{node_id}",
    response_model=DriverTreeNodeResponse,
    status_code=status.HTTP_200_OK,
    summary="ノード更新",
)
@handle_service_errors
async def update_node(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
    node_update: DriverTreeNodeUpdate = Body(...),
) -> DriverTreeNodeResponse:
    """ノードを更新します。"""
    return await tree_service.update_node(project_id, node_id, node_update)


@tree_node_router.delete(
    "/project/{project_id}/node/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ノード削除",
)
@handle_service_errors
async def delete_node(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
) -> None:
    """ノードを削除します。"""
    await tree_service.delete_node(project_id, node_id)


@tree_node_router.get(
    "/project/{project_id}/node/{node_id}/preview/output",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="入力ノードプレビューファイルダウンロード",
)
@handle_service_errors
async def download_node_preview(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
) -> StreamingResponse:
    """入力ノードプレビューファイルをダウンロードします。"""
    return await tree_service.download_node_preview(project_id, node_id)


# ================================================================================
# 施策管理
# ================================================================================


@tree_node_router.post(
    "/project/{project_id}/node/{node_id}/policy",
    response_model=DriverTreePolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="施策設定作成",
)
@handle_service_errors
async def create_policy(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
    policy_create: DriverTreePolicyCreate = Body(...),
) -> DriverTreePolicyResponse:
    """施策設定を作成します。"""
    return await tree_service.create_policy(project_id, node_id, policy_create)


@tree_node_router.get(
    "/project/{project_id}/node/{node_id}/policy",
    response_model=DriverTreePolicyListResponse,
    status_code=status.HTTP_200_OK,
    summary="施策設定一覧取得",
)
@handle_service_errors
async def list_policies(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
) -> DriverTreePolicyListResponse:
    """施策設定一覧を取得します。"""
    return await tree_service.list_policies(project_id, node_id)


@tree_node_router.patch(
    "/project/{project_id}/node/{node_id}/policy/{policy_id}",
    response_model=DriverTreePolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="施策設定更新",
)
@handle_service_errors
async def update_policy(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
    policy_id: uuid.UUID = Path(..., description="施策ID"),
    policy_update: DriverTreePolicyUpdate = Body(...),
) -> DriverTreePolicyResponse:
    """施策設定を更新します。"""
    return await tree_service.update_policy(project_id, node_id, policy_id, policy_update)


@tree_node_router.delete(
    "/project/{project_id}/node/{node_id}/policy/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="施策設定削除",
)
@handle_service_errors
async def delete_policy(
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    node_id: uuid.UUID = Path(..., description="ノードID"),
    policy_id: uuid.UUID = Path(..., description="施策ID"),
) -> None:
    """施策設定を削除します。"""
    await tree_service.delete_policy(project_id, node_id, policy_id)


__all__ = ["tree_router", "tree_file_router", "tree_node_router"]
