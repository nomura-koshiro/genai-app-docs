"""ドライバーツリー ツリー管理APIエンドポイント。

このモジュールは、ドライバーツリーのツリー管理に関するAPIエンドポイントを定義します。

主な機能:
    - 新規ツリー作成（POST /api/v1/project/{project_id}/driver-tree/tree）
    - ツリー一覧取得（GET /api/v1/project/{project_id}/driver-tree/tree）
    - ツリー取得（GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}）
    - 数式/データインポート（POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/import）
    - ツリーリセット（POST /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/reset）
    - ツリー削除（DELETE /api/v1/project/{project_id}/driver-tree/tree/{tree_id}）
    - 業界分類/業界/ドライバーツリー型/KPI選択肢取得（GET /api/v1/project/{project_id}/driver-tree/category）
    - 数式取得（GET /api/v1/project/{project_id}/driver-tree/formula）
    - ドライバーツリー計算結果取得（GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/data）
    - シミュレーションファイルダウンロード（GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/output）
"""

import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from app.api.core import DriverTreeServiceDep, ProjectMemberDep
from app.core.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.driver_tree import (
    DriverTreeCalculatedDataResponse,
    DriverTreeCategoryListResponse,
    DriverTreeCreateTreeRequest,
    DriverTreeCreateTreeResponse,
    DriverTreeDeleteResponse,
    DriverTreeFormulaGetResponse,
    DriverTreeGetTreeResponse,
    DriverTreeImportFormulaRequest,
    DriverTreeInfo,
    DriverTreeListResponse,
    DriverTreeResetResponse,
    TreePoliciesResponse,
)

logger = get_logger(__name__)

driver_tree_trees_router = APIRouter()


# ================================================================================
# ツリー CRUD
# ================================================================================


