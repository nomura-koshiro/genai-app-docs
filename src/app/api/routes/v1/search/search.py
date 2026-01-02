"""グローバル検索APIエンドポイント。

共通UI設計書（UI-004〜UI-005）に基づくグローバル検索のRESTful APIエンドポイントを定義します。

主な機能:
    - グローバル検索（GET /api/v1/search - プロジェクト・セッション・ファイル・ツリー横断検索）
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.core import CurrentUserAccountDep, GlobalSearchServiceDep
from app.core.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.search import SearchQuery, SearchResponse, SearchTypeEnum

logger = get_logger(__name__)

search_router = APIRouter()


@search_router.get(
    "/search",
    response_model=SearchResponse,
    summary="グローバル検索",
    description="""
    プロジェクト・セッション・ファイル・ツリーを横断検索します。

    **認証が必要です。**

    クエリパラメータ:
        - q: str - 検索クエリ（2文字以上、必須）
        - type: str - 検索対象タイプ（project/session/file/tree）、カンマ区切りで複数指定可
        - project_id: UUID - プロジェクトIDで絞り込み
        - limit: int - 取得件数（デフォルト: 20、最大: 100）

    レスポンス:
        - SearchResponse: 検索結果
            - results: list[SearchResultInfo] - 検索結果リスト
            - total: int - 総件数
            - query: str - 検索クエリ
            - types: list[str] - 検索対象タイプ

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 422: バリデーションエラー
    """,
)
@handle_service_errors
async def search(
    current_user: CurrentUserAccountDep,
    search_service: GlobalSearchServiceDep,
    q: str = Query(..., min_length=2, max_length=100, description="検索クエリ"),
    type: str | None = Query(
        None,
        description="検索対象タイプ（project/session/file/tree）、カンマ区切りで複数指定可",
    ),
    project_id: UUID | None = Query(None, description="プロジェクトIDで絞り込み"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
) -> SearchResponse:
    """グローバル検索を実行します。"""
    logger.info(
        "グローバル検索",
        user_id=str(current_user.id),
        query=q,
        type=type,
        project_id=str(project_id) if project_id else None,
        limit=limit,
        action="search",
    )

    # 検索タイプをパース
    search_types: list[SearchTypeEnum] | None = None
    if type:
        type_list = [t.strip().lower() for t in type.split(",")]
        search_types = []
        for t in type_list:
            try:
                search_types.append(SearchTypeEnum(t))
            except ValueError:
                pass  # 無効なタイプは無視

    # 検索クエリを構築
    query = SearchQuery(
        q=q,
        type=search_types,
        project_id=project_id,
        limit=limit,
    )

    # 検索を実行
    result = await search_service.search(query, current_user.id)

    logger.info(
        "グローバル検索完了",
        user_id=str(current_user.id),
        query=q,
        result_count=result.total,
    )

    return result
