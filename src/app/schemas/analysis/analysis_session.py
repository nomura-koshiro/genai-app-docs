import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# 分析ファイルスキーマ
# ================================================================================
class AnalysisFileBase(BaseCamelCaseModel):
    """分析ファイルベーススキーマ。

    分析用に処理されたファイルの基本情報を定義します。

    Attributes:
        sheet_name (str): シート名
        axis_config (dict[str, Any]): 軸設定JSON(例: {'軸1': '店舗名', '軸2': '地域'})
        data (list[dict[str, Any]]): データJSON(pandas DataFrame の JSON 形式)
    """

    sheet_name: str = Field(..., max_length=255, description="シート名")
    axis_config: dict[str, Any] = Field(..., description="軸設定JSON")
    data: dict[str, Any] = Field(..., description="データJSON")


class AnalysisFileCreate(BaseCamelCaseModel):
    """分析ファイル作成スキーマ。

    新規分析ファイル作成時の入力データを定義します。
    注意: シート名、軸設定はここで指定できない、Update 時に設定してください。

    Attributes:
        project_file_id (uuid.UUID): プロジェクトファイルID

    Example:
        >>> analysis_file_create = AnalysisFileCreate(
        ...     project_file_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        ... )
    """

    project_file_id: uuid.UUID = Field(..., description="プロジェクトファイルID")


class AnalysisFileUpdate(BaseCamelCaseModel):
    """分析ファイル更新スキーマ。

    分析ファイル更新時の入力データを定義します。
    すべてのフィールドは Optional(部分更新対応)。

    Attributes:
        sheet_name (str | None): シート名
        axis_config (dict[str, Any] | None): 軸設定JSON

    Example:
        >>> analysis_file_update = AnalysisFileUpdate(
        ...     sheet_name="UpdatedSheet",
        ...     axis_config={"軸1": "店舗名", "軸2": "商品カテゴリ"}
        ... )
    """

    sheet_name: str | None = Field(default=None, max_length=255, description="シート名")
    axis_config: dict[str, Any] | None = Field(default=None, description="軸設定JSON")


class AnalysisFileConfigResponse(BaseCamelCaseModel):
    """分析ファイル設定レスポンススキーマ。

    分析ファイルの設定情報を返すレスポンスを定義します。
    ファイル選択後、軸設定、シート設定の候補を返す際に使用します。

    Attributes:
        id (uuid.UUID): 分析ファイルID
        config_list (list[dict[str, Any]]): 設定候補リスト

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "config_list": [
        ...         {
        ...             "sheet_name": "Sheet1",
        ...             "axis_config": {"軸1": "店舗名", "軸2": "地域"}
        ...         },
        ...         {
        ...             "sheet_name": "Sheet2",
        ...             "axis_config": {"軸1": "商品カテゴリ", "軸2": "売上"}
        ...         }
        ...     ]
        ... }
    """

    id: uuid.UUID = Field(..., description="分析ファイルID")
    config_list: list[dict[str, Any]] = Field(..., description="設定候補リスト")


