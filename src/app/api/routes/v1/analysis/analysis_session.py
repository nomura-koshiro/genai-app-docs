"""分析セッションAPIエンドポイント。

このモジュールは、分析セッションの管理に関するAPIエンドポイントを定義します。

主な機能:
    - 分析セッション一覧取得(GET /api/v1/project/{project_id}/analysis/session)
    - 分析セッション作成(POST /api/v1/project/{project_id}/analysis/session)
    - 分析セッション詳細取得(GET /api/v1/project/{project_id}/analysis/session/{session_id})
    - 分析セッション結果取得(GET /api/v1/project/{project_id}/analysis/session/{session_id}/result)
    - 分析セッション更新 (入力ファイル選択／スナップショット復元)(PUT /api/v1/project/{project_id}/analysis/session/{session_id})
    - 分析セッション削除(DELETE /api/v1/project/{project_id}/analysis/session/{session_id})
    - ファイル管理(GET/POST /api/v1/project/{project_id}/analysis/session/{session_id}/file)
    - ファイル設定更新(PATCH /api/v1/project/{project_id}/analysis/session/{session_id}/file/{file_id})
    - AIチャット実行(POST /api/v1/project/{project_id}/analysis/session/{session_id}/chat)
    - 分析ステップ作成(POST /api/v1/project/{project_id}/analysis/session/{session_id}/step)
    - 分析ステップ更新削除(PUT/DELETE /api/v1/project/{project_id}/analysis/session/{session_id}/step/{step_id})
"""

import uuid

from fastapi import APIRouter, Body, Path, Query, status

from app.api.core import AnalysisSessionServiceDep, ProjectMemberDep
from app.api.decorators import async_timeout, handle_service_errors
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisChatCreate,
    AnalysisChatListResponse,
    AnalysisFileConfigResponse,
    AnalysisFileCreate,
    AnalysisFileListResponse,
    AnalysisFileResponse,
    AnalysisFileUpdate,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisSessionListResponse,
    AnalysisSessionResultListResponse,
    AnalysisSessionUpdate,
    AnalysisSnapshotCreate,
    AnalysisSnapshotListResponse,
    AnalysisSnapshotResponse,
    AnalysisStepCreate,
    AnalysisStepResponse,
    AnalysisStepUpdate,
)

logger = get_logger(__name__)

analysis_sessions_router = APIRouter()


# ================================================================================
# セッション CRUD
# ================================================================================


