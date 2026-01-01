"""分析関連のPydanticスキーマ。

このモジュールは、分析機能に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    テンプレート:
        分析施策:
            - AnalysisValidationBase: 施策ベース
            - AnalysisValidationCreate: 施策作成リクエスト
            - AnalysisValidationUpdate: 施策更新リクエスト
            - AnalysisValidationResponse: 施策レスポンス

        分析課題:
            - AnalysisIssueBase: 課題ベース
            - AnalysisIssueCreate: 課題作成リクエスト
            - AnalysisIssueUpdate: 課題更新リクエスト
            - AnalysisIssueCatalogResponse: 課題カタログレスポンス
            - AnalysisIssueDetailResponse: 課題詳細レスポンス

        グラフ軸設定:
            - AnalysisGraphAxisBase: 軸設定ベース
            - AnalysisGraphAxisCreate: 軸設定作成リクエスト
            - AnalysisGraphAxisUpdate: 軸設定更新リクエスト
            - AnalysisGraphAxisResponse: 軸設定レスポンス

        ダミー計算式:
            - AnalysisDummyFormulaBase: 計算式ベース
            - AnalysisDummyFormulaCreate: 計算式作成リクエスト
            - AnalysisDummyFormulaUpdate: 計算式更新リクエスト
            - AnalysisDummyFormulaResponse: 計算式レスポンス

        ダミーチャート:
            - AnalysisDummyChartBase: チャートベース
            - AnalysisDummyChartCreate: チャート作成リクエスト
            - AnalysisDummyChartUpdate: チャート更新リクエスト
            - AnalysisDummyChartResponse: チャートレスポンス
    分析セッション:
        分析ファイル:
            - AnalysisFileBase: 分析ファイルベース
            - AnalysisFileCreate: 分析ファイル作成リクエスト
            - AnalysisFileConfigResponse: 分析ファイル作成時の設定レスポンス
            - AnalysisFileUpdate: 分析ファイル更新リクエスト
            - AnalysisFileResponse: 分析ファイルレスポンス

        チャット:
            - AnalysisChatBase: チャットベース
            - AnalysisChatCreate: チャット作成リクエスト
            - AnalysisChatUpdate: チャット更新リクエスト
            - AnalysisChatResponse: チャットレスポンス

        ステップ:
            - AnalysisStepBase: ステップベース
            - AnalysisStepCreate: ステップ作成リクエスト
            - AnalysisStepUpdate: ステップ更新リクエスト
            - AnalysisStepDelete: ステップ削除リクエスト
            - AnalysisStepResponse: ステップレスポンス

        スナップショット:
            - AnalysisSnapshotBase: スナップショットベース
            - AnalysisSnapshotResponse: スナップショットレスポンス

        セッション:
            - AnalysisSessionBase: セッションベース
            - AnalysisSessionCreate: セッション作成リクエスト
            - AnalysisSessionUpdate: セッション更新リクエスト
            - AnalysisSessionResponse: セッションレスポンス
            - AnalysisSessionDetailResponse: セッション詳細レスポンス
            - AnalysisSessionResultResponse: セッション結果レスポンス

使用例:
    >>> from app.schemas.analysis import AnalysisFileCreate, AnalysisIssueCreate
    >>> file_data = AnalysisFileCreate(
    ...     project_file_id=project_file_id,
    ...     sheet_name="Sheet1",
    ...     axis_config={"軸1": "店舗名"},
    ...     data={"columns": ["店舗名", "売上"], "data": [["A店", 1000]]}
    ... )
"""