class AnalysisFileResponse(BaseCamelCaseORMModel):
    """分析ファイルレスポンススキーマ。

    分析ファイル情報の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): 分析ファイルID
        session_id (uuid.UUID): セッションID
        project_file_id (uuid.UUID): プロジェクトファイルID
        project_file_name (str): プロジェクトファイル名 (結合データ)
        sheet_name (str): シート名
        axis_config (dict[str, Any]): 軸設定JSON
        data (dict[str, Any]): データJSON
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "session_id": "323e4567-e89b-12d3-a456-426614174222",
        ...     "project_file_id": "223e4567-e89b-12d3-a456-426614174111",
        ...     "project_file_name": "sales_data.xlsx",
        ...     "sheet_name": "Sheet1",
        ...     "axis_config": {"軸1": "店舗名", "軸2": "地域"},
        ...     "data": [{"店舗名": "A店", "売上": 1000, "地域": "東京"}, ...], // pandas DataFrame の record 形式
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="分析ファイルID")
    sheet_name: str = Field(..., max_length=255, description="シート名")
    axis_config: dict[str, Any] = Field(..., description="軸設定JSON")
    data: list[dict[str, Any]] = Field(..., description="データJSON（pandas DataFrameのrecord形式）")
    session_id: uuid.UUID = Field(..., description="セッションID")
    project_file_id: uuid.UUID = Field(..., description="プロジェクトファイルID")
    project_file_name: str = Field(..., description="プロジェクトファイル名")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# チャットスキーマ
# ================================================================================
class AnalysisChatBase(BaseCamelCaseModel):
    """ベース分析チャットスキーマ。

    チャットメッセージの基本情報を定義します。

    Attributes:
        chat_order (int): チャット順序
        role (str): ロール(例: "user", "assistant")
        message (str | None): メッセージ内容
    """

    chat_order: int = Field(..., description="チャット順序")
    role: str = Field(..., max_length=50, description="ロール(例: 'user', 'assistant')")
    message: str | None = Field(default=None, description="メッセージ内容")


class AnalysisChatCreate(BaseCamelCaseModel):
    """分析チャット作成リクエストスキーマ。

    現在のsnapshotに新規チャットメッセージ作成時に使用します。

    Attributes:
        message (str): メッセージ内容

    Example:
        >>> chat = AnalysisChatCreate(
        ...     message="売上の推移を分析してください"
        ... )
    """

    # create時はrole = userなので、設定不要
    # role: str = Field(..., max_length=50, description="ロール(例: 'user', 'assistant')")
    message: str = Field(..., description="メッセージ内容")


class AnalysisChatUpdate(BaseCamelCaseModel):
    """分析チャット更新リクエストスキーマ。

    既存のチャットメッセージを更新する際に使用します。
    すべてのフィールドは Optional(部分更新対応)。

    Attributes:
        chat_order (int | None): チャット順序
        role (str | None): ロール
        message (str | None): メッセージ内容
    """

    chat_order: int | None = Field(default=None, description="チャット順序")
    role: str | None = Field(default=None, max_length=50, description="ロール")
    message: str | None = Field(default=None, description="メッセージ内容")


class AnalysisChatResponse(BaseCamelCaseORMModel):
    """分析チャットレスポンススキーマ。

    チャットのレスポンスを定義します。

    Attributes:
        id (uuid.UUID): チャットID
        chat_order (int): チャット順序
        snapshot (int): 最初に出現したスナップショット番号
        role (str): ロール
        message (str | None): メッセージ内容
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "423e4567-e89b-12d3-a456-426614174333",
        ...     "chat_order": 1,
        ...     "snapshot": 1,
        ...     "role": "user",
        ...     "message": "売上の推移を分析してください",
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-02T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="チャットID")
    chat_order: int = Field(..., description="チャット順序")
    snapshot: int = Field(default=1, description="最初に出現したスナップショット番号")
    role: str = Field(..., max_length=50, description="ロール(例: 'user', 'assistant')")
    message: str | None = Field(default=None, description="メッセージ内容")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# ステップスキーマ
# ================================================================================
class AnalysisStepBase(BaseCamelCaseModel):
    """ベース分析ステップスキーマ。

    分析ステップの基本情報を定義します。

    Attributes:
        name (str): ステップ名
        step_order (int): ステップ順序
        type (str): ステップタイプ(例: "filter", "aggregation", "transform", "summary")
        input (str): 入力データの参照
        config (dict[str, Any]): ステップ設定(JSON)
    """

    name: str = Field(..., max_length=255, description="ステップ名")
    step_order: int = Field(..., description="ステップ順序")
    type: str = Field(..., max_length=50, description="ステップタイプ")
    input: str = Field(..., max_length=255, description="入力データの参照")
    config: dict[str, Any] = Field(..., description="ステップ設定(JSON)")


class AnalysisStepCreate(BaseCamelCaseModel):
    """分析ステップ作成リクエストスキーマ。

    新規ステップ作成時に使用します。

    Attributes:
        name (str): ステップ名
        type (str): ステップタイプ (例: "filter", "aggregation", "transform", "summary")
        input (str): 入力データの参照

    Example:
        >>> step = AnalysisStepCreate(
        ...     name="売上フィルタ",
        ...     type="filter",
        ...     input="step_1", // ステップ1の出力を参照
        ... )
    """

    name: str = Field(..., max_length=255, description="ステップ名")
    type: str = Field(..., max_length=50, description="ステップタイプ")
    input: str = Field(..., max_length=255, description="入力データの参照")