@analysis_sessions_router.get(
    "/project/{project_id}/analysis/session",
    response_model=AnalysisSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション一覧取得",
    description="""
    プロジェクトに属する分析セッションの一覧を取得します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    - created_at降順でソートされます(最新が先頭)

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    クエリパラメータ:
        - skip: int - スキップ数（デフォルト: 0）
        - limit: int - 取得件数（デフォルト: 100）
        - is_active: bool - アクティブフィルタ（オプション）

    レスポンス:
        - AnalysisSessionListResponse: 分析セッション一覧レスポンス
            - sessions (list[AnalysisSessionResponse]): セッションリスト
                - id (uuid): セッションID
                - project_id (uuid): プロジェクトID
                - issue_id (uuid): 課題ID
                - creator_id (uuid): 作成者ID
                - current_snapshot (int): 現在のスナップショット番号
                - created_at (datetime): 作成日時
                - updated_at (datetime): 更新日時
            - total (int): 総件数
            - skip (int): スキップ数
            - limit (int): 取得件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_sessions(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
    is_active: bool | None = Query(None, description="アクティブフラグフィルタ"),
) -> AnalysisSessionListResponse:
    """分析セッション一覧を取得します。"""
    logger.info(
        "分析セッション一覧取得リクエスト",
        user_id=str(member.user_id),
        project_id=str(project_id),
        skip=skip,
        limit=limit,
        action="list_sessions",
    )

    sessions = await session_service.list_sessions(
        project_id=project_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    logger.info(
        "分析セッション一覧を取得しました",
        user_id=str(member.user_id),
        project_id=str(project_id),
        count=len(sessions),
    )

    return AnalysisSessionListResponse(
        sessions=sessions,
        total=len(sessions),
        skip=skip,
        limit=limit,
    )


@analysis_sessions_router.post(
    "/project/{project_id}/analysis/session",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析セッション作成",
    description="""
    新しい分析セッションを作成します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    - セッション作成時に初期スナップショット(snapshot_id=0)が作成されます
    - 施策課題テンプレが設定されます
    - 空のチャット履歴が初期化されます

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - issue_id (uuid): 課題ID（必須）

    レスポンス:
        - AnalysisSessionDetailResponse: 分析セッション詳細情報
            - id (uuid): セッションID
            - project_id (uuid): プロジェクトID
            - issue_id (uuid): 課題ID
            - creator_id (uuid): 作成者ID
            - current_snapshot (int): 現在のスナップショット番号
            - input_file_id (uuid | None): 入力ファイルID
            - snapshot_list (list[AnalysisSnapshotResponse]): スナップショット一覧
            - file_list (list[AnalysisFileResponse]): 分析ファイル一覧
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: プロジェクトまたは課題が見つからない
    """,
)
@handle_service_errors
async def create_session(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_create: AnalysisSessionCreate = Body(..., description="分析セッション作成リクエスト"),
) -> AnalysisSessionDetailResponse:
    """分析セッションを作成します。

    Args:
        project_id (uuid.UUID): プロジェクトID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisSessionDetailResponse: 作成された分析セッション詳細
    """

    logger.info(
        "分析セッション作成リクエスト",
        user_id=str(member.user_id),
        project_id=str(project_id),
        action="create_session",
    )

    session = await session_service.create_session(project_id, member.user_id, session_create)

    logger.info(
        "分析セッションを作成しました",
        user_id=str(member.user_id),
        session_id=str(session.id),
        project_id=str(project_id),
    )

    return session


@analysis_sessions_router.get(
    "/project/{project_id}/analysis/session/{session_id}",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション詳細取得",
    description="""
    指定されたIDの分析セッション情報を取得します。
    ステップ、ファイル、チャット履歴を含む完全な情報を返します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    レスポンス:
        - AnalysisSessionDetailResponse: 分析セッション詳細情報
            - id (uuid): セッションID
            - project_id (uuid): プロジェクトID
            - issue_id (uuid): 課題ID
            - creator_id (uuid): 作成者ID
            - current_snapshot (int): 現在のスナップショット番号
            - input_file_id (uuid | None): 入力ファイルID
            - snapshot_list (list[AnalysisSnapshotResponse]): スナップショット一覧
            - file_list (list[AnalysisFileResponse]): 分析ファイル一覧
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def get_session(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
) -> AnalysisSessionDetailResponse:
    """分析セッション詳細を取得します。

    Args:
        session_id (uuid.UUID): セッションID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisSessionDetailResponse: 分析セッション詳細
    """
    logger.info(
        "分析セッション詳細取得リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="get_session",
    )

    session = await session_service.get_session(project_id, session_id)

    logger.info(
        "分析セッション詳細を取得しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
    )

    return session


@analysis_sessions_router.get(
    "/project/{project_id}/analysis/session/{session_id}/result",
    response_model=AnalysisSessionResultListResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション結果取得",
    description="""
    分析セッションの結果を取得します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - session_id (uuid): セッションID

    レスポンス:
        - AnalysisSessionResultListResponse:
            - results (list[AnalysisSessionResultResponse]): 結果リスト
                - step_id (uuid): ステップID
                - step_name (str): ステップ名
                - result_formula (list[dict[str, Any]] | None): 結果の数式リスト
                - result_chart (dict[str, Any] | None): 結果のチャート (plotly の JSON)
                - result_table (list[dict[str, Any]] | None): 結果のテーブル (pandasのto_dict(orient='records')形式)
            - total (int): 総件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def get_session_result(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
) -> AnalysisSessionResultListResponse:
    """分析結果を取得します。

    Args:
        session_id (uuid.UUID): セッションID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisSessionResultListResponse: 分析結果一覧
    """
    logger.info(
        "分析結果取得リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="get_session_result",
    )

    result = await session_service.get_session_result(project_id, session_id)

    logger.info(
        "分析結果を取得しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
    )

    return result


@analysis_sessions_router.put(
    "/project/{project_id}/analysis/session/{session_id}",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="分析セッション更新 (入力ファイル選択／スナップショット復元)",
    description="""
    指定されたIDの分析セッションに対して、入力ファイルの選択またはスナップショットの復元を行います。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - session_id (uuid): セッションID

    クエリパラメータ:
        - AnalysisSessionUpdate:
            - current_snapshot (int): 復元するスナップショット番号 (オプション)
            - input_file_id (uuid): 選択する入力ファイルID (オプション)

    レスポンス:
        - AnalysisSessionDetailResponse:
            - id (uuid): セッションID
            - project_id (uuid): プロジェクトID
            - issue_id (uuid): 課題ID
            - creator_id (uuid): 作成者ID
            - current_snapshot (int): 現在のスナップショット番号
            - input_file_id (uuid | None): 入力ファイルID
            - snapshot_list (list[AnalysisSnapshotResponse]): スナップショット一覧
            - file_list (list[AnalysisFileResponse]): 分析ファイル一覧
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションまたはファイルが見つからない
    """,
)
@handle_service_errors
async def update_session(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    session_update: AnalysisSessionUpdate = Body(..., description="分析セッション更新リクエスト"),
) -> AnalysisSessionDetailResponse:
    """入力ファイルを選択します。

    Args:
        session_id (uuid.UUID): セッションID
        file_id (uuid.UUID): ファイルID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisSessionDetailResponse: 更新されたセッション詳細
    """

    file_id = session_update.input_file_id
    snapshot_order = session_update.current_snapshot

    if file_id is not None:
        logger.info(
            "分析セッション入力ファイル選択リクエスト",
            user_id=str(member.user_id),
            session_id=str(session_id),
            file_id=str(file_id),
            snapshot_order=str(snapshot_order),
            action="select_input_file",
        )
        result = await session_service.select_input_file(session_id, session_update.input_file_id)

    if snapshot_order is not None:
        logger.info(
            "分析セッションスナップショット復元リクエスト",
            user_id=str(member.user_id),
            session_id=str(session_id),
            snapshot_order=str(snapshot_order),
            action="restore_snapshot",
        )
        result = await session_service.restore_snapshot(session_id, snapshot_order)

    logger.info(
        "分析セッションを更新しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        file_id=str(file_id),
        snapshot_order=str(snapshot_order),
    )

    return result


@analysis_sessions_router.delete(
    "/project/{project_id}/analysis/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="分析セッション削除",
    description="""
    指定されたIDの分析セッションを削除します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    レスポンス:
        - なし（204 No Content）

    ステータスコード:
        - 204: 成功（削除完了）
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def delete_session(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
) -> None:
    """分析セッションを削除します。

    Args:
        session_id (uuid.UUID): セッションID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
    """
    logger.info(
        "分析セッション削除リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="delete_session",
    )

    await session_service.delete_session(project_id, session_id)

    logger.info(
        "分析セッションを削除しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
    )


@analysis_sessions_router.post(
    "/project/{project_id}/analysis/session/{session_id}/duplicate",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析セッション複製",
    description="""
    指定されたIDの分析セッションを複製します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    セッションとその関連データ（スナップショット、ステップ、チャット、ファイル）を
    深いコピーで複製します。

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - 複製元セッションID（必須）

    レスポンス:
        - AnalysisSessionDetailResponse: 複製されたセッション詳細

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def duplicate_session(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="複製元セッションID"),
) -> AnalysisSessionDetailResponse:
    """分析セッションを複製します。

    Args:
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        project_id (uuid.UUID): プロジェクトID
        session_id (uuid.UUID): 複製元セッションID

    Returns:
        AnalysisSessionDetailResponse: 複製されたセッション詳細
    """
    logger.info(
        "分析セッション複製リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="duplicate_session",
    )

    duplicated = await session_service.duplicate_session(project_id, session_id, member.user_id)

    logger.info(
        "分析セッションを複製しました",
        user_id=str(member.user_id),
        original_session_id=str(session_id),
        new_session_id=str(duplicated.id),
    )

    return duplicated


# ================================================================================
# ファイル管理
# ================================================================================


@analysis_sessions_router.get(
    "/project/{project_id}/analysis/session/{session_id}/file",
    response_model=AnalysisFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="登録済ファイル一覧取得",
    description="""
    指定されたIDの分析セッションに登録されたファイルを取得します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    レスポンス:
        - AnalysisFileListResponse: 分析ファイル一覧レスポンス
            - files (list[AnalysisFileResponse]): ファイルリスト
                - id (uuid): ファイルID
                - session_id (uuid): セッションID
                - project_file_id (uuid): プロジェクトファイルID
                - project_file_name (str): プロジェクトファイル名
                - sheet_name (str): シート名
                - axis_config (dict[str, Any]): 軸設定JSON
                - data (list[dict[str, Any]]): データJSON（pandas DataFrameのrecord形式）
                - created_at (datetime): 作成日時
                - updated_at (datetime): 更新日時
            - total (int): 総件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def list_session_files(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
) -> AnalysisFileListResponse:
    """セッションに登録されたファイル一覧を取得します。

    Args:
        session_id (uuid.UUID): セッションID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisFileListResponse: ファイル一覧
    """
    logger.info(
        "登録済ファイル取得リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="list_session_files",
    )

    files = await session_service.list_session_files(project_id, session_id)

    logger.info(
        "登録済ファイルを取得しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        count=len(files),
    )

    return AnalysisFileListResponse(
        files=files,
        total=len(files),
    )


@analysis_sessions_router.post(
    "/project/{project_id}/analysis/session/{session_id}/file",
    response_model=AnalysisFileConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ファイルアップロード",
    description="""
    分析セッションにファイルを登録します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    クエリパラメータ:
        - pjt_file_id (uuid): プロジェクトファイルID (必須)

    レスポンス:
        - AnalysisFileConfigResponse: 分析ファイル設定情報
            - id (uuid): 分析ファイルID
            - config_list (list[dict[str, Any]]): 設定候補リスト（シート名、軸設定の候補）

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションまたはファイルが見つからない
    """,
)
@handle_service_errors
async def upload_session_file(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    analysis_file_create: AnalysisFileCreate = Body(..., description="ファイルアップロードリクエスト"),
) -> AnalysisFileConfigResponse:
    """セッションにファイルを登録します。

    Args:
        session_id (uuid.UUID): セッションID
        request (AnalysisFileCreate): ファイルアップロードリクエスト
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisFileConfigResponse: ファイル設定情報
    """

    pjt_file_id = analysis_file_create.project_file_id
    logger.info(
        "ファイルアップロードリクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        pjt_file_id=str(pjt_file_id),
        action="upload_session_file",
    )

    file = await session_service.upload_session_file(project_id, session_id, analysis_file_create)

    logger.info(
        "ファイルをアップロードしました",
        user_id=str(member.user_id),
        session_id=str(session_id),
    )

    return file


@analysis_sessions_router.patch(
    "/project/{project_id}/analysis/session/{session_id}/file/{file_id}",
    response_model=AnalysisFileResponse,
    status_code=status.HTTP_200_OK,
    summary="ファイル設定更新",
    description="""
    ファイルの設定(シート、軸)を登録します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）
        - file_id: uuid - ファイルID（必須）

    クエリパラメータ:
        - なし

    パスパラメータ:
        - session_id (uuid): セッションID
        - file_id (uuid): ファイルID

    リクエストボディ:
        - AnalysisFileUpdate:
            - sheet_name (str): シート名 (オプション)
            - axis_config (dict[str, Any]): 軸設定JSON (オプション)

    レスポンス:
        - AnalysisFileResponse:
            - id (uuid): ファイルID
            - session_id (uuid): セッションID
            - project_file_id (uuid): プロジェクトファイルID
            - project_file_name (str): プロジェクトファイル名
            - sheet_name (str): シート名
            - axis_config (dict[str, Any]): 軸設定JSON
            - data (list[dict[str, Any]]): データJSON（pandas DataFrameのrecord形式）
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションまたはファイルが見つからない
    """,
)
@handle_service_errors
async def update_file_config(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    file_id: uuid.UUID = Path(..., description="ファイルID"),
    analysis_file_update: AnalysisFileUpdate = Body(..., description="ファイル設定更新データ"),
) -> AnalysisFileResponse:
    """ファイルの設定を更新します。

    Args:
        session_id (uuid.UUID): セッションID
        file_id (uuid.UUID): ファイルID
        analysis_file_update (AnalysisFileUpdate): 更新データ
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス

    Returns:
        AnalysisFileResponse: 更新されたファイル情報
    """
    logger.info(
        "シート選択/データカラム設定送信リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        file_id=str(file_id),
        action="update_file_config",
    )

    result = await session_service.update_file_config(project_id, session_id, file_id, analysis_file_update)

    logger.info(
        "ファイル設定を更新しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        file_id=str(file_id),
    )

    return result


# ================================================================================
# スナップショット管理
# ================================================================================


@analysis_sessions_router.get(
    "/project/{project_id}/analysis/session/{session_id}/snapshots",
    response_model=AnalysisSnapshotListResponse,
    status_code=status.HTTP_200_OK,
    summary="スナップショット一覧取得",
    description="""
    セッションのスナップショット一覧を取得します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    レスポンス:
        - AnalysisSnapshotListResponse: スナップショット一覧
            - snapshots (list[AnalysisSnapshotResponse]): スナップショットリスト
                - id (uuid): スナップショットID
                - snapshot_order (int): スナップショット順序番号
                - parent_snapshot_id (uuid | None): 親スナップショットID
                - chat_list (list[AnalysisChatResponse]): チャットリスト
                - step_list (list[AnalysisStepResponse]): ステップリスト
                - created_at (datetime): 作成日時
                - updated_at (datetime): 更新日時
            - total (int): 総件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def list_snapshots(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
) -> AnalysisSnapshotListResponse:
    """スナップショット一覧を取得します。

    Args:
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        project_id (uuid.UUID): プロジェクトID
        session_id (uuid.UUID): セッションID

    Returns:
        AnalysisSnapshotListResponse: スナップショット一覧
    """
    logger.info(
        "スナップショット一覧取得リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="list_snapshots",
    )

    snapshots = await session_service.list_snapshots(project_id, session_id)

    logger.info(
        "スナップショット一覧を取得しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        count=len(snapshots),
    )

    return AnalysisSnapshotListResponse(
        snapshots=snapshots,
        total=len(snapshots),
    )


@analysis_sessions_router.post(
    "/project/{project_id}/analysis/session/{session_id}/snapshots",
    response_model=AnalysisSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="手動スナップショット保存",
    description="""
    現在の分析状態を手動でスナップショットとして保存します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    リクエストボディ:
        - name (str | None): スナップショット名（オプション）
        - description (str | None): スナップショット説明（オプション）

    レスポンス:
        - AnalysisSnapshotResponse: 作成されたスナップショット
            - id (uuid): スナップショットID
            - snapshot_order (int): スナップショット順序番号
            - parent_snapshot_id (uuid | None): 親スナップショットID
            - chat_list (list[AnalysisChatResponse]): チャットリスト
            - step_list (list[AnalysisStepResponse]): ステップリスト
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def create_snapshot(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    snapshot_create: AnalysisSnapshotCreate = Body(..., description="スナップショット作成リクエスト"),
) -> AnalysisSnapshotResponse:
    """手動でスナップショットを保存します。

    Args:
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        project_id (uuid.UUID): プロジェクトID
        session_id (uuid.UUID): セッションID
        snapshot_create (AnalysisSnapshotCreate): スナップショット作成データ

    Returns:
        AnalysisSnapshotResponse: 作成されたスナップショット
    """
    logger.info(
        "手動スナップショット保存リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="create_snapshot",
    )

    snapshot = await session_service.create_snapshot(project_id, session_id, snapshot_create)

    logger.info(
        "スナップショットを保存しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        snapshot_id=str(snapshot.id),
    )

    return snapshot


# ================================================================================
# チャット
# ================================================================================


@analysis_sessions_router.get(
    "/project/{project_id}/analysis/session/{session_id}/messages",
    response_model=AnalysisChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="チャットメッセージ履歴取得",
    description="""
    セッションのチャットメッセージ履歴を取得します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    現在のスナップショットに関連付けられたすべてのチャットメッセージを返します。

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    クエリパラメータ:
        - skip: int - スキップ数（デフォルト: 0）
        - limit: int - 取得件数（デフォルト: 100、最大: 500）

    レスポンス:
        - AnalysisChatListResponse: チャットメッセージ一覧
            - messages (list[AnalysisChatResponse]): メッセージリスト
                - id (uuid): メッセージID
                - chat_order (int): チャット順序
                - snapshot (int): スナップショット番号
                - role (str): ロール（user/assistant）
                - message (str | None): メッセージ内容
                - created_at (datetime): 作成日時
                - updated_at (datetime): 更新日時
            - total (int): 総件数
            - skip (int): スキップ数
            - limit (int): 取得件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def get_chat_messages(
    member: ProjectMemberDep,
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=500, description="取得する最大レコード数"),
) -> AnalysisChatListResponse:
    """チャットメッセージ履歴を取得します。

    Args:
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        project_id (uuid.UUID): プロジェクトID
        session_id (uuid.UUID): セッションID
        skip (int): スキップ数
        limit (int): 取得件数

    Returns:
        AnalysisChatListResponse: チャットメッセージ一覧
    """
    logger.info(
        "チャットメッセージ履歴取得リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        skip=skip,
        limit=limit,
        action="get_chat_messages",
    )

    messages = await session_service.get_chat_messages(project_id, session_id, skip, limit)

    logger.info(
        "チャットメッセージ履歴を取得しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        count=len(messages),
    )

    return AnalysisChatListResponse(
        messages=messages,
        total=len(messages),
        skip=skip,
        limit=limit,
    )


@analysis_sessions_router.post(
    "/project/{project_id}/analysis/session/{session_id}/chat",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="AIチャット実行",
    description="""
    AIエージェントとチャットを実行します(準備中)。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    クエリパラメータ:
        - なし

    リクエストボディ:
        - message (str): ユーザーメッセージ（必須）

    レスポンス:
        - AnalysisSessionDetailResponse: 分析セッション詳細情報
            - id (uuid): セッションID
            - project_id (uuid): プロジェクトID
            - issue_id (uuid): 課題ID
            - creator_id (uuid): 作成者ID
            - current_snapshot (int): 現在のスナップショット番号
            - input_file_id (uuid | None): 入力ファイルID
            - snapshot_list (list[AnalysisSnapshotResponse]): スナップショット一覧
            - file_list (list[AnalysisFileResponse]): 分析ファイル一覧
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
        - 504: タイムアウト（10分）
    """,
)
@handle_service_errors
@async_timeout(600.0)  # 10分タイムアウト(AIチャット処理)
async def execute_chat(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    chat_create: AnalysisChatCreate = Body(..., description="AIチャット実行リクエスト"),
) -> AnalysisSessionDetailResponse:
    """AIチャットを実行します。

    Args:
        session_id (uuid.UUID): セッションID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        chat_create (AnalysisChatCreate): チャット作成データ

    Returns:
        AnalysisSessionDetailResponse: 更新されたセッション詳細
    """
    logger.info(
        "AIチャット実行リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        action="execute_chat",
    )

    response = await session_service.execute_chat(project_id, session_id, chat_create)

    logger.info(
        "AIチャットを実行しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
    )

    return response


# ================================================================================
# 分析ステップ管理
# ================================================================================


@analysis_sessions_router.post(
    "/project/{project_id}/analysis/session/{session_id}/step",
    response_model=AnalysisStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析ステップ作成",
    description="""
    最新snapshotに新しい分析ステップを作成します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）

    リクエストボディ:
        - step_name (str): ステップ名（必須）
        - step_type (str): ステップタイプ（必須: filter/aggregate/transform/summary）
        - data_source (str): データソース（必須: originalまたはステップID）
        - config (dict): ステップ設定（オプション）

    レスポンス:
        - AnalysisStepResponse: 分析ステップ情報
            - id (uuid): ステップID
            - name (str): ステップ名
            - type (str): ステップタイプ
            - input (str): データソース
            - step_order (int): ステップ順序
            - config (dict[str, Any]): ステップ設定(JSON)
            - snapshot_id (uuid): スナップショットID
            - result_formula (list[dict[str, Any]] | None): 結果の数式リスト
            - result_chart (dict[str, Any] | None): 結果のチャート (plotly の JSON)
            - result_table (list[dict[str, Any]] | None): 結果のテーブル (pandasのto_dict(orient='records')形式)
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションが見つからない
    """,
)
@handle_service_errors
async def create_step(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    analysis_step_create: AnalysisStepCreate = Body(..., description="分析ステップ作成データ"),
) -> AnalysisStepResponse:
    """分析ステップを作成します。

    Args:
        session_id (uuid.UUID): セッションID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        analysis_step_create (AnalysisStepCreate): ステップ作成データ

    Returns:
        AnalysisStepResponse: 作成されたステップ情報
    """

    step_name = analysis_step_create.name
    step_type = analysis_step_create.type
    data_source = analysis_step_create.input

    logger.info(
        "分析ステップ作成リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        step_name=step_name,
        step_type=step_type,
        action="create_step",
    )

    result = await session_service.create_step(
        project_id=project_id,
        session_id=session_id,
        step_name=step_name,
        step_type=step_type,
        data_source=data_source,
    )

    logger.info(
        "分析ステップを作成しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        step_name=step_name,
    )

    return result


@analysis_sessions_router.put(
    "/project/{project_id}/analysis/session/{session_id}/step/{step_id}",
    response_model=AnalysisStepResponse,
    status_code=status.HTTP_200_OK,
    summary="分析ステップ更新",
    description="""
    最新snapshotの既存分析ステップを更新します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）
        - step_id: uuid - ステップID（必須）

    クエリパラメータ:
        - なし

    リクエストボディ:
    - AnalysisStepUpdate:
        - name (str): ステップ名 (オプション)
        - type (str): ステップタイプ (オプション)
        - input (str): データソース (オプション)
        - config (dict): ステップ設定 (オプション)

    レスポンス:
        - AnalysisStepResponse: 分析ステップ情報
            - id (uuid): ステップID
            - name (str): ステップ名
            - type (str): ステップタイプ
            - input (str): データソース
            - step_order (int): ステップ順序
            - config (dict[str, Any]): ステップ設定(JSON)
            - snapshot_id (uuid): スナップショットID
            - result_formula (list[dict[str, Any]] | None): 結果の数式リスト
            - result_chart (dict[str, Any] | None): 結果のチャート (plotly の JSON)
            - result_table (list[dict[str, Any]] | None): 結果のテーブル (pandasのto_dict(orient='records')形式)
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションまたはステップが見つからない
    """,
)
@handle_service_errors
async def update_step(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    step_id: uuid.UUID = Path(..., description="分析ステップID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
    analysis_step_update: AnalysisStepUpdate = Body(..., description="分析ステップ更新データ"),
) -> AnalysisStepResponse:
    """分析ステップを更新します。

    Args:
        session_id (uuid.UUID): セッションID
        step_id (uuid.UUID): ステップID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
        analysis_step_update (AnalysisStepUpdate): ステップ更新データ

    Returns:
        AnalysisStepResponse: 更新されたステップ情報
    """
    step_name = analysis_step_update.name
    step_type = analysis_step_update.type
    data_source = analysis_step_update.input
    config = analysis_step_update.config

    logger.info(
        "分析ステップ更新リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        step_id=str(step_id),
        action="update_step",
    )

    result = await session_service.update_step(
        project_id=project_id,
        session_id=session_id,
        step_id=step_id,
        step_name=step_name,
        step_type=step_type,
        data_source=data_source,
        config=config,
    )

    logger.info(
        "分析ステップを更新しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        step_id=str(step_id),
    )

    return result


@analysis_sessions_router.delete(
    "/project/{project_id}/analysis/session/{session_id}/step/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="分析ステップ削除",
    description="""
    最新snapshotの指定されたステップを削除します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - 物理削除されます(論理削除ではありません)

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - session_id: uuid - セッションID（必須）
        - step_id: uuid - ステップID（必須）

    レスポンス:
        - なし（204 No Content）

    ステータスコード:
        - 204: 成功（削除完了）
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: セッションまたはステップが見つからない
    """,
)
@handle_service_errors
async def delete_step(
    member: ProjectMemberDep,  # 権限チェック（プロジェクトメンバーであることを確認）
    session_service: AnalysisSessionServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    step_id: uuid.UUID = Path(..., description="分析ステップID"),
    session_id: uuid.UUID = Path(..., description="分析セッションID"),
) -> None:
    """分析ステップを削除します。

    Args:
        session_id (uuid.UUID): セッションID
        step_id (uuid.UUID): ステップID
        member (ProjectMemberDep): プロジェクトメンバー（権限チェック済み）
        session_service (AnalysisSessionServiceDep): 分析セッションサービス
    """
    logger.info(
        "分析ステップ削除リクエスト",
        user_id=str(member.user_id),
        session_id=str(session_id),
        step_id=str(step_id),
        action="delete_step",
    )

    await session_service.delete_step(project_id, session_id, step_id)

    logger.info(
        "分析ステップを削除しました",
        user_id=str(member.user_id),
        session_id=str(session_id),
        step_id=str(step_id),
    )
