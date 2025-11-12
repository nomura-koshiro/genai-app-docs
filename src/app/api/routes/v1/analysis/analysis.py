"""Azure AD認証用データ分析APIエンドポイント。

このモジュールは、Azure AD認証に対応したデータ分析のRESTful APIエンドポイントを定義します。
分析セッションの作成・管理、ファイルアップロード、AIエージェントとのチャット、
分析結果の取得などの操作を提供します。

主な機能:
    - 分析セッション作成（POST /api/v1/analysis/sessions - 認証必須）
    - セッション一覧取得（GET /api/v1/analysis/sessions - プロジェクト別）
    - セッション詳細取得（GET /api/v1/analysis/sessions/{session_id}）
    - データファイルアップロード（POST /api/v1/analysis/sessions/{session_id}/files）
    - AIチャット実行（POST /api/v1/analysis/sessions/{session_id}/chat）
    - 分析結果取得（GET /api/v1/analysis/sessions/{session_id}/result）
    - 検証設定取得（GET /api/v1/analysis/validation-config）
    - ダミーデータ取得（GET /api/v1/analysis/dummy/{chart_type}）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - プロジェクトメンバー権限チェック

使用例:
    >>> # セッション作成
    >>> POST /api/v1/analysis/sessions
    >>> Authorization: Bearer <Azure_AD_Token>
    >>> {
    ...     "project_id": "12345678-1234-1234-1234-123456789abc",
    ...     "policy": "市場拡大",
    ...     "issue": "新規参入"
    ... }
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

# 認証のインポート（依存性ファイルから）
from app.api.core.dependencies import CurrentUserAzureDep
from app.api.decorators import async_timeout, handle_service_errors
from app.core.database import get_db
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.schemas.analysis.session import (
    AnalysisFileUploadRequest,
    AnalysisFileUploadResponse,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisStepCreate,
    AnalysisStepResponse,
    ChatRequest,
    ChatResponse,
    DummyDataResponse,
    ValidationConfigResponse,
)
from app.services.analysis import AnalysisService
from app.services.project.project import ProjectService

logger = get_logger(__name__)

router = APIRouter()


# ================================================================================
# 依存性注入ヘルパー
# ================================================================================


def get_analysis_service(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    """分析サービスインスタンスを生成します。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        AnalysisService: 初期化された分析サービス
    """
    return AnalysisService(db)


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    """プロジェクトサービスインスタンスを生成します。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        ProjectService: 初期化されたプロジェクトサービス
    """
    return ProjectService(db)


# ================================================================================
# POST Endpoints
# ================================================================================


@router.post(
    "/sessions",
    response_model=AnalysisSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析セッション作成",
    description="""
    新しい分析セッションを作成します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    - セッション作成時に初期スナップショット（snapshot_id=0）が作成されます
    - validation_config（施策・課題）が設定されます
    - 空のチャット履歴が初期化されます

    リクエストボディ:
        - project_id: プロジェクトID（必須）
        - policy: 施策名（必須）
        - issue: 課題名（必須）
    """,
)
@handle_service_errors
@async_timeout(300.0)  # 5分タイムアウト（分析処理）
async def create_session(
    session_data: AnalysisSessionCreate,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    project_service: ProjectService = Depends(get_project_service),
) -> AnalysisSessionDetailResponse:
    """新しい分析セッションを作成します。

    Args:
        session_data: セッション作成リクエスト
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）
        project_service: プロジェクトサービス（自動注入）

    Returns:
        AnalysisSessionDetailResponse: 作成されたセッション情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: プロジェクトが存在しない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/analysis/sessions
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "project_id": "12345678-1234-1234-1234-123456789abc",
        ...     "policy": "市場拡大",
        ...     "issue": "新規参入"
        ... }
        >>>
        >>> # レスポンス (201 Created)
        >>> {
        ...     "session_id": "87654321-4321-4321-4321-123456789abc",
        ...     "project_id": "12345678-1234-1234-1234-123456789abc",
        ...     "validation_config": {"policy": "市場拡大", "issue": "新規参入"},
        ...     "steps": [],
        ...     "files": [],
        ...     "chat_history": [],
        ...     "snapshot_history": [
        ...         {
        ...             "snapshot_id": 0,
        ...             "timestamp": "2024-01-15T10:30:00Z",
        ...             "description": "初期状態",
        ...             "steps": [],
        ...             "files": []
        ...         }
        ...     ],
        ...     "is_active": true,
        ...     "created_at": "2024-01-15T10:30:00Z",
        ...     "updated_at": "2024-01-15T10:30:00Z"
        ... }

    Note:
        - プロジェクトメンバーのみがセッションを作成できます
        - 作成時に初期スナップショット（snapshot_id=0）が自動作成されます
    """
    logger.info(
        "分析セッション作成リクエスト",
        project_id=str(session_data.project_id),
        user_id=str(current_user.id),
        policy=session_data.policy,
        issue=session_data.issue,
        action="create_analysis_session",
    )

    # プロジェクトメンバーシップチェック
    has_access = await project_service.check_user_access(
        project_id=session_data.project_id,
        user_id=current_user.id,
    )
    if not has_access:
        logger.warning(
            "プロジェクトアクセス権限なし",
            project_id=str(session_data.project_id),
            user_id=str(current_user.id),
        )
        raise AuthorizationError(
            "このプロジェクトへのアクセス権限がありません",
            details={"project_id": str(session_data.project_id)},
        )

    # セッション作成
    session = await analysis_service.create_session(
        session_data=session_data,
        creator_id=current_user.id,
    )

    logger.info(
        "分析セッションを作成しました",
        session_id=str(session.id),
        project_id=str(session.project_id),
        user_id=str(current_user.id),
    )

    # レスポンス作成
    return await analysis_service.get_session_result(session.id)


@router.post(
    "/sessions/{session_id}/files",
    response_model=AnalysisFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="データファイルアップロード",
    description="""
    分析セッションにデータファイルをアップロードします。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - 対応フォーマット: CSV, XLSX, XLS
    - ファイルはBase64エンコードして送信してください
    - ストレージにはCSV形式（UTF-8）で保存されます
    - 軸候補が自動抽出されます
    - タイムアウト: 5分

    リクエストボディ:
        - file_name: ファイル名（必須）
        - file_data: Base64エンコードされたファイルデータ（必須）
        - table_name: テーブル名（必須）
    """,
)
@handle_service_errors
@async_timeout(300.0)  # 5分タイムアウト（ファイルアップロード・処理）
async def upload_file(
    session_id: uuid.UUID,
    file_request: AnalysisFileUploadRequest,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisFileUploadResponse:
    """データファイルをアップロードします。

    Args:
        session_id: セッションID
        file_request: ファイルアップロードリクエスト
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        AnalysisFileUploadResponse: アップロード結果

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: セッションが存在しない
            - 400: ファイル形式が未対応、データ構造が不正
            - 500: 内部エラー

    Note:
        - タイムアウトは5分です
        - 大きなファイルはタイムアウトする可能性があります
    """
    logger.info(
        "ファイルアップロードリクエスト",
        session_id=str(session_id),
        file_name=file_request.file_name,
        user_id=str(current_user.id),
        action="upload_analysis_file",
    )

    # セッション存在確認とアクセス権限チェック
    session = await analysis_service.get_session(session_id)
    if not session:
        raise NotFoundError(
            "セッションが見つかりません",
            details={"session_id": str(session_id)},
        )

    # TODO: プロジェクトメンバーシップチェック（後で追加）

    # ファイルアップロード
    result = await analysis_service.upload_data_file(
        session_id=session_id,
        file_request=file_request,
        user_id=current_user.id,
    )

    logger.info(
        "ファイルをアップロードしました",
        session_id=str(session_id),
        file_id=str(result.id),
        file_name=result.file_name,
    )

    return result


@router.post(
    "/sessions/{session_id}/steps",
    response_model=AnalysisStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析ステップ作成",
    description="""
    新しい分析ステップを作成します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - ステップタイプ: filter/aggregate/transform/summary
    - step_orderは自動採番されます（0から開始）
    - data_sourceにはoriginalまたは別のステップID（step_0など）を指定

    リクエストボディ:
        - step_name: ステップ名（必須）
        - step_type: ステップタイプ（必須）
        - data_source: データソース（必須）
        - config: ステップ設定（JSONB）
    """,
)
@handle_service_errors
@async_timeout(30.0)
async def create_step(
    session_id: uuid.UUID,
    step_data: AnalysisStepCreate,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisStepResponse:
    """新しい分析ステップを作成します。

    Args:
        session_id: セッションID
        step_data: ステップ作成リクエスト
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        AnalysisStepResponse: 作成されたステップ情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: セッションが存在しない
            - 400: ステップ設定が不正
            - 500: 内部エラー
    """
    logger.info(
        "ステップ作成リクエスト",
        session_id=str(session_id),
        step_name=step_data.step_name,
        step_type=step_data.step_type,
        user_id=str(current_user.id),
        action="create_analysis_step",
    )

    # セッション存在確認
    session = await analysis_service.get_session(session_id)
    if not session:
        raise NotFoundError(
            "セッションが見つかりません",
            details={"session_id": str(session_id)},
        )

    # ステップ作成
    step = await analysis_service.create_step(
        session_id=session_id,
        step_data=step_data,
    )

    logger.info(
        "ステップを作成しました",
        session_id=str(session_id),
        step_id=str(step.id),
        step_name=step.step_name,
        step_order=step.step_order,
    )

    return AnalysisStepResponse.model_validate(step)


@router.post(
    "/sessions/{session_id}/chat",
    response_model=ChatResponse,
    summary="AIチャット実行",
    description="""
    AIエージェントとチャットを実行します（準備中）。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - Phase 3.1で完全実装予定
    - 現在はプレースホルダー実装です
    - タイムアウト: 10分

    リクエストボディ:
        - message: ユーザーメッセージ（必須）
    """,
)
@handle_service_errors
@async_timeout(300.0)  # 5分タイムアウト（AIエージェント実行）
async def execute_chat(
    session_id: uuid.UUID,
    chat_request: ChatRequest,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> ChatResponse:
    """AIエージェントとチャットを実行します。

    Args:
        session_id: セッションID
        chat_request: チャットリクエスト
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        ChatResponse: チャットレスポンス

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: セッションが存在しない
            - 500: 内部エラー

    Note:
        - Phase 3.1でAIエージェント統合予定
        - タイムアウトは10分です
    """
    logger.info(
        "チャット実行リクエスト",
        session_id=str(session_id),
        message_length=len(chat_request.message),
        user_id=str(current_user.id),
        action="execute_analysis_chat",
    )

    # セッション存在確認
    session = await analysis_service.get_session(session_id)
    if not session:
        raise NotFoundError(
            "セッションが見つかりません",
            details={"session_id": str(session_id)},
        )

    # チャット実行
    response = await analysis_service.execute_chat(
        session_id=session_id,
        chat_request=chat_request,
    )

    logger.info(
        "チャットを実行しました",
        session_id=str(session_id),
        snapshot_id=response.snapshot_id,
    )

    return response


# ================================================================================
# GET Endpoints
# ================================================================================


@router.get(
    "/sessions",
    response_model=list[AnalysisSessionDetailResponse],
    summary="分析セッション一覧取得",
    description="""
    プロジェクトに属する分析セッションの一覧を取得します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    - project_idパラメータでプロジェクトを指定（必須）
    - created_at降順でソートされます（最新が先頭）

    クエリパラメータ:
        - project_id: プロジェクトID（必須）
        - skip: スキップするレコード数（デフォルト: 0）
        - limit: 取得する最大レコード数（デフォルト: 100、最大: 1000）
        - is_active: アクティブフラグフィルタ（オプション）
    """,
)
@handle_service_errors
@async_timeout(60.0)
async def list_sessions(
    current_user: CurrentUserAzureDep,
    project_id: uuid.UUID = Query(..., description="プロジェクトID"),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    project_service: ProjectService = Depends(get_project_service),
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
    is_active: bool | None = Query(None, description="アクティブフラグフィルタ"),
) -> list[AnalysisSessionDetailResponse]:
    """プロジェクトの分析セッション一覧を取得します。

    Args:
        project_id: プロジェクトID
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）
        project_service: プロジェクトサービス（自動注入）
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        is_active: アクティブフラグフィルタ

    Returns:
        list[AnalysisSessionDetailResponse]: セッション一覧

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: プロジェクトが存在しない
            - 500: 内部エラー
    """
    logger.info(
        "セッション一覧取得リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        action="list_analysis_sessions",
    )

    # プロジェクトメンバーシップチェック
    has_access = await project_service.check_user_access(
        project_id=project_id,
        user_id=current_user.id,
    )
    if not has_access:
        logger.warning(
            "プロジェクトアクセス権限なし",
            project_id=str(project_id),
            user_id=str(current_user.id),
        )
        raise AuthorizationError(
            "このプロジェクトへのアクセス権限がありません",
            details={"project_id": str(project_id)},
        )

    # セッション一覧取得
    sessions = await analysis_service.list_project_sessions(
        project_id=project_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    logger.info(
        "セッション一覧を取得しました",
        project_id=str(project_id),
        count=len(sessions),
    )

    # 各セッションの詳細情報を取得
    return [await analysis_service.get_session_result(session.id) for session in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=AnalysisSessionDetailResponse,
    summary="セッション詳細取得",
    description="""
    指定されたIDの分析セッション情報を取得します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - ステップ、ファイル、チャット履歴を含む完全な情報を返します
    - N+1クエリを回避するため、selectinloadを使用します
    """,
)
@handle_service_errors
async def get_session(
    session_id: uuid.UUID,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisSessionDetailResponse:
    """セッション詳細を取得します。

    Args:
        session_id: セッションID
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        AnalysisSessionDetailResponse: セッション詳細情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: セッションが存在しない
            - 500: 内部エラー
    """
    logger.info(
        "セッション詳細取得リクエスト",
        session_id=str(session_id),
        user_id=str(current_user.id),
        action="get_analysis_session",
    )

    # TODO: プロジェクトメンバーシップチェック

    # セッション詳細取得
    result = await analysis_service.get_session_result(session_id)

    logger.info(
        "セッション詳細を取得しました",
        session_id=str(session_id),
        steps_count=len(result.steps),
        files_count=len(result.files),
    )

    return result


@router.get(
    "/sessions/{session_id}/result",
    response_model=AnalysisSessionDetailResponse,
    summary="分析結果取得",
    description="""
    分析セッションの結果を取得します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - get_sessionと同じレスポンスを返します
    - エイリアスエンドポイントです
    """,
)
@handle_service_errors
async def get_session_result(
    session_id: uuid.UUID,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisSessionDetailResponse:
    """分析結果を取得します（エイリアス）。

    Args:
        session_id: セッションID
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        AnalysisSessionDetailResponse: 分析結果

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: セッションが存在しない
            - 500: 内部エラー
    """
    return await get_session(session_id, current_user, analysis_service)


@router.get(
    "/validation-config",
    response_model=ValidationConfigResponse,
    summary="検証設定取得",
    description="""
    分析の検証設定（施策・課題）を取得します。

    **認証が必要です。**

    - validation.ymlファイルから読み込まれます
    - policiesとissuesのリストを返します
    """,
)
@handle_service_errors
async def get_validation_config(
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> ValidationConfigResponse:
    """検証設定を取得します。

    Args:
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        ValidationConfigResponse: 検証設定

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 500: 内部エラー
    """
    logger.debug(
        "検証設定取得リクエスト",
        user_id=str(current_user.id),
        action="get_validation_config",
    )

    config = await analysis_service.get_validation_config()

    logger.debug(
        "検証設定を取得しました",
        policies_count=len(config.validation_config.get("policies", [])),
        issues_count=len(config.validation_config.get("issues", [])),
    )

    return config


@router.get(
    "/dummy/{chart_type}",
    response_model=DummyDataResponse,
    summary="ダミーチャートデータ取得",
    description="""
    指定されたチャートタイプのダミーデータを取得します。

    **認証が必要です。**

    - Plotly形式のJSONデータを返します
    - app/data/analysis/dummy/chart/配下から読み込まれます

    パスパラメータ:
        - chart_type: チャートタイプ（例: bar, line, pie, scatter）
    """,
)
@handle_service_errors
async def get_dummy_data(
    chart_type: str,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> DummyDataResponse:
    """ダミーチャートデータを取得します。

    Args:
        chart_type: チャートタイプ
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Returns:
        DummyDataResponse: ダミーデータ

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: 指定されたチャートタイプが存在しない
            - 500: 内部エラー
    """
    logger.debug(
        "ダミーデータ取得リクエスト",
        chart_type=chart_type,
        user_id=str(current_user.id),
        action="get_dummy_data",
    )

    dummy_data = await analysis_service.get_dummy_data(chart_type)

    logger.debug(
        "ダミーデータを取得しました",
        chart_type=chart_type,
    )

    return dummy_data


# ================================================================================
# DELETE Endpoints
# ================================================================================


@router.delete(
    "/sessions/{session_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="分析ステップ削除",
    description="""
    指定されたステップを削除します。

    **認証が必要です。**
    **セッションが属するプロジェクトのメンバーのみアクセス可能です。**

    - 物理削除されます（論理削除ではありません）
    - 関連する結果データは削除されません
    """,
)
@handle_service_errors
async def delete_step(
    session_id: uuid.UUID,
    step_id: uuid.UUID,
    current_user: CurrentUserAzureDep,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> None:
    """分析ステップを削除します。

    Args:
        session_id: セッションID
        step_id: ステップID
        current_user: 認証済みユーザー（自動注入）
        analysis_service: 分析サービス（自動注入）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: セッションまたはステップが存在しない
            - 500: 内部エラー

    Note:
        - 物理削除されます
        - レスポンスは204 No Contentです
    """
    logger.info(
        "ステップ削除リクエスト",
        session_id=str(session_id),
        step_id=str(step_id),
        user_id=str(current_user.id),
        action="delete_analysis_step",
    )

    # セッション存在確認
    session = await analysis_service.get_session(session_id)
    if not session:
        raise NotFoundError(
            "セッションが見つかりません",
            details={"session_id": str(session_id)},
        )

    # ステップ削除
    await analysis_service.delete_step(step_id)

    logger.info(
        "ステップを削除しました",
        session_id=str(session_id),
        step_id=str(step_id),
    )
