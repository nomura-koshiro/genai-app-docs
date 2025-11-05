"""Driver Tree API。

このモジュールは、ドライバーツリー機能のRESTful APIエンドポイントを提供します。
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.dependencies import CurrentUserAzureDep, get_db
from app.api.decorators import async_timeout, handle_service_errors
from app.core.logging import get_logger
from app.schemas.driver_tree import (
    FormulaCreateRequest,
    FormulaResponse,
    KPIListResponse,
    NodeCreate,
    NodeResponse,
    NodeUpdate,
    TreeResponse,
)
from app.services.driver_tree import DriverTreeService

logger = get_logger(__name__)

router = APIRouter()


def get_driver_tree_service(db: AsyncSession = Depends(get_db)) -> DriverTreeService:
    """Driver Treeサービスを取得します。

    Args:
        db: データベースセッション

    Returns:
        DriverTreeService: Driver Treeサービス
    """
    return DriverTreeService(db)


@router.post("/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
@handle_service_errors
async def create_node(
    node_data: NodeCreate,
    current_user: CurrentUserAzureDep,
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> NodeResponse:
    """ノードを作成します。

    Args:
        node_data: ノード作成リクエスト
        current_user: 現在のユーザー
        driver_tree_service: Driver Treeサービス

    Returns:
        NodeResponse: 作成されたノード
    """
    logger.info(
        "ノード作成リクエスト",
        tree_id=str(node_data.tree_id),
        label=node_data.label,
        user_id=str(current_user.id),
        action="create_driver_tree_node",
    )

    node = await driver_tree_service.create_node(
        tree_id=node_data.tree_id,
        label=node_data.label,
        parent_id=node_data.parent_id,
        operator=node_data.operator,
        x=node_data.x,
        y=node_data.y,
    )

    logger.info(
        "ノードを作成しました",
        node_id=str(node.id),
        label=node.label,
    )

    return NodeResponse.model_validate(node)


@router.get("/nodes/{node_id}", response_model=NodeResponse)
@handle_service_errors
async def get_node(
    node_id: uuid.UUID,
    current_user: CurrentUserAzureDep,
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> NodeResponse:
    """ノードを取得します。

    Args:
        node_id: ノードID
        current_user: 現在のユーザー
        driver_tree_service: Driver Treeサービス

    Returns:
        NodeResponse: ノード
    """
    logger.info(
        "ノード取得リクエスト",
        node_id=str(node_id),
        user_id=str(current_user.id),
        action="get_driver_tree_node",
    )

    node = await driver_tree_service.get_node(node_id)

    logger.info(
        "ノードを取得しました",
        node_id=str(node.id),
        label=node.label,
    )

    return NodeResponse.model_validate(node)


@router.put("/nodes/{node_id}", response_model=NodeResponse)
@handle_service_errors
async def update_node(
    node_id: uuid.UUID,
    node_data: NodeUpdate,
    current_user: CurrentUserAzureDep,
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> NodeResponse:
    """ノードを更新します。

    Args:
        node_id: ノードID
        node_data: ノード更新リクエスト
        current_user: 現在のユーザー
        driver_tree_service: Driver Treeサービス

    Returns:
        NodeResponse: 更新されたノード
    """
    logger.info(
        "ノード更新リクエスト",
        node_id=str(node_id),
        user_id=str(current_user.id),
        action="update_driver_tree_node",
    )

    node = await driver_tree_service.update_node(
        node_id=node_id,
        label=node_data.label,
        parent_id=node_data.parent_id,
        operator=node_data.operator,
        x=node_data.x,
        y=node_data.y,
    )

    logger.info(
        "ノードを更新しました",
        node_id=str(node.id),
        label=node.label,
    )

    return NodeResponse.model_validate(node)


@router.post("/trees", response_model=TreeResponse, status_code=status.HTTP_201_CREATED)
@handle_service_errors
@async_timeout(60.0)
async def create_tree_from_formulas(
    formula_data: FormulaCreateRequest,
    current_user: CurrentUserAzureDep,
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> TreeResponse:
    """数式からツリーを作成します。

    Args:
        formula_data: 数式作成リクエスト
        current_user: 現在のユーザー
        driver_tree_service: Driver Treeサービス

    Returns:
        TreeResponse: 作成されたツリー
    """
    logger.info(
        "ツリー作成リクエスト",
        formula_count=len(formula_data.formulas),
        tree_name=formula_data.name,
        user_id=str(current_user.id),
        action="create_driver_tree_from_formulas",
    )

    tree = await driver_tree_service.create_tree_from_formulas(
        formulas=formula_data.formulas,
        tree_name=formula_data.name,
    )

    logger.info(
        "ツリーを作成しました",
        tree_id=str(tree.id),
        tree_name=tree.name,
    )

    return await driver_tree_service.get_tree_response(tree.id)


@router.get("/trees/{tree_id}", response_model=TreeResponse)
@handle_service_errors
async def get_tree(
    tree_id: uuid.UUID,
    current_user: CurrentUserAzureDep,
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> TreeResponse:
    """ツリーを取得します。

    Args:
        tree_id: ツリーID
        current_user: 現在のユーザー
        driver_tree_service: Driver Treeサービス

    Returns:
        TreeResponse: ツリー
    """
    logger.info(
        "ツリー取得リクエスト",
        tree_id=str(tree_id),
        user_id=str(current_user.id),
        action="get_driver_tree",
    )

    response = await driver_tree_service.get_tree_response(tree_id)

    logger.info(
        "ツリーを取得しました",
        tree_id=str(tree_id),
        tree_name=response.name,
    )

    return response


@router.get("/categories")
@handle_service_errors
async def get_categories(
    current_user: CurrentUserAzureDep,
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> dict[str, dict[str, list[str]]]:
    """カテゴリー一覧を取得します。

    Args:
        current_user: 現在のユーザー
        driver_tree_service: Driver Treeサービス

    Returns:
        dict: カテゴリーの辞書
    """
    logger.info(
        "カテゴリー一覧取得リクエスト",
        user_id=str(current_user.id),
        action="get_driver_tree_categories",
    )

    categories = await driver_tree_service.get_categories()

    logger.info(
        "カテゴリー一覧を取得しました",
        category_count=len(categories),
    )

    return categories


@router.get("/kpis", response_model=KPIListResponse)
@handle_service_errors
async def get_kpis(
    current_user: CurrentUserAzureDep,
) -> KPIListResponse:
    """KPI一覧を取得します。

    Args:
        current_user: 現在のユーザー

    Returns:
        KPIListResponse: KPI一覧
    """
    logger.info(
        "KPI一覧取得リクエスト",
        user_id=str(current_user.id),
        action="get_driver_tree_kpis",
    )

    kpis = ["売上", "原価", "販管費", "粗利", "営業利益", "EBITDA"]

    logger.info(
        "KPI一覧を取得しました",
        kpi_count=len(kpis),
    )

    return KPIListResponse(kpis=kpis)


@router.get("/formulas", response_model=FormulaResponse)
@handle_service_errors
async def get_formulas(
    current_user: CurrentUserAzureDep,
    tree_type: str = Query(..., description="ツリータイプ"),
    kpi: str = Query(..., description="KPI名"),
    driver_tree_service: DriverTreeService = Depends(get_driver_tree_service),
) -> FormulaResponse:
    """指定されたツリータイプとKPIの数式を取得します。

    Args:
        current_user: 現在のユーザー
        tree_type: ツリータイプ
        kpi: KPI名
        driver_tree_service: Driver Treeサービス

    Returns:
        FormulaResponse: 数式レスポンス
    """
    logger.info(
        "数式取得リクエスト",
        tree_type=tree_type,
        kpi=kpi,
        user_id=str(current_user.id),
        action="get_driver_tree_formulas",
    )

    formulas = await driver_tree_service.get_formulas(tree_type, kpi)

    logger.info(
        "数式を取得しました",
        tree_type=tree_type,
        kpi=kpi,
        formula_count=len(formulas),
    )

    return FormulaResponse(formulas=formulas)