class AnalysisStepUpdate(BaseCamelCaseModel):
    """分析ステップ更新リクエストスキーマ。

    既存のステップを更新する際に使用します。
    すべてのフィールドは Optional(部分更新対応)。

    Attributes:
        name (str | None): ステップ名
        type (str | None): ステップタイプ
        input (str | None): 入力データの参照
        config (dict[str, Any] | None): ステップ設定
    """

    name: str | None = Field(default=None, max_length=255, description="ステップ名")
    type: str | None = Field(default=None, max_length=50, description="ステップタイプ")
    input: str | None = Field(default=None, max_length=255, description="入力データの参照")
    config: dict[str, Any] | None = Field(default=None, description="ステップ設定")


class AnalysisStepDelete(BaseCamelCaseModel):
    """分析ステップ削除リクエストスキーマ。

    ステップ削除時に使用します。

    Attributes:
        id (uuid.UUID): ステップID
    """

    id: uuid.UUID = Field(..., description="ステップID")


class AnalysisStepResponse(BaseCamelCaseORMModel):
    """分析ステップレスポンススキーマ。

    ステップ情報の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): ステップID
        name (str): ステップ名
        step_order (int): ステップ順序
        type (str): ステップタイプ
        input (str): 入力データの参照
        config (dict[str, Any]): ステップ設定
        snapshot_id (uuid.UUID): スナップショットID
        result_data (list[dict[str, Any]] | None): 結果データ (中間保存用)
        result_formula (list[dict[str, Any]] | None): 結果の数式リスト
        result_chart (dict[str, Any] | None): 結果のチャート (plotly の JSON)
        result_table (list[dict[str, Any]] | None): 結果のテーブル (pandasのto_dict(orient='records')形式)
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
        result_data (list[dict[str, Any]] | None): 結果データ (中間保存用)
        result_formula (list[dict[str, Any]] | None): 結果の数式リスト
        result_chart (dict[str, Any] | None): 結果のチャート (plotly の JSON)
        result_table (list[dict[str, Any]] | None): 結果のテーブル (pandasのto_dict(orient='records')形式)

    Example:
        >>> {
        ...     "id": "523e4567-e89b-12d3-a456-426614174444",
        ...     "name": "売上フィルタ",
        ...     "step_order": 1,
        ...     "type": "filter",
        ...     "input": "step_1",
        ...     "config": {"条件": "売上 > 1000"},
        ...     "result_formula": [{'name': '合計売上', 'value': '100', 'unit': '円'}, ...],
        ...     "result_chart": {"data": [...], "layout": {...}},  // plotlyのJSON形式
        ...     "result_table": [{"店舗名": "A店", "売上": 1000, "地域": "東京"}],  // pandasのto_dict(orient='records')形式
        ...     "snapshot_id": "323e4567-e89b-12d3-a456-426614174222",
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-02T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="ステップID")
    name: str = Field(..., max_length=255, description="ステップ名")
    step_order: int = Field(..., description="ステップ順序")
    type: str = Field(..., max_length=50, description="ステップタイプ")
    input: str = Field(..., max_length=255, description="入力データの参照")
    config: dict[str, Any] = Field(..., description="ステップ設定(JSON)")
    snapshot_id: uuid.UUID = Field(..., description="スナップショットID")
    result_data: list[dict[str, Any]] | None = Field(default=None, description="結果データ (中間保存用)")
    result_formula: list[dict[str, Any]] | None = Field(default=None, description="結果の数式リスト")
    result_chart: dict[str, Any] | None = Field(default=None, description="結果のチャート (plotly の JSON)")
    result_table: list[dict[str, Any]] | None = Field(default=None, description="結果のテーブル (pandasのto_dict(orient='records')形式)")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# snapshotスキーマ
# ================================================================================
class AnalysisSnapshotBase(BaseCamelCaseModel):
    """ベース分析スナップショットスキーマ。

    分析スナップショットの基本情報を定義します。

    Attributes:
        snapshot_order (int): スナップショット順序
        chat (list[AnalysisChatResponse]): チャットメッセージリスト
        step (list[AnalysisStepResponse]): ステップリスト
    """

    snapshot_order: int = Field(..., description="スナップショット順序")
    chat: list[AnalysisChatResponse] = Field(default=[], description="チャットメッセージリスト")
    step: list[AnalysisStepResponse] = Field(default=[], description="ステップリスト")


class AnalysisSnapshotResponse(BaseCamelCaseORMModel):
    """分析スナップショットレスポンススキーマ。

    分析スナップショット情報の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): スナップショットID
        snapshot_order (int): スナップショット順序
        chat (list[AnalysisChatResponse]): チャットメッセージリスト
        step (list[AnalysisStepResponse]): ステップリスト
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "623e4567-e89b-12d3-a456-426614174555",
        ...     "snapshot_order": 1,
        ...     "chat": [AnalysisChatResponse, ...],
        ...     "step": [AnalysisStepResponse, ...],
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-02T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="スナップショットID")
    snapshot_order: int = Field(..., description="スナップショット順序")
    chat: list[AnalysisChatResponse] = Field(default=[], description="チャットメッセージリスト")
    step: list[AnalysisStepResponse] = Field(default=[], description="ステップリスト")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# 分析セッションスキーマ