@driver_tree_trees_router.post(
    "/project/{project_id}/driver-tree/tree",
    response_model=DriverTreeCreateTreeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新規ツリー作成",
    description="""
    新規ツリーを作成します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - DriverTreeCreateTreeRequest: ドライバーツリー作成リクエスト
            - name (str): ツリー名（必須）
            - description (str): 説明（オプション）

    レスポンス:
        - DriverTreeCreateTreeResponse: ドライバーツリー作成レスポンス
            - tree_id (uuid): ツリーID
            - name (str): ツリー名
            - description (str): 説明
            - created_at (datetime): 作成日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def create_tree(
    project_id: uuid.UUID,
    tree_data: DriverTreeCreateTreeRequest,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeCreateTreeResponse:
    """新規ツリーを作成します。"""
    logger.info(
        "新規ツリー作成リクエスト",
        user_id=str(member.user_id),
        project_id=str(project_id),
        tree_name=tree_data.name,
        action="create_tree",
    )

    tree = await tree_service.create_tree(
        project_id=project_id,
        name=tree_data.name,
        description=tree_data.description,
        user_id=member.user_id,
    )

    logger.info(
        "ツリーを作成しました",
        user_id=str(member.user_id),
        project_id=str(project_id),
        tree_name=tree_data.name,
    )

    return DriverTreeCreateTreeResponse(**tree)


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/tree",
    response_model=DriverTreeListResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリー一覧取得",
    description="""
    ツリーの一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - DriverTreeListResponse: ドライバーツリー一覧レスポンス
            - trees (list): ツリー一覧
                - tree_id (uuid): ツリーID
                - name (str): ツリー名
                - description (str): 説明
                - created_at (datetime): 作成日時
                - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_trees(
    project_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeListResponse:
    """ツリー一覧を取得します。"""
    logger.info(
        "ツリー一覧取得リクエスト",
        user_id=str(member.user_id),
        project_id=str(project_id),
        action="list_trees",
    )

    result = await tree_service.list_trees(project_id, member.user_id)

    logger.info(
        "ツリー一覧を取得しました",
        user_id=str(member.user_id),
        project_id=str(project_id),
        count=len(result.get("trees", [])),
    )

    return DriverTreeListResponse(**result)


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/tree/{tree_id}",
    response_model=DriverTreeGetTreeResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリー取得",
    description="""
    ツリーの全体構造を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    レスポンス:
        - DriverTreeGetTreeResponse: ドライバーツリー取得レスポンス
            - tree_id (uuid): ツリーID
            - name (str): ツリー名
            - description (str): 説明
            - root (dict): ルートノード
            - nodes (list): ノード情報リスト
            - relationship (list): 関係リスト

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def get_tree(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeGetTreeResponse:
    """ツリーを取得します。"""
    logger.info(
        "ツリー取得リクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        action="get_tree",
    )

    tree = await tree_service.get_tree(project_id, tree_id, member.user_id)

    logger.info(
        "ツリーを取得しました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
    )

    return DriverTreeGetTreeResponse(tree=DriverTreeInfo.model_validate(tree))


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/tree/{tree_id}/policy",
    response_model=TreePoliciesResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリー施策一覧取得",
    description="""
    ツリーに紐づくすべてのノードの施策を一括で取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    レスポンス:
        - TreePoliciesResponse: ツリー施策一覧レスポンス
            - tree_id (uuid): ツリーID
            - policies (list[TreePolicyItem]): 施策一覧
                - policy_id (uuid): 施策ID
                - node_id (uuid): ノードID
                - node_label (str): ノード名
                - label (str): 施策名
                - description (str | None): 説明
                - impact_type (str): 影響タイプ（加算/減算/乗算/除算）
                - impact_value (float): 影響値
                - status (str): 施策状態（active/inactive）
            - total_count (int): 施策総数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def get_tree_policies(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> TreePoliciesResponse:
    """ツリー施策一覧を取得します。"""
    logger.info(
        "ツリー施策一覧取得リクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        action="get_tree_policies",
    )

    result = await tree_service.get_tree_policies(project_id, tree_id, member.user_id)

    logger.info(
        "ツリー施策一覧を取得しました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        total_count=result.get("total_count", 0),
    )

    return TreePoliciesResponse(**result)


@driver_tree_trees_router.post(
    "/project/{project_id}/driver-tree/tree/{tree_id}/import",
    response_model=DriverTreeGetTreeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="数式/データインポート",
    description="""
    ツリーに数式データをインポートします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    リクエストボディ:
        - DriverTreeImportFormulaRequest: 数式インポートリクエスト
            - position_x (int): ルートノードX座標
            - position_y (int): ルートノードY座標
            - formulas (list[str]): 数式リスト
            - sheet_id (uuid): 入力シートID（オプション）

    レスポンス:
        - DriverTreeGetTreeResponse: ドライバーツリー取得レスポンス（ツリー全体の最新構造）

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def import_formula(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    import_data: DriverTreeImportFormulaRequest,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeGetTreeResponse:
    """数式をインポートします。"""
    logger.info(
        "数式/データインポートリクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        formula_count=len(import_data.formulas),
        action="import_formula",
    )

    tree = await tree_service.import_formula(
        project_id=project_id,
        tree_id=tree_id,
        position_x=import_data.position_x,
        position_y=import_data.position_y,
        formulas=import_data.formulas,
        sheet_id=import_data.sheet_id,
        user_id=member.user_id,
    )

    logger.info(
        "数式をインポートしました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        formula_count=len(import_data.formulas),
    )

    return DriverTreeGetTreeResponse(tree=DriverTreeInfo.model_validate(tree))


@driver_tree_trees_router.post(
    "/project/{project_id}/driver-tree/tree/{tree_id}/reset",
    response_model=DriverTreeResetResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリーリセット",
    description="""
    ツリーを初期状態にリセットします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    レスポンス:
        - DriverTreeResetResponse: ドライバーツリーリセットレスポンス
            - tree (dict): リセット後のツリー全体構造
            - reset_at (datetime): リセット日時

    ステータスコード:
        - 200: リセット成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def reset_tree(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeResetResponse:
    """ツリーをリセットします。"""
    logger.info(
        "ツリーリセットリクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        action="reset_tree",
    )

    result = await tree_service.reset_tree(project_id, tree_id, member.user_id)

    logger.info(
        "ツリーをリセットしました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
    )

    return DriverTreeResetResponse(**result)


@driver_tree_trees_router.delete(
    "/project/{project_id}/driver-tree/tree/{tree_id}",
    response_model=DriverTreeDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="ツリー削除",
    description="""
    ツリーを完全に削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    レスポンス:
        - DriverTreeDeleteResponse: ドライバーツリー削除レスポンス
            - success (bool): 成功フラグ
            - deleted_at (datetime): 削除日時

    ステータスコード:
        - 200: 削除成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def delete_tree(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeDeleteResponse:
    """ツリーを削除します。"""
    logger.info(
        "ツリー削除リクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        action="delete_tree",
    )

    result = await tree_service.delete_tree(project_id, tree_id, member.user_id)

    logger.info(
        "ツリーを削除しました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
    )

    return DriverTreeDeleteResponse(**result)


@driver_tree_trees_router.post(
    "/project/{project_id}/driver-tree/tree/{tree_id}/duplicate",
    response_model=DriverTreeGetTreeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ツリー複製",
    description="""
    指定されたIDのドライバーツリーを複製します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    ツリーとその関連データ（ノード、リレーションシップ）を深いコピーで複製します。

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - 複製元ツリーID（必須）

    レスポンス:
        - DriverTreeGetTreeResponse: 複製されたツリー情報

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def duplicate_tree(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,
    tree_service: DriverTreeServiceDep,
) -> DriverTreeGetTreeResponse:
    """ドライバーツリーを複製します。"""
    logger.info(
        "ツリー複製リクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        action="duplicate_tree",
    )

    result = await tree_service.duplicate_tree(project_id, tree_id, member.user_id)

    logger.info(
        "ツリーを複製しました",
        user_id=str(member.user_id),
        original_tree_id=str(tree_id),
        new_tree_id=str(result.get("tree_id")),
    )

    return DriverTreeGetTreeResponse(tree=DriverTreeInfo.model_validate(result))


# ================================================================================
# マスタデータ取得
# ================================================================================


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/category",
    response_model=DriverTreeCategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="業界分類一覧取得",
    description="""
    業界分類・業界名・ドライバー型の階層構造を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - DriverTreeCategoryListResponse: カテゴリ一覧レスポンス
            - categories: 業界分類リスト
                - category_id: int - 業界分類ID
                - category_name: str - 業界分類名
                - industries: 業界名リスト
                    - industry_id: int - 業界名ID
                    - industry_name: str - 業界名
                    - driver_types: ドライバー型リスト
                        - driver_type_id: int - ドライバー型ID
                        - driver_type: str - ドライバー型名

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def get_categories(
    project_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeCategoryListResponse:
    """業界分類一覧を取得します。"""
    logger.info(
        "業界分類一覧取得リクエスト",
        user_id=str(member.user_id),
        project_id=str(project_id),
        action="get_categories",
    )

    result = await tree_service.get_categories(project_id, member.user_id)

    logger.info(
        "業界分類一覧を取得しました",
        user_id=str(member.user_id),
        project_id=str(project_id),
        category_count=len(result.get("categories", [])),
    )

    return DriverTreeCategoryListResponse(**result)


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/formula",
    response_model=DriverTreeFormulaGetResponse,
    status_code=status.HTTP_200_OK,
    summary="数式取得",
    description="""
    指定されたドライバー型とKPIに対応する数式を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    クエリパラメータ:
        - driver_type_id: int - ドライバー型ID（必須）
        - kpi: str - KPI（売上 | 原価 | 販管費 | 粗利 | 営業利益 | EBITDA 、必須）

    レスポンス:
        - DriverTreeFormulaGetResponse: 数式取得レスポンス
            - formula: 数式情報
                - formula_id: uuid - 数式ID
                - driver_type_id: int - ドライバー型ID
                - driver_type: str - ドライバー型名
                - kpi: str - KPI
                - formulas: list[str] - 数式リスト

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: 数式が見つからない
    """,
)
@handle_service_errors
async def get_formulas(
    project_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
    driver_type_id: int = Query(..., description="ドライバー型ID"),
    kpi: str = Query(..., description="KPI（売上 | 原価 | 販管費 | 粗利 | 営業利益 | EBITDA）"),
) -> DriverTreeFormulaGetResponse:
    """数式を取得します。"""
    logger.info(
        "数式取得リクエスト",
        user_id=str(member.user_id),
        project_id=str(project_id),
        driver_type_id=driver_type_id,
        kpi=kpi,
        action="get_formulas",
    )

    result = await tree_service.get_formulas(project_id, driver_type_id, kpi, member.user_id)

    logger.info(
        "数式を取得しました",
        user_id=str(member.user_id),
        project_id=str(project_id),
        driver_type_id=driver_type_id,
        kpi=kpi,
    )

    return DriverTreeFormulaGetResponse(**result)


# ================================================================================
# 計算・出力
# ================================================================================


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/tree/{tree_id}/data",
    response_model=DriverTreeCalculatedDataResponse,
    status_code=status.HTTP_200_OK,
    summary="ドライバーツリー計算結果取得",
    description="""
    ツリー全体の計算を実行し結果を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    レスポンス:
        - DriverTreeCalculatedDataResponse: 計算結果レスポンス
            - calculated_data_list (list): 計算データ一覧
                - node_id (uuid): ノードID
                - label (str): ノード名
                - columns (list[str]): カラム名リスト
                - records (list): データレコード

    ステータスコード:
        - 200: 計算成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
        - 422: 計算エラー（数式エラー、データ不足等）
    """,
)
@handle_service_errors
async def get_tree_data(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
) -> DriverTreeCalculatedDataResponse:
    """ツリー計算結果を取得します。"""
    logger.info(
        "ドライバーツリー計算結果取得リクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        action="get_tree_data",
    )

    result = await tree_service.get_tree_data(project_id, tree_id, member.user_id)

    logger.info(
        "ドライバーツリー計算結果を取得しました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
    )

    return DriverTreeCalculatedDataResponse(**result)


@driver_tree_trees_router.get(
    "/project/{project_id}/driver-tree/tree/{tree_id}/output",
    status_code=status.HTTP_200_OK,
    summary="シミュレーションファイルダウンロード",
    description="""
    シミュレーション結果をExcel/CSV形式でエクスポートします。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - tree_id: uuid - ツリーID（必須）

    クエリパラメータ:
        - format: str - 出力形式（"xlsx"|"csv"、デフォルト: "xlsx"）

    レスポンス:
        - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        - File: シミュレーション結果ファイル

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: ツリーが見つからない
    """,
)
@handle_service_errors
async def download_simulation_output(
    project_id: uuid.UUID,
    tree_id: uuid.UUID,
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    tree_service: DriverTreeServiceDep,
    format: str = Query("xlsx", description="出力形式（xlsx|csv）"),
) -> StreamingResponse:
    """シミュレーション結果をダウンロードします。"""
    logger.info(
        "シミュレーションファイルダウンロードリクエスト",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        format=format,
        action="download_simulation_output",
    )

    file_stream = await tree_service.download_simulation_output(project_id, tree_id, format, member.user_id)

    logger.info(
        "シミュレーションファイルをダウンロードしました",
        user_id=str(member.user_id),
        tree_id=str(tree_id),
        format=format,
    )

    return file_stream
