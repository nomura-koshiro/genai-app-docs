"""分析テンプレート管理のPydanticスキーマ。

このモジュールは、分析テンプレートとチャートデータの
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    テンプレート:
        - AnalysisTemplateBase: 基本テンプレート情報
        - AnalysisTemplateCreate: テンプレート作成リクエスト
        - AnalysisTemplateUpdate: テンプレート更新リクエスト
        - AnalysisTemplateResponse: テンプレート情報レスポンス
        - AnalysisTemplateDetailResponse: チャートデータを含む詳細レスポンス

    チャート:
        - AnalysisTemplateChartBase: 基本チャート情報
        - AnalysisTemplateChartCreate: チャート作成リクエスト
        - AnalysisTemplateChartResponse: チャート情報レスポンス

    初期軸設定:
        - AnalysisInitialAxisConfig: UI初期軸設定
        - AnalysisInitialAxisList: 初期軸設定のリスト

使用方法:
    >>> from app.schemas.analysis.template import AnalysisTemplateCreate
    >>>
    >>> # テンプレート作成
    >>> template = AnalysisTemplateCreate(
    ...     policy="市場拡大",
    ...     issue="新規参入",
    ...     description="新規市場への参入効果を分析します",
    ...     agent_prompt="...",
    ...     initial_msg="分析を開始します",
    ...     initial_axis=[{"name": "横軸", "option": "科目", "multiple": False}]
    ... )
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ================================================================================
# 初期軸設定スキーマ
# ================================================================================


class AnalysisInitialAxisConfig(BaseModel):
    """初期軸設定スキーマ。

    UIで表示する軸の初期設定を定義します。

    Attributes:
        name (str): 軸名（例: "横軸", "色分け"）
        option (str): 初期選択カラム名
        multiple (bool): 複数選択可能か

    Example:
        >>> axis_config = AnalysisInitialAxisConfig(
        ...     name="横軸",
        ...     option="科目",
        ...     multiple=False
        ... )
    """

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., description="軸名")
    option: str = Field(..., description="初期選択カラム名")
    multiple: bool = Field(False, description="複数選択可能か")


# 初期軸設定の型定義
AnalysisInitialAxisList = list[AnalysisInitialAxisConfig]


# ================================================================================
# Plotlyチャートデータスキーマ
# ================================================================================


class AnalysisPlotlyChartData(BaseModel):
    """Plotlyチャートデータの基本構造スキーマ。

    Plotly形式のチャートデータ（data, layout, config）を定義します。
    Plotlyの完全な型定義は複雑すぎるため、最低限の構造検証のみ行います。

    Attributes:
        data (list[dict[str, Any]]): チャート系列データ（必須）
        layout (dict[str, Any] | None): レイアウト設定（タイトル、軸設定など）
        config (dict[str, Any] | None): チャート設定（ツールバー表示など）

    Example:
        >>> chart = AnalysisPlotlyChartData(
        ...     data=[
        ...         {
        ...             "type": "bar",
        ...             "x": ["A", "B", "C"],
        ...             "y": [1, 2, 3],
        ...             "name": "売上"
        ...         }
        ...     ],
        ...     layout={
        ...         "title": "売上推移",
        ...         "xaxis": {"title": "カテゴリ"},
        ...         "yaxis": {"title": "金額"}
        ...     }
        ... )

    Note:
        - `extra='allow'`により、Plotlyの拡張フィールドも許可
        - 最低限 `data` フィールドが必須で、空でないことを保証
    """

    model_config = ConfigDict(extra="allow", frozen=False)

    data: list[dict[str, Any]] = Field(..., description="チャート系列データ", min_length=1)
    layout: dict[str, Any] | None = Field(default=None, description="レイアウト設定")
    config: dict[str, Any] | None = Field(default=None, description="チャート設定")


# ================================================================================
# 分析テンプレートチャートスキーマ
# ================================================================================


class AnalysisTemplateChartBase(BaseModel):
    """ベース分析テンプレートチャートスキーマ。

    チャートの基本情報を定義します。

    Attributes:
        chart_name (str): チャート名
        chart_data (dict[str, Any]): Plotlyチャートデータ
        chart_order (int): 表示順序
        chart_type (str | None): チャートタイプ
    """

    chart_name: str = Field(..., max_length=500, description="チャート名（ファイル名由来）")
    chart_data: dict[str, Any] = Field(..., description="Plotly形式のチャートデータ")
    chart_order: int = Field(default=0, description="チャート表示順序")
    chart_type: str | None = Field(default=None, max_length=50, description="チャートタイプ（bar, line, pie等）")


class AnalysisTemplateChartCreate(AnalysisTemplateChartBase):
    """チャート作成リクエストスキーマ。

    新規チャート作成時に必要な情報を定義します。

    Attributes:
        template_id (uuid.UUID): 所属するテンプレートID

    Example:
        >>> chart = AnalysisTemplateChartCreate(
        ...     template_id=uuid.uuid4(),
        ...     chart_name="利益改善効果グラフ",
        ...     chart_data={"data": [...], "layout": {...}},
        ...     chart_type="scatter"
        ... )
    """

    template_id: uuid.UUID = Field(..., description="テンプレートID")


class AnalysisTemplateChartResponse(AnalysisTemplateChartBase):
    """チャート情報レスポンススキーマ。

    チャート情報のAPI応答形式を定義します。

    Attributes:
        id (uuid.UUID): チャートID
        template_id (uuid.UUID): 所属するテンプレートID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "template_id": "223e4567-e89b-12d3-a456-426614174000",
        ...     "chart_name": "利益改善効果グラフ",
        ...     "chart_data": {"data": [...], "layout": {...}},
        ...     "chart_order": 0,
        ...     "chart_type": "scatter",
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="チャートID")
    template_id: uuid.UUID = Field(..., description="テンプレートID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# 分析テンプレートスキーマ
# ================================================================================


class AnalysisTemplateBase(BaseModel):
    """ベース分析テンプレートスキーマ。

    テンプレートの基本情報を定義します。

    Attributes:
        policy (str): 施策名
        issue (str): 課題名
        description (str): テンプレート説明
        agent_prompt (str): AIエージェント用プロンプト
        initial_msg (str): 初期メッセージ
        initial_axis (list[dict[str, Any]]): 初期軸設定
        dummy_formula (list[dict[str, Any]] | None): ダミー計算式
        dummy_input (list[str] | None): ダミー入力データ
        dummy_hint (str | None): ダミーヒント
        is_active (bool): アクティブフラグ
        display_order (int): 表示順序
    """

    policy: str = Field(..., max_length=200, description="施策名")
    issue: str = Field(..., max_length=500, description="課題名")
    description: str = Field(..., description="テンプレートの説明")
    agent_prompt: str = Field(..., description="AIエージェント用のプロンプト")
    initial_msg: str = Field(..., description="初期メッセージ")
    initial_axis: list[dict[str, Any]] = Field(default_factory=list, description="初期軸設定（論理型: InitialAxisList）")
    dummy_formula: list[dict[str, Any]] | None = Field(default=None, description="ダミー計算式")
    dummy_input: list[str] | None = Field(default=None, description="ダミー入力データ")
    dummy_hint: str | None = Field(default=None, description="ダミーヒント")
    is_active: bool = Field(default=True, description="アクティブフラグ")
    display_order: int = Field(default=0, description="表示順序")


class AnalysisTemplateCreate(AnalysisTemplateBase):
    """テンプレート作成リクエストスキーマ。

    新規テンプレート作成時に必要な情報を定義します。

    Example:
        >>> template = AnalysisTemplateCreate(
        ...     policy="市場拡大",
        ...     issue="新規参入",
        ...     description="新規市場への参入効果を分析します",
        ...     agent_prompt="...",
        ...     initial_msg="分析を開始します",
        ...     initial_axis=[
        ...         {"name": "横軸", "option": "科目", "multiple": False}
        ...     ]
        ... )
    """

    pass


class AnalysisTemplateUpdate(BaseModel):
    """テンプレート更新リクエストスキーマ。

    テンプレート情報の部分更新に使用します。
    すべてのフィールドはOptionalです。

    Example:
        >>> update = AnalysisTemplateUpdate(
        ...     description="更新された説明文",
        ...     is_active=False
        ... )
    """

    policy: str | None = Field(default=None, max_length=200, description="施策名")
    issue: str | None = Field(default=None, max_length=500, description="課題名")
    description: str | None = Field(default=None, description="テンプレートの説明")
    agent_prompt: str | None = Field(default=None, description="AIエージェント用のプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    initial_axis: list[dict[str, Any]] | None = Field(default=None, description="初期軸設定（論理型: InitialAxisList）")
    dummy_formula: list[dict[str, Any]] | None = Field(default=None, description="ダミー計算式")
    dummy_input: list[str] | None = Field(default=None, description="ダミー入力データ")
    dummy_hint: str | None = Field(default=None, description="ダミーヒント")
    is_active: bool | None = Field(default=None, description="アクティブフラグ")
    display_order: int | None = Field(default=None, description="表示順序")


class AnalysisTemplateResponse(AnalysisTemplateBase):
    """テンプレート情報レスポンススキーマ。

    テンプレート情報のAPI応答形式を定義します（チャートデータは含まない）。

    Attributes:
        id (uuid.UUID): テンプレートID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "policy": "市場拡大",
        ...     "issue": "新規参入",
        ...     "description": "新規市場への参入効果を分析します",
        ...     "agent_prompt": "...",
        ...     "initial_msg": "分析を開始します",
        ...     "initial_axis": [{"name": "横軸", "option": "科目", "multiple": false}],
        ...     "dummy_formula": null,
        ...     "dummy_input": null,
        ...     "dummy_hint": null,
        ...     "is_active": true,
        ...     "display_order": 0,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="テンプレートID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnalysisTemplateDetailResponse(AnalysisTemplateResponse):
    """テンプレート詳細レスポンススキーマ。

    チャートデータを含むテンプレート詳細情報のAPI応答形式を定義します。

    Attributes:
        charts (list[AnalysisTemplateChartResponse]): 関連するチャートデータのリスト

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "policy": "市場拡大",
        ...     "issue": "新規参入",
        ...     "description": "新規市場への参入効果を分析します",
        ...     "agent_prompt": "...",
        ...     "initial_msg": "分析を開始します",
        ...     "initial_axis": [...],
        ...     "dummy_formula": [...],
        ...     "dummy_input": [...],
        ...     "dummy_hint": "...",
        ...     "is_active": true,
        ...     "display_order": 0,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z",
        ...     "charts": [
        ...         {
        ...             "id": "223e4567-e89b-12d3-a456-426614174000",
        ...             "template_id": "123e4567-e89b-12d3-a456-426614174000",
        ...             "chart_name": "利益改善効果グラフ",
        ...             "chart_data": {"data": [...], "layout": {...}},
        ...             "chart_order": 0,
        ...             "chart_type": "scatter",
        ...             "created_at": "2025-01-01T00:00:00Z",
        ...             "updated_at": "2025-01-01T00:00:00Z"
        ...         }
        ...     ]
        ... }
    """

    charts: list[AnalysisTemplateChartResponse] = Field(
        default_factory=list,
        description="関連するチャートデータのリスト",
    )
