"""ドライバーツリー ノード管理APIエンドポイント。

このモジュールは、ドライバーツリーのノード管理に関するAPIエンドポイントを定義します。

主な機能:
    - ノード作成（POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/node）
    - ノード詳細取得（GET /api/v1/project/{project_id}/driver-tree/node/{node_id}）
    - ノード詳細更新（PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id}）
    - ノード削除（DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id}）
    - 入力ノードプレビューファイルダウンロード（GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/preview/output）
    - 施策設定作成（POST /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy）
    - 施策設定一覧取得（GET /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy）
    - 施策設定更新（PATCH /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id}）
    - 施策設定削除（DELETE /api/v1/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id}）
"""

import uuid

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from app.api.core import DriverTreeNodeServiceDep, ProjectMemberDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.driver_tree import (
    DriverTreeCreateNodeRequest,
    DriverTreeNodeCreateResponse,
    DriverTreeNodeDeleteResponse,
    DriverTreeNodeDetailResponse,
    DriverTreeNodeInfo,
    DriverTreeNodePolicyCreateRequest,
    DriverTreeNodePolicyCreateResponse,
    DriverTreeNodePolicyDeleteResponse,
    DriverTreeNodePolicyResponse,
    DriverTreeNodePolicyUpdateRequest,
    DriverTreeNodePolicyUpdateResponse,
    DriverTreeNodeUpdateRequest,
    DriverTreeNodeUpdateResponse,
)

logger = get_logger(__name__)

driver_tree_nodes_router = APIRouter()


# ================================================================================
# ノード CRUD
# ================================================================================