# ================================================================================
class AnalysisSessionBase(BaseCamelCaseModel):
    """ベース分析セッションスキーマ。

    分析セッションの基本情報を定義します。

    Attributes:
        current_snapshot (int): 現在のスナップショット番号
    """

    current_snapshot: int = Field(..., description="現在のスナップショット番号")


class AnalysisSessionCreate(BaseCamelCaseModel):
    """分析セッション作成リクエストスキーマ。

    新規分析セッション作成時に使用します。

    Attributes:
        issue_id (uuid.UUID): 課題ID

    Example:
        >>> session = AnalysisSessionCreate(
        ...     issue_id=uuid.uuid4(),
        ... )
    """

    issue_id: uuid.UUID = Field(..., description="課題ID")


class AnalysisSessionUpdate(BaseCamelCaseModel):
    """分析セッション更新リクエストスキーマ。

    既存の分析セッションを更新する際に使用します。
    選択ファイルの変更、またはスナップショットの切り替えに対応。
    すべてのフィールドは Optional(部分更新対応)。

    Attributes:
        current_snapshot (int | None): 現在のスナップショット番号
        input_file_id (uuid.UUID | None): 入力ファイルID

    Example:
        >>> session_update = AnalysisSessionUpdate(
        ...     current_snapshot=変更後の番号,
        ...     input_file_id=変更後のファイルID
        ... )
    """

    current_snapshot: int | None = Field(default=None, description="現在のスナップショット番号")
    input_file_id: uuid.UUID | None = Field(default=None, description="入力ファイルID")


class AnalysisSessionDelete(BaseCamelCaseModel):
    """分析セッション削除リクエストスキーマ。

    分析セッション削除時に使用します。

    Attributes:
        id (uuid.UUID): セッションID
    """

    id: uuid.UUID = Field(..., description="セッションID")