from app.schemas.analysis.analysis_session import (
    # チャット
    AnalysisChatBase,
    AnalysisChatCreate,
    AnalysisChatListResponse,
    AnalysisChatResponse,
    AnalysisChatUpdate,
    # 分析ファイル
    AnalysisFileBase,
    AnalysisFileConfigResponse,
    AnalysisFileCreate,
    AnalysisFileListResponse,
    AnalysisFileResponse,
    AnalysisFileUpdate,
    # セッション
    AnalysisSessionBase,
    AnalysisSessionCreate,
    AnalysisSessionDelete,
    AnalysisSessionDetailResponse,
    AnalysisSessionListResponse,
    AnalysisSessionResponse,
    AnalysisSessionResultListResponse,
    AnalysisSessionResultResponse,
    AnalysisSessionUpdate,
    # スナップショット
    AnalysisSnapshotBase,
    AnalysisSnapshotCreate,
    AnalysisSnapshotListResponse,
    AnalysisSnapshotResponse,
    # ステップ
    AnalysisStepBase,
    AnalysisStepCreate,
    AnalysisStepDelete,
    AnalysisStepResponse,
    AnalysisStepUpdate,
    # リレーション展開用Info
    CreatorInfo,
    InputFileInfo,
    IssueInfo,
    # バリデーション情報
    ValidationInfo,
)
from app.schemas.analysis.analysis_template import (
    # ダミーチャート
    AnalysisDummyChartBase,
    AnalysisDummyChartCreate,
    AnalysisDummyChartResponse,
    AnalysisDummyChartUpdate,
    # ダミー計算式
    AnalysisDummyFormulaBase,
    AnalysisDummyFormulaCreate,
    AnalysisDummyFormulaResponse,
    AnalysisDummyFormulaUpdate,
    # グラフ軸設定
    AnalysisGraphAxisBase,
    AnalysisGraphAxisCreate,
    AnalysisGraphAxisResponse,
    AnalysisGraphAxisUpdate,
    # 分析課題
    AnalysisIssueBase,
    AnalysisIssueCatalogListResponse,
    AnalysisIssueCatalogResponse,
    AnalysisIssueCreate,
    AnalysisIssueDetailResponse,
    AnalysisIssueUpdate,
    # 分析施策
    AnalysisValidationBase,
    AnalysisValidationCreate,
    AnalysisValidationResponse,
    AnalysisValidationUpdate,
    # 分析テンプレート（ユーザー作成）
    AnalysisTemplateCreateRequest,
    AnalysisTemplateCreateResponse,
    AnalysisTemplateDeleteResponse,
)

__all__ = [
    # 分析セッション
    "AnalysisSessionBase",
    "AnalysisSessionCreate",
    "AnalysisSessionUpdate",
    "AnalysisSessionDelete",
    "AnalysisSessionResponse",
    "AnalysisSessionDetailResponse",
    "AnalysisSessionListResponse",
    "AnalysisSessionResultResponse",
    "AnalysisSessionResultListResponse",
    # リレーション展開用Info
    "CreatorInfo",
    "InputFileInfo",
    "IssueInfo",
    # 分析スナップショット
    "AnalysisSnapshotBase",
    "AnalysisSnapshotCreate",
    "AnalysisSnapshotListResponse",
    "AnalysisSnapshotResponse",
    # 分析ファイル
    "AnalysisFileBase",
    "AnalysisFileCreate",
    "AnalysisFileResponse",
    "AnalysisFileConfigResponse",
    "AnalysisFileListResponse",
    "AnalysisFileUpdate",
    # チャット
    "AnalysisChatBase",
    "AnalysisChatCreate",
    "AnalysisChatListResponse",
    "AnalysisChatResponse",
    "AnalysisChatUpdate",
    # ステップ
    "AnalysisStepBase",
    "AnalysisStepCreate",
    "AnalysisStepResponse",
    "AnalysisStepUpdate",
    "AnalysisStepDelete",
    # バリデーション情報
    "ValidationInfo",
    # 分析施策
    "AnalysisValidationBase",
    "AnalysisValidationCreate",
    "AnalysisValidationUpdate",
    "AnalysisValidationResponse",
    # 分析課題
    "AnalysisIssueBase",
    "AnalysisIssueCreate",
    "AnalysisIssueUpdate",
    "AnalysisIssueCatalogResponse",
    "AnalysisIssueCatalogListResponse",
    "AnalysisIssueDetailResponse",
    # グラフ軸設定
    "AnalysisGraphAxisBase",
    "AnalysisGraphAxisCreate",
    "AnalysisGraphAxisUpdate",
    "AnalysisGraphAxisResponse",
    # ダミー計算式
    "AnalysisDummyFormulaBase",
    "AnalysisDummyFormulaCreate",
    "AnalysisDummyFormulaUpdate",
    "AnalysisDummyFormulaResponse",
    # ダミーチャート
    "AnalysisDummyChartBase",
    "AnalysisDummyChartCreate",
    "AnalysisDummyChartUpdate",
    "AnalysisDummyChartResponse",
    # 分析テンプレート（ユーザー作成）
    "AnalysisTemplateCreateRequest",
    "AnalysisTemplateCreateResponse",
    "AnalysisTemplateDeleteResponse",
]