@driver_tree_nodes_router.post(
    "/project/{project_id}/driver-tree/tree/{tree_id}/node",
    response_model=DriverTreeNodeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ノード作成",
    description="""
    ツリーに新規ノードを作成します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    リクエストボディ:
        - DriverTreeCreateNodeRequest: ノード作成リクエスト
            - label (str): ノード名（必須）
            - position_x (int): X座標（必須）
            - position_y (int): Y座標（必須）
            - node_type (str): ノードタイプ（必須）

    レスポンス:
        - DriverTreeNodeCreateResponse: ノード作成レスポンス
            - tree (dict): ツリー全体の最新構造
            - created_node_id (uuid): 作成されたノードID

    ステータスコード:
        - 201: 作成成功
        - 400: 不正なノード設定
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def create_node(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    node_data: DriverTreeCreateNodeRequest,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodeCreateResponse:
    """ノードを作成します。"""
    logger.info(
        "ノード作成リクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        node_label=node_data.label,
        node_type=node_data.node_type,
        action="create_node",
    )

    result = await node_service.create_node(
        project_id=project_id,
        tree_id=tree_id,
        label=node_data.label,
        node_type=node_data.node_type,
        position_x=node_data.position_x,
        position_y=node_data.position_y,
        user_id=member.user_id,
    )

    logger.info(
        "ノードを作成しました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        node_label=node_data.label,
    )

    return DriverTreeNodeCreateResponse(**result)


@driver_tree_nodes_router.get(
    "/project/{project_id}/driver-tree/node/{node_id}",
    response_model=DriverTreeNodeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="ノード詳細取得",
    description="""
    ノードの詳細情報を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）

    レスポンス:
        - DriverTreeNodeDetailResponse: ノード詳細レスポンス
            - node (DriverTreeNodeInfo): ノード詳細情報
                - node_id (uuid): ノードID
                - label (str): ノード名
                - node_type (str): ノードタイプ（入力|計算|定数）
                - position_x (int): X座標
                - position_y (int): Y座標
                - data (DriverTreeNodeData | None): 入力ノードのデータ

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードが見つからない
    """,
)
@handle_service_errors
async def get_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodeDetailResponse:
    """ノード詳細を取得します。"""
    logger.info(
        "ノード詳細取得リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        action="get_node",
    )

    node = await node_service.get_node(project_id, node_id, member.user_id)

    logger.info(
        "ノード詳細を取得しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
    )

    return DriverTreeNodeDetailResponse(node=DriverTreeNodeInfo.model_validate(node))


@driver_tree_nodes_router.patch(
    "/project/{project_id}/driver-tree/node/{node_id}",
    response_model=DriverTreeNodeUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="ノード詳細更新",
    description="""
    ノード情報を更新します（PATCH）。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）

    リクエストボディ:
        - DriverTreeNodeUpdateRequest: ノード更新リクエスト（すべてオプション）
            - label (str): ノード名
            - node_type (str): ノードタイプ
            - position_x (int): X座標
            - position_y (int): Y座標
            - operator (str): 演算子
            - children_id_list (list[uuid]): 子ノードIDリスト

    レスポンス:
        - DriverTreeNodeUpdateResponse: ノード更新レスポンス
            - tree (dict): ツリー全体の最新構造

    ステータスコード:
        - 200: 更新成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードが見つからない
        - 422: バリデーションエラー
    """,
)
@handle_service_errors
async def update_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    update_data: DriverTreeNodeUpdateRequest,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodeUpdateResponse:
    """ノードを更新します。"""
    logger.info(
        "ノード詳細更新リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        action="update_node",
    )

    result = await node_service.update_node(
        project_id=project_id,
        node_id=node_id,
        label=update_data.label,
        node_type=update_data.node_type,
        position_x=update_data.position_x,
        position_y=update_data.position_y,
        operator=update_data.operator,
        children_id_list=update_data.children_id_list,
        user_id=member.user_id,
    )

    logger.info(
        "ノードを更新しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
    )

    return DriverTreeNodeUpdateResponse(**result)


@driver_tree_nodes_router.delete(
    "/project/{project_id}/driver-tree/node/{node_id}",
    response_model=DriverTreeNodeDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="ノード削除",
    description="""
    ノードを削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）

    レスポンス:
        - DriverTreeNodeDeleteResponse: ノード削除レスポンス
            - tree (dict): ツリー全体の最新構造

    ステータスコード:
        - 200: 削除成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードが見つからない
    """,
)
@handle_service_errors
async def delete_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodeDeleteResponse:
    """ノードを削除します。"""
    logger.info(
        "ノード削除リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        action="delete_node",
    )

    result = await node_service.delete_node(project_id, node_id, member.user_id)

    logger.info(
        "ノードを削除しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
    )

    return DriverTreeNodeDeleteResponse(**result)


@driver_tree_nodes_router.get(
    "/project/{project_id}/driver-tree/node/{node_id}/preview/output",
    status_code=status.HTTP_200_OK,
    summary="入力ノードプレビューファイルダウンロード",
    description="""
    ノードデータをCSV形式でエクスポートします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）

    レスポンス:
        - Content-Type: text/csv
        - File: データファイル

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードが見つからない
    """,
)
@handle_service_errors
async def download_node_preview(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> StreamingResponse:
    """ノードデータをダウンロードします。"""
    logger.info(
        "入力ノードプレビューファイルダウンロードリクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        action="download_node_preview",
    )

    csv_stream = await node_service.download_node_preview(project_id, node_id, member.user_id)

    logger.info(
        "入力ノードプレビューファイルをダウンロードしました",
        user_id=str(member.user_id),
        node_id=str(node_id),
    )

    return csv_stream


# ================================================================================
# 施策設定 CRUD
# ================================================================================


@driver_tree_nodes_router.post(
    "/project/{project_id}/driver-tree/node/{node_id}/policy",
    response_model=DriverTreeNodePolicyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="施策設定作成",
    description="""
    施策を設定します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）

    リクエストボディ:
        - DriverTreeNodePolicyCreateRequest: 施策作成リクエスト
            - name (str): 施策名（必須）
            - value (float): 施策値（必須）

    レスポンス:
        - DriverTreeNodePolicyCreateResponse: 施策作成レスポンス
            - node_id (uuid): ノードID
            - policies (list[DriverTreeNodePolicyInfo]): 施策リスト
                - policy_id (uuid): 施策ID
                - name (str): 施策名
                - value (float): 施策値

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードが見つからない
    """,
)
@handle_service_errors
async def create_policy(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    policy_data: DriverTreeNodePolicyCreateRequest,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodePolicyCreateResponse:
    """施策を作成します。"""
    logger.info(
        "施策設定作成リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        policy_name=policy_data.name,
        action="create_policy",
    )

    result = await node_service.create_policy(
        project_id=project_id,
        node_id=node_id,
        name=policy_data.name,
        value=policy_data.value,
        user_id=member.user_id,
    )

    logger.info(
        "施策を作成しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
        policy_name=policy_data.name,
    )

    return DriverTreeNodePolicyCreateResponse(**result)


@driver_tree_nodes_router.get(
    "/project/{project_id}/driver-tree/node/{node_id}/policy",
    response_model=DriverTreeNodePolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="施策設定一覧取得",
    description="""
    ノードに設定されている全施策の一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）

    レスポンス:
        - DriverTreeNodePolicyResponse: 施策一覧レスポンス
            - node_id (uuid): ノードID
            - policies (list[DriverTreeNodePolicyInfo]): 施策リスト
                - policy_id (uuid): 施策ID
                - name (str): 施策名
                - value (float): 施策値

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードが見つからない
    """,
)
@handle_service_errors
async def list_policies(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodePolicyResponse:
    """施策一覧を取得します。"""
    logger.info(
        "施策設定一覧取得リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        action="list_policies",
    )

    result = await node_service.list_policies(project_id, node_id, member.user_id)

    logger.info(
        "施策一覧を取得しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
        count=len(result.get("policies", [])),
    )

    return DriverTreeNodePolicyResponse(**result)


@driver_tree_nodes_router.patch(
    "/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id}",
    response_model=DriverTreeNodePolicyUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="施策設定更新",
    description="""
    施策設定を更新します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）
        - policy_id: uuid - 施策ID（必須）

    リクエストボディ:
        - DriverTreeNodePolicyUpdateRequest: 施策更新リクエスト
            - name (str): 施策名（オプション）
            - value (float): 施策値（オプション）

    レスポンス:
        - DriverTreeNodePolicyUpdateResponse: 施策更新レスポンス
            - node_id (uuid): ノードID
            - policies (list[DriverTreeNodePolicyInfo]): 施策リスト
                - policy_id (uuid): 施策ID
                - name (str): 施策名
                - value (float): 施策値

    ステータスコード:
        - 200: 更新成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードまたは施策が見つからない
    """,
)
@handle_service_errors
async def update_policy(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    policy_id: uuid.UUID,
    update_data: DriverTreeNodePolicyUpdateRequest,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodePolicyUpdateResponse:
    """施策を更新します。"""
    logger.info(
        "施策設定更新リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        policy_id=str(policy_id),
        action="update_policy",
    )

    result = await node_service.update_policy(
        project_id=project_id,
        node_id=node_id,
        policy_id=policy_id,
        name=update_data.name,
        value=update_data.value,
        user_id=member.user_id,
    )

    logger.info(
        "施策を更新しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
        policy_id=str(policy_id),
    )

    return DriverTreeNodePolicyUpdateResponse(**result)


@driver_tree_nodes_router.delete(
    "/project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id}",
    response_model=DriverTreeNodePolicyDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="施策設定削除",
    description="""
    施策設定を削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - node_id: uuid - ノードID（必須）
        - policy_id: uuid - 施策ID（必須）

    レスポンス:
        - DriverTreeNodePolicyDeleteResponse: 施策削除レスポンス
            - node_id (uuid): ノードID
            - policies (list[DriverTreeNodePolicyInfo]): 施策リスト
                - policy_id (uuid): 施策ID
                - name (str): 施策名
                - value (float): 施策値

    ステータスコード:
        - 200: 削除成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ノードまたは施策が見つからない
    """,
)
@handle_service_errors
async def delete_policy(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    policy_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    node_service: DriverTreeNodeServiceDep,
) -> DriverTreeNodePolicyDeleteResponse:
    """施策を削除します。"""
    logger.info(
        "施策設定削除リクエスト",
        user_id=str(member.user_id),
        node_id=str(node_id),
        policy_id=str(policy_id),
        action="delete_policy",
    )

    result = await node_service.delete_policy(project_id, node_id, policy_id, member.user_id)

    logger.info(
        "施策を削除しました",
        user_id=str(member.user_id),
        node_id=str(node_id),
        policy_id=str(policy_id),
    )

    return DriverTreeNodePolicyDeleteResponse(**result)
