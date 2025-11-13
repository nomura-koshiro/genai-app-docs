"""分析セッション管理のPydanticスキーマ。

このモジュールは、分析セッション、ステップ、ファイル管理の
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    分析セッション:
        - AnalysisSessionBase: 基本セッション情報
        - AnalysisSessionCreate: セッション作成リクエスト
        - AnalysisSessionUpdate: セッション更新リクエスト
        - AnalysisSessionResponse: セッション情報レスポンス
        - AnalysisSessionDetailResponse: セッション詳細レスポンス

    分析ステップ:
        - AnalysisStepBase: 基本ステップ情報
        - AnalysisStepCreate: ステップ作成リクエスト
        - AnalysisStepResponse: ステップ情報レスポンス

    分析ファイル:
        - AnalysisFileBase: 基本ファイル情報
        - AnalysisFileUploadRequest: ファイルアップロードリクエスト
        - AnalysisFileResponse: ファイル情報レスポンス

    スナップショット:
        - AnalysisStepSnapshot: スナップショット内のステップデータ
        - SnapshotHistoryItem: 1つのスナップショット（AnalysisStepSnapshotのリスト）
        - SnapshotHistory: スナップショット履歴（SnapshotHistoryItemのリスト）

    チャット履歴:
        - AnalysisChatMessage: チャット履歴のメッセージ
        - ChatHistory: チャット履歴（AnalysisChatMessageのリスト）

    結果数式:
        - AnalysisResultFormula: サマリーステップの計算結果
        - AnalysisResultFormulaList: 結果数式のリスト

    ファイルメタデータ:
        - AnalysisFileMetadata: アップロードファイルのメタ情報

    AIチャット:
        - AnalysisChatRequest: チャットリクエスト
        - AnalysisChatResponse: チャット応答

使用方法:
    >>> from app.schemas.analysis.session import AnalysisSessionCreate, AnalysisChatRequest
    >>>
    >>> # セッション作成
    >>> session = AnalysisSessionCreate(
    ...     project_id=uuid.uuid4(),
    ...     policy="市場拡大",
    ...     issue="新規参入"
    ... )
    >>>
    >>> # AIチャット
    >>> chat = AnalysisChatRequest(
    ...     message="売上データを東京と大阪でフィルタリングしてください"
    ... )
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ================================================================================
# スナップショット関連スキーマ
# ================================================================================


class AnalysisStepSnapshot(BaseModel):
    """スナップショット内のステップデータ。

    snapshot_historyに保存される個別ステップの情報を定義します。
    結果データ（result_data, result_chart, result_formula）は含まれません。

    Attributes:
        name (str): ステップ名
        type (str): ステップタイプ（filter/aggregation/transform/summary）
        data (str): データソース（ファイルIDまたは前ステップID）
        config (dict[str, Any]): ステップ設定

    Example:
        >>> snapshot = AnalysisStepSnapshot(
        ...     name="売上フィルタ",
        ...     type="filter",
        ...     data="file_abc123",
        ...     config={"category": {"地域": ["東京", "大阪"]}}
        ... )
    """

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., description="ステップ名")
    type: str = Field(..., description="ステップタイプ")
    data: str = Field(..., description="データソース")
    config: dict[str, Any] = Field(default_factory=dict, description="ステップ設定")


# スナップショット履歴の型定義
# - SnapshotHistoryItem: 1つのスナップショット（複数のステップのリスト）
# - SnapshotHistory: スナップショット履歴（スナップショットのリスト）
#
# 注意: DB保存時は model_dump() で dict に変換されるため、
# 実際のDB型は list[list[dict[str, Any]]] となります。
# 使用時に AnalysisStepSnapshot.model_validate() で型変換してください。
SnapshotHistoryItem = list[AnalysisStepSnapshot]
SnapshotHistory = list[SnapshotHistoryItem]


class AnalysisChatMessage(BaseModel):
    """チャット履歴のメッセージスキーマ。

    AIエージェントとのチャット履歴を構造化して保存します。

    Attributes:
        role (Literal["user", "assistant"]): メッセージの送信者
        content (str): メッセージ内容
        timestamp (str): タイムスタンプ（ISO8601形式推奨）

    Example:
        >>> message = AnalysisChatMessage(
        ...     role="user",
        ...     content="売上データを東京でフィルタリングしてください",
        ...     timestamp="2024-01-15T10:30:00Z"
        ... )
    """

    model_config = ConfigDict(frozen=False)

    role: Literal["user", "assistant"] = Field(..., description="メッセージの送信者")
    content: str = Field(..., description="メッセージ内容")
    timestamp: str = Field(..., description="タイムスタンプ（ISO8601形式）")


# チャット履歴の型定義
ChatHistory = list[AnalysisChatMessage]


class AnalysisResultFormula(BaseModel):
    """結果数式スキーマ。

    サマリーステップの計算結果を表現します。

    Attributes:
        name (str): 数式名（例: "売上合計"）
        formula (str): 計算式（例: "sum(売上)"）
        result (float): 計算結果
        unit (str | None): 単位（例: "円", "%"）

    Example:
        >>> formula = AnalysisResultFormula(
        ...     name="売上合計",
        ...     formula="sum(売上)",
        ...     result=1000000.0,
        ...     unit="円"
        ... )
    """

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., description="数式名")
    formula: str = Field(..., description="計算式")
    result: float = Field(..., description="計算結果")
    unit: str | None = Field(default=None, description="単位")


# 結果数式の型定義
AnalysisResultFormulaList = list[AnalysisResultFormula]


class AnalysisFileMetadata(BaseModel):
    """ファイルメタデータスキーマ。

    アップロードされたファイルのメタ情報を保存します。

    Attributes:
        sheet_name (str | None): シート名（Excelファイルの場合）
        row_count (int): 行数
        column_count (int): 列数
        columns (list[str] | None): カラム名のリスト

    Example:
        >>> metadata = AnalysisFileMetadata(
        ...     sheet_name="Sheet1",
        ...     row_count=1000,
        ...     column_count=10,
        ...     columns=["ID", "名前", "売上"]
        ... )
    """

    model_config = ConfigDict(frozen=False)

    sheet_name: str | None = Field(default=None, description="シート名（Excelファイルの場合）")
    row_count: int = Field(..., ge=0, description="行数")
    column_count: int = Field(..., ge=0, description="列数")
    columns: list[str] | None = Field(default=None, description="カラム名のリスト")


# ================================================================================
# 分析セッションスキーマ
# ================================================================================


class AnalysisSessionBase(BaseModel):
    """ベース分析セッションスキーマ。

    分析セッションの基本情報を定義します。

    Attributes:
        session_name (str | None): セッション名
        validation_config (dict[str, Any]): validation設定
    """

    session_name: str | None = Field(default=None, max_length=255, description="セッション名")
    validation_config: dict[str, Any] = Field(default_factory=dict, description="分析設定（validation.ymlの内容）")


class AnalysisSessionCreate(BaseModel):
    """分析セッション作成リクエストスキーマ。

    新規分析セッション作成時に使用します。

    Attributes:
        project_id (uuid.UUID): プロジェクトID
        policy (str): 施策名
        issue (str): 課題名
        session_name (str | None): セッション名（オプション）

    Example:
        >>> session = AnalysisSessionCreate(
        ...     project_id=uuid.uuid4(),
        ...     policy="市場拡大",
        ...     issue="新規参入",
        ...     session_name="2024年第1四半期分析"
        ... )
    """

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    policy: str = Field(..., min_length=1, max_length=100, description="施策名")
    issue: str = Field(..., min_length=1, max_length=100, description="課題名")
    session_name: str | None = Field(default=None, max_length=255, description="セッション名")


class AnalysisSessionUpdate(BaseModel):
    """分析セッション更新リクエストスキーマ。

    セッション情報の更新時に使用します。

    Attributes:
        session_name (str | None): セッション名
        is_active (bool | None): アクティブフラグ

    Example:
        >>> update = AnalysisSessionUpdate(
        ...     session_name="Updated Session Name",
        ...     is_active=False
        ... )

    Note:
        - すべてのフィールドはオプションです
        - validation_configは変更できません
    """

    session_name: str | None = Field(default=None, max_length=255, description="セッション名")
    is_active: bool | None = Field(default=None, description="アクティブフラグ")


class AnalysisSessionResponse(BaseModel):
    """分析セッション情報レスポンススキーマ。

    APIレスポンスでセッション情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): セッションID
        project_id (uuid.UUID): プロジェクトID
        created_by (uuid.UUID | None): 作成者のユーザーID
        session_name (str | None): セッション名
        validation_config (dict[str, Any]): validation設定
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> from datetime import UTC
        >>> session = AnalysisSessionResponse(
        ...     id=uuid.uuid4(),
        ...     project_id=uuid.uuid4(),
        ...     created_by=uuid.uuid4(),
        ...     session_name="売上分析",
        ...     validation_config={"policy": "市場拡大", "issue": "新規参入"},
        ...     is_active=True,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC)
        ... )

    Note:
        - from_attributesを有効にしているため、ORMモデルから直接変換可能です
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="セッションID（UUID）")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    created_by: uuid.UUID | None = Field(default=None, description="作成者のユーザーID")
    session_name: str | None = Field(default=None, description="セッション名")
    validation_config: dict[str, Any] = Field(..., description="validation設定")
    is_active: bool = Field(..., description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時（UTC）")
    updated_at: datetime = Field(..., description="更新日時（UTC）")


class AnalysisSessionDetailResponse(AnalysisSessionResponse):
    """分析セッション詳細レスポンススキーマ。

    セッション情報に加えて、ステップとファイルの情報も含みます。

    Attributes:
        id (uuid.UUID): セッションID（継承）
        project_id (uuid.UUID): プロジェクトID（継承）
        created_by (uuid.UUID | None): 作成者のユーザーID（継承）
        session_name (str | None): セッション名（継承）
        validation_config (dict[str, Any]): validation設定（継承）
        chat_history (ChatHistory): チャット履歴
            各メッセージは AnalysisChatMessage（DB保存時はdictに変換）
        snapshot_history (SnapshotHistory | None): スナップショット履歴
            各スナップショットはAnalysisStepSnapshotのリスト（list[list[AnalysisStepSnapshot]]）
            DB保存時はdictに変換されます
        steps (list[AnalysisStepResponse]): 分析ステップリスト
        files (list[AnalysisFileResponse]): アップロードファイルリスト
        is_active (bool): アクティブフラグ（継承）
        created_at (datetime): 作成日時（継承）
        updated_at (datetime): 更新日時（継承）
    """

    chat_history: list[dict[str, Any]] = Field(default_factory=list, description="チャット履歴")
    snapshot_history: list[list[dict[str, Any]]] | None = Field(default=None, description="スナップショット履歴")
    steps: list["AnalysisStepResponse"] = Field(default_factory=list, description="分析ステップリスト")
    files: list["AnalysisFileResponse"] = Field(default_factory=list, description="アップロードファイルリスト")


# ================================================================================
# 分析ステップスキーマ
# ================================================================================


class AnalysisStepBase(BaseModel):
    """ベース分析ステップスキーマ。

    分析ステップの基本情報を定義します。

    Attributes:
        step_name (str): ステップ名
        step_type (str): ステップタイプ（filter/aggregate/transform/summary）
        data_source (str): データソース
        config (dict[str, Any]): ステップ設定
    """

    step_name: str = Field(..., min_length=1, max_length=255, description="ステップ名")
    step_type: str = Field(
        ...,
        pattern="^(filter|aggregate|transform|summary)$",
        description="ステップタイプ（filter/aggregate/transform/summary）",
    )
    data_source: str = Field(default="original", max_length=100, description="データソース（original/step_0/step_1/...）")
    config: dict[str, Any] = Field(default_factory=dict, description="ステップ設定")


class AnalysisStepCreate(AnalysisStepBase):
    """分析ステップ作成リクエストスキーマ。

    新規ステップ追加時に使用します。

    Attributes:
        session_id (uuid.UUID): セッションID
        step_name (str): ステップ名（継承）
        step_type (str): ステップタイプ（継承）
        data_source (str): データソース（継承）
        config (dict[str, Any]): ステップ設定（継承）

    Example:
        >>> step = AnalysisStepCreate(
        ...     session_id=uuid.uuid4(),
        ...     step_name="売上フィルタリング",
        ...     step_type="filter",
        ...     data_source="original",
        ...     config={"category_filter": {"地域": ["東京", "大阪"]}}
        ... )
    """

    session_id: uuid.UUID = Field(..., description="セッションID")


class AnalysisStepResponse(AnalysisStepBase):
    """分析ステップ情報レスポンススキーマ。

    APIレスポンスでステップ情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): ステップID
        session_id (uuid.UUID): セッションID
        step_name (str): ステップ名（継承）
        step_type (str): ステップタイプ（継承）
        step_order (int): ステップの順序
        data_source (str): データソース（継承）
        config (dict[str, Any]): ステップ設定（継承）
        result_data_path (str | None): 結果データのストレージパス
        result_chart (dict[str, Any] | None): 結果チャート（Plotly JSON）
        result_formula (AnalysisResultFormulaList | None): 結果数式（各要素は AnalysisResultFormula）
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ステップID")
    session_id: uuid.UUID = Field(..., description="セッションID")
    step_order: int = Field(..., description="ステップの順序（0から開始）")
    result_data_path: str | None = Field(default=None, description="結果データのストレージパス")
    result_chart: dict[str, Any] | None = Field(default=None, description="結果チャート（Plotly JSON）")
    result_formula: list[dict[str, Any]] | None = Field(default=None, description="結果数式リスト（論理型: AnalysisResultFormulaList）")
    is_active: bool = Field(..., description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時（UTC）")
    updated_at: datetime = Field(..., description="更新日時（UTC）")


# ================================================================================
# 分析ファイルスキーマ
# ================================================================================


class AnalysisFileBase(BaseModel):
    """ベース分析ファイルスキーマ。

    分析ファイルの基本情報を定義します。

    Attributes:
        file_name (str): ファイル名
        table_name (str): テーブル名
        table_axis (list[str] | None): 軸候補のリスト
    """

    file_name: str = Field(..., min_length=1, max_length=255, description="ファイル名")
    table_name: str = Field(..., min_length=1, max_length=255, description="テーブル名")
    table_axis: list[str] | None = Field(default=None, description="軸候補のリスト")


class AnalysisFileUploadRequest(AnalysisFileBase):
    """分析ファイルアップロードリクエストスキーマ。

    ファイルアップロード時に使用します。

    Attributes:
        session_id (uuid.UUID): セッションID
        file_name (str): ファイル名（継承）
        table_name (str): テーブル名（継承）
        table_axis (list[str] | None): 軸候補のリスト（継承）
        data (str): DataFrameのCSV文字列

    Example:
        >>> upload = AnalysisFileUploadRequest(
        ...     session_id=uuid.uuid4(),
        ...     file_name="sales_data.xlsx",
        ...     table_name="売上データ",
        ...     table_axis=["地域", "商品"],
        ...     data="地域,商品,売上\\n東京,商品A,1000\\n..."
        ... )
    """

    session_id: uuid.UUID = Field(..., description="セッションID")
    data: str = Field(..., description="DataFrameのCSV文字列")


class AnalysisFileResponse(AnalysisFileBase):
    """分析ファイル情報レスポンススキーマ。

    APIレスポンスでファイル情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): ファイルID
        session_id (uuid.UUID): セッションID
        uploaded_by (uuid.UUID | None): アップロード者のユーザーID
        file_name (str): ファイル名（継承）
        table_name (str): テーブル名（継承）
        storage_path (str): ストレージパス
        file_size (int): ファイルサイズ（バイト）
        content_type (str | None): MIMEタイプ
        table_axis (list[str] | None): 軸候補のリスト（継承）
        file_metadata (dict[str, Any] | None): その他のメタデータ
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ファイルID")
    session_id: uuid.UUID = Field(..., description="セッションID")
    uploaded_by: uuid.UUID | None = Field(default=None, description="アップロード者のユーザーID")
    storage_path: str = Field(..., description="ストレージパス")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")
    content_type: str | None = Field(default=None, description="MIMEタイプ")
    file_metadata: AnalysisFileMetadata | None = Field(default=None, description="ファイルメタデータ")
    is_active: bool = Field(..., description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時（UTC）")
    updated_at: datetime = Field(..., description="更新日時（UTC）")


class AnalysisFileUploadResponse(BaseModel):
    """分析ファイルアップロード成功レスポンススキーマ。

    ファイルアップロード直後に返却される情報を含みます。

    Attributes:
        id (uuid.UUID): ファイルID
        session_id (uuid.UUID): セッションID
        file_name (str): ファイル名
        table_name (str): テーブル名
        storage_path (str): ストレージパス
        file_size (int): ファイルサイズ（バイト）
        content_type (str | None): MIMEタイプ
        table_axis (list[str] | None): 軸候補のリスト
        uploaded_by (uuid.UUID | None): アップロード者のユーザーID
        created_at (datetime): 作成日時
        message (str): 成功メッセージ
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ファイルID")
    session_id: uuid.UUID = Field(..., description="セッションID")
    file_name: str = Field(..., description="ファイル名")
    table_name: str = Field(..., description="テーブル名")
    storage_path: str = Field(..., description="ストレージパス")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")
    content_type: str | None = Field(default=None, description="MIMEタイプ")
    table_axis: list[str] | None = Field(default=None, description="軸候補のリスト")
    uploaded_by: uuid.UUID | None = Field(default=None, description="アップロード者のユーザーID")
    created_at: datetime = Field(..., description="作成日時（UTC）")
    message: str = Field(..., description="成功メッセージ")


# ================================================================================
# AIチャットスキーマ
# ================================================================================


class AnalysisChatRequest(BaseModel):
    """AIチャットリクエストスキーマ。

    AIエージェントとのチャット時に使用します。

    Attributes:
        message (str): ユーザーのメッセージ

    Example:
        >>> chat = AnalysisChatRequest(
        ...     message="売上データを東京と大阪でフィルタリングしてください"
        ... )
    """

    message: str = Field(..., min_length=1, description="ユーザーのメッセージ")


class AnalysisChatResponse(BaseModel):
    """AIチャット応答スキーマ。

    AIエージェントからの応答を返す際に使用します。

    Attributes:
        message (str): AIエージェントのメッセージ
        snapshot_id (int): スナップショットID
        steps_added (int): 追加されたステップ数
        steps_modified (int): 変更されたステップ数
        analysis_result (dict[str, Any] | None): 分析結果（チャート、数式など）

    Example:
        >>> response = AnalysisChatResponse(
        ...     message="東京と大阪でフィルタリングしました。",
        ...     steps_added=1,
        ...     steps_modified=0,
        ...     analysis_result={"chart": {...}, "formula": [...]}
        ... )
    """

    message: str = Field(..., description="AIエージェントのメッセージ")
    snapshot_id: int = Field(..., description="スナップショットID")
    steps_added: int = Field(default=0, description="追加されたステップ数")
    steps_modified: int = Field(default=0, description="変更されたステップ数")
    analysis_result: dict[str, Any] | None = Field(default=None, description="分析結果")


# ================================================================================
# その他のスキーマ
# ================================================================================


class AnalysisValidationConfigResponse(BaseModel):
    """validation設定レスポンススキーマ。

    validation.ymlの内容を返す際に使用します。

    Attributes:
        validation_config (dict[str, Any]): validation設定の全体

    Example:
        >>> config = AnalysisValidationConfigResponse(
        ...     validation_config={
        ...         "市場拡大": {
        ...             "新規参入": {...}
        ...         }
        ...     }
        ... )
    """

    validation_config: dict[str, Any] = Field(..., description="validation設定の全体")


class AnalysisDummyDataResponse(BaseModel):
    """ダミーデータレスポンススキーマ。

    ダミーデータを返す際に使用します。

    Attributes:
        formula (list[dict[str, str]]): ダミー数式
        input (list[str]): ダミー入力データ（CSV文字列のリスト）
        chart (list[str]): ダミーチャート（Plotly JSONのリスト）
        hint (str): ヒント文章

    Example:
        >>> dummy = AnalysisDummyDataResponse(
        ...     formula=[{"name": "売上合計", "value": "1000"}],
        ...     input=["地域,売上\\n東京,1000"],
        ...     chart=["{}"],
        ...     hint="このデータは..."
        ... )
    """

    formula: list[dict[str, str]] = Field(default_factory=list, description="ダミー数式")
    input: list[str] = Field(default_factory=list, description="ダミー入力データ（CSV文字列）")
    chart: list[str] = Field(default_factory=list, description="ダミーチャート（Plotly JSON）")
    hint: str = Field(default="", description="ヒント文章")