class AnalysisSessionResponse(BaseCamelCaseORMModel):
    """分析セッションレスポンススキーマ。

    分析セッションを選択するときに、レスポンスとして返す際に使用します。
    詳細内容は含まれません。

    Attributes:
        id (uuid.UUID): セッションID
        current_snapshot (int): 現在のスナップショット番号
        project_id (uuid.UUID): プロジェクトID
        issue_id (uuid.UUID): 課題ID
        creator_id (uuid.UUID): 作成者のユーザーID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "223e4567-e89b-12d3-a456-426614174111",
        ...     "project_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "issue_id": "323e4567-e89b-12d3-a456-426614174222",
        ...     "creator_id": "423e4567-e89b-12d3-a456-426614174333",
        ...     "current_snapshot": 2,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-02T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="セッションID")
    current_snapshot: int = Field(..., description="現在のスナップショット番号")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    issue_id: uuid.UUID = Field(..., description="課題ID")
    creator_id: uuid.UUID = Field(..., description="作成者のユーザーID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnalysisSessionDetailResponse(AnalysisSessionResponse):
    """分析セッション詳細レスポンススキーマ。

    分析セッションの詳細情報を含むレスポンスを定義します。

    Attributes:
        input_file_id (uuid.UUID | None): 入力ファイルID

    Example:
        >>> {
        ...     "id": "223e4567-e89b-12d3-a456-426614174111",
        ...     "project_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "issue_id": "323e4567-e89b-12d3-a456-426614174222",
        ...     "creator_id": "423e4567-e89b-12d3-a456-426614174333",
        ...     "current_snapshot": 2,
        ...     "snapshot_list": [AnalysisSnapshotResponse, ...],
        ...     "file_list": [AnalysisFileResponse, ...],
        ...     "input_file_id": "523e4567-e89b-12d3-a456-426614174444",
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-02T00:00:00Z"
        ... }
    """

    input_file_id: uuid.UUID | None = Field(default=None, description="入力ファイルID")
    snapshot_list: list[AnalysisSnapshotResponse] = Field(default=[], description="スナップショットリスト")
    file_list: list[AnalysisFileResponse] = Field(default=[], description="分析ファイルリスト")


class AnalysisSessionResultResponse(BaseCamelCaseModel):
    """分析セッション結果レスポンススキーマ。

    分析セッションのサマリステップ結果を含むレスポンスを定義します。

    Attributes:
        step_id (uuid.UUID): ステップID
        step_name (str): ステップ名
        result_formula (list[dict[str, Any]] | None): 結果の数式リスト
        result_chart (dict[str, Any] | None): 結果のチャート (plotly の JSON)
        result_table (list[dict[str, Any]] | None): 結果のテーブル (pandasのto_dict(orient='records')形式)
    """

    step_id: uuid.UUID = Field(..., description="ステップID")
    step_name: str = Field(..., description="ステップ名")
    result_formula: list[dict[str, Any]] | None = Field(default=None, description="結果の数式リスト")
    result_chart: dict[str, Any] | None = Field(default=None, description="結果のチャート (plotly の JSON)")
    result_table: list[dict[str, Any]] | None = Field(default=None, description="結果のテーブル (pandasのto_dict(orient='records')形式)")


# ================================================================================
# 一覧レスポンススキーマ
# ================================================================================
class AnalysisSessionListResponse(BaseCamelCaseModel):
    """分析セッション一覧レスポンススキーマ。

    分析セッション一覧APIのレスポンス形式を定義します。

    Attributes:
        sessions (list[AnalysisSessionResponse]): セッションリスト
        total (int): 総件数
        skip (int): スキップ数（オフセット）
        limit (int): 取得件数

    Example:
        >>> response = AnalysisSessionListResponse(
        ...     sessions=[session1, session2, session3],
        ...     total=100,
        ...     skip=0,
        ...     limit=10
        ... )
    """

    sessions: list[AnalysisSessionResponse] = Field(..., description="セッションリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数（オフセット）")
    limit: int = Field(..., description="取得件数")


class AnalysisFileListResponse(BaseCamelCaseModel):
    """分析ファイル一覧レスポンススキーマ。

    分析ファイル一覧APIのレスポンス形式を定義します。

    Attributes:
        files (list[AnalysisFileResponse]): ファイルリスト
        total (int): 総件数

    Example:
        >>> response = AnalysisFileListResponse(
        ...     files=[file1, file2, file3],
        ...     total=3
        ... )
    """

    files: list[AnalysisFileResponse] = Field(..., description="ファイルリスト")
    total: int = Field(..., description="総件数")


class AnalysisSessionResultListResponse(BaseCamelCaseModel):
    """分析セッション結果一覧レスポンススキーマ。

    分析セッション結果一覧APIのレスポンス形式を定義します。

    Attributes:
        results (list[AnalysisSessionResultResponse]): 結果リスト
        total (int): 総件数

    Example:
        >>> response = AnalysisSessionResultListResponse(
        ...     results=[result1, result2, result3],
        ...     total=3
        ... )
    """

    results: list[AnalysisSessionResultResponse] = Field(..., description="結果リスト")
    total: int = Field(..., description="総件数")
