import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# 施策スキーマ
# ================================================================================
class AnalysisValidationBase(BaseCamelCaseModel):
    """分析施策ベーススキーマ。

    施策の基本情報を定義します。

    Attributes:
        name (str): 施策名
        validation_order (int): 表示順序

    Example:
        >>> validation = AnalysisValidationBase(
        ...     name="市場拡大",
        ...     validation_order=1
        ... )
    """

    name: str = Field(..., max_length=200, description="施策名")
    validation_order: int = Field(..., description="表示順序")


class AnalysisValidationCreate(AnalysisValidationBase):
    """分析施策作成スキーマ。

    新規施策作成時の入力データを定義します。

    Example:
        >>> validation_create = AnalysisValidationCreate(
        ...     name="市場拡大",
        ...     validation_order=1
        ... )
    """

    pass


class AnalysisValidationUpdate(BaseCamelCaseModel):
    """分析施策更新スキーマ。

    施策更新時の入力データを定義します。

    Attributes:
        name (str | None): 施策名
        validation_order (int | None): 表示順序

    Example:
        >>> validation_update = AnalysisValidationUpdate(
        ...     name="市場拡大",
        ...     validation_order=1
        ... )
    """

    name: str | None = Field(default=None, max_length=200, description="施策名")
    validation_order: int | None = Field(default=None, description="表示順序")


class AnalysisValidationResponse(BaseCamelCaseORMModel):
    """分析施策レスポンススキーマ。

    施策情報の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): 施策ID
        name (str): 施策名
        validation_order (int): 表示順序
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "name": "市場拡大",
        ...     "validation_order": 1,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="施策ID")
    name: str = Field(..., max_length=200, description="施策名")
    validation_order: int = Field(..., description="表示順序")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# グラフ軸設定スキーマ
# ================================================================================
class AnalysisGraphAxisBase(BaseCamelCaseModel):
    """グラフ軸設定ベーススキーマ。

    UIで表示する軸の設定を定義します。

    Attributes:
        name (str): 軸名(例: "横軸", "色分け")
        option (str): '科目'または'軸'のいずれか
        multiple (bool): 複数選択可能か
        axis_order (int): 軸の表示順序

    Example:
        >>> axis = AnalysisGraphAxisBase(
        ...     name="横軸",
        ...     option="科目",
        ...     multiple=False,
        ...     axis_order=1
        ... )
    """

    name: str = Field(..., max_length=200, description="軸名、例: '横軸', '色分け'")
    option: str = Field(..., max_length=50, description="'科目'または'軸'のいずれか")
    multiple: bool = Field(default=False, description="複数選択可能か")
    axis_order: int = Field(..., description="軸の表示順序")


class AnalysisGraphAxisCreate(AnalysisGraphAxisBase):
    """グラフ軸設定作成スキーマ。

    新規軸設定追加用に必要な情報を定義します。

    Attributes:
        issue_id (uuid.UUID): 所属する課題ID

    Example:
        >>> axis_create = AnalysisGraphAxisCreate(
        ...     issue_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     name="横軸",
        ...     option="科目",
        ...     multiple=False,
        ...     axis_order=1
        ... )
    """

    issue_id: uuid.UUID = Field(..., description="課題ID")


class AnalysisGraphAxisUpdate(BaseCamelCaseModel):
    """グラフ軸設定更新スキーマ。

    軸設定更新用に必要な情報を定義します。

    Attributes:
        name (str | None): 軸名(例: "横軸", "色分け")
        option (str | None): '科目'または'軸'のいずれか
        multiple (bool | None): 複数選択可能か
        axis_order (int | None): 軸の表示順序
    Example:
        >>> axis_update = AnalysisGraphAxisUpdate(
        ...     name="横軸",
        ...     option="科目",
        ...     multiple=False,
        ...     axis_order=1
        ... )
    """

    name: str | None = Field(default=None, max_length=200, description="軸名、例: '横軸', '色分け'")
    option: str | None = Field(default=None, max_length=50, description="'科目'または'軸'のいずれか")
    multiple: bool | None = Field(default=None, description="複数選択可能か")
    axis_order: int | None = Field(default=None, description="軸の表示順序")


class AnalysisGraphAxisResponse(BaseCamelCaseORMModel):
    """グラフ軸設定レスポンススキーマ。

    軸設定の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): 軸設定ID
        name (str): 軸名
        option (str): '科目'または'軸'のいずれか
        multiple (bool): 複数選択可能か
        axis_order (int): 軸の表示順序
        issue_id (uuid.UUID): 所属する課題ID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "issue_id": "223e4567-e89b-12d3-a456-426614174000",
        ...     "name": "横軸",
        ...     "option": "科目",
        ...     "multiple": false,
        ...     "axis_order": 1,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="軸設定ID")
    name: str = Field(..., max_length=200, description="軸名、例: '横軸', '色分け'")
    option: str = Field(..., max_length=50, description="'科目'または'軸'のいずれか")
    multiple: bool = Field(default=False, description="複数選択可能か")
    axis_order: int = Field(..., description="軸の表示順序")
    issue_id: uuid.UUID = Field(..., description="課題ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# ダミー計算式スキーマ
# ================================================================================
class AnalysisDummyFormulaBase(BaseCamelCaseModel):
    """ダミー計算式ベーススキーマ。

    ダミー出力計算式の名前と値を定義します。

    Attributes:
        name (str): 計算式名(例: "平均売上")
        value (str): 計算結果と単位を含む文字列(例: "5000円")
        formula_order (int): 計算式の表示順序

    Example:
        >>> formula = AnalysisDummyFormulaBase(
        ...     name="平均売上",
        ...     value="5000円",
        ...     formula_order=1
        ... )
    """

    name: str = Field(..., description="計算式名、例: '平均売上'")
    value: str = Field(..., description="計算結果と単位を含む文字列、例: '5000円'")
    formula_order: int = Field(..., description="計算式の表示順序")


class AnalysisDummyFormulaCreate(AnalysisDummyFormulaBase):
    """ダミー計算式作成スキーマ。

    新規計算式追加用に必要な情報を定義します。

    Attributes:
        issue_id (uuid.UUID): 所属する課題ID

    Example:
        >>> formula_create = AnalysisDummyFormulaCreate(
        ...     issue_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     name="平均売上",
        ...     value="5000円",
        ...     formula_order=1
        ... )
    """

    issue_id: uuid.UUID = Field(..., description="課題ID")


class AnalysisDummyFormulaUpdate(BaseCamelCaseModel):
    """ダミー計算式更新スキーマ。

    計算式更新用に必要な情報を定義します。

    Attributes:
        name (str | None): 計算式名(例: "平均売上")
        value (str | None): 計算結果と単位を含む文字列(例: "5000円")
        formula_order (int | None): 計算式の表示順序
    Example:
        >>> formula_update = AnalysisDummyFormulaUpdate(
        ...     name="平均売上",
        ...     value="5000円",
        ...     formula_order=1
        ... )
    """

    name: str | None = Field(default=None, description="計算式名、例: '平均売上'")
    value: str | None = Field(default=None, description="計算結果と単位を含む文字列、例: '5000円'")
    formula_order: int | None = Field(default=None, description="計算式の表示順序")


class AnalysisDummyFormulaResponse(BaseCamelCaseORMModel):
    """ダミー計算式レスポンススキーマ。

    計算式情報の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): 計算式ID
        name (str): 計算式名
        value (str): 計算結果と単位を含む文字列
        formula_order (int): 計算式の表示順序
        issue_id (uuid.UUID): 所属する課題ID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "issue_id": "223e4567-e89b-12d3-a456-426614174000",
        ...     "name": "平均売上",
        ...     "value": "5000円",
        ...     "formula_order": 1,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="計算式ID")
    name: str = Field(..., description="計算式名、例: '平均売上'")
    value: str = Field(..., description="計算結果と単位を含む文字列、例: '5000円'")
    formula_order: int = Field(..., description="計算式の表示順序")
    issue_id: uuid.UUID = Field(..., description="課題ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# ================================================================================
# ダミーチャートスキーマ
# ================================================================================
class AnalysisDummyChartBase(BaseCamelCaseModel):
    """ダミーチャートベーススキーマ。

    Plotly チャートデータを blob として保存します。

    Attributes:
        chart (dict): チャートデータ(Plotly JSON)
        chart_order (int): チャートの表示順序

    Example:
        >>> chart = AnalysisDummyChartBase(
        ...     chart={"data": [...], "layout": {...}},
        ...     chart_order=1
        ... )
    """

    chart: dict = Field(..., description="チャートデータ(Plotly JSON)")
    chart_order: int = Field(..., description="チャートの表示順序")


class AnalysisDummyChartCreate(AnalysisDummyChartBase):
    """ダミーチャート作成スキーマ。

    新規チャート追加用に必要な情報を定義します。

    Attributes:
        issue_id (uuid.UUID): 所属する課題ID

    Example:
        >>> chart_create = AnalysisDummyChartCreate(
        ...     issue_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     chart=b'{"data": [...]}',
        ...     chart_order=1
        ... )
    """

    issue_id: uuid.UUID = Field(..., description="課題ID")


class AnalysisDummyChartUpdate(BaseCamelCaseModel):
    """ダミーチャート更新スキーマ。

    チャート更新用に必要な情報を定義します。

    Attributes:
        chart (dict | None): チャートデータ(Plotly JSON)
        chart_order (int | None): チャートの表示順序
    Example:
        >>> chart_update = AnalysisDummyChartUpdate(
        ...     chart=b'{"data": [...]}',
        ...     chart_order=1
        ... )
    """

    chart: dict | None = Field(default=None, description="チャートデータ(Plotly JSON)")
    chart_order: int | None = Field(default=None, description="チャートの表示順序")


class AnalysisDummyChartResponse(BaseCamelCaseORMModel):
    """ダミーチャートレスポンススキーマ。

    チャート情報の API レスポンスを定義します。

    Attributes:
        id (uuid.UUID): チャートID
        chart (dict): チャートデータ(Plotly JSON)
        chart_order (int): チャートの表示順序
        issue_id (uuid.UUID): 所属する課題ID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "issue_id": "223e4567-e89b-12d3-a456-426614174000",
        ...     "chart": "eyJkYXRhIjogWy4uLl19",  // Base64エンコード
        ...     "chart_order": 1,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="チャートID")
    chart: dict = Field(..., description="チャートデータ(Plotly JSON)")
    chart_order: int = Field(..., description="チャートの表示順序")
    issue_id: uuid.UUID = Field(..., description="課題ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    @field_validator("chart", mode="before")
    @classmethod
    def parse_chart_bytes(cls, v: Any) -> dict:
        """bytesをdictに変換します。"""
        if isinstance(v, bytes):
            return json.loads(v.decode("utf-8"))
        if isinstance(v, str):
            return json.loads(v)
        return v


# ================================================================================
# 分析課題スキーマ
# ================================================================================
class AnalysisIssueBase(BaseCamelCaseModel):
    """ベース分析課題スキーマ。

    課題の基本情報を定義します。

    Attributes:
        name (str): 課題名
        description (str | None): 課題説明
        agent_prompt (str | None): AIエージェント用プロンプト
        initial_msg (str | None): 初期メッセージ
        dummy_input (list[dict] | None): ダミー入力データ(pandas.to_dict, orient='records')形式
        dummy_hint (str | None): ダミーヒント
        issue_order (int): 表示順序

    Example:
        >>> issue = AnalysisIssueBase(
        ...     name="新規参入",
        ...     description="新規市場への参入効果を分析します",
        ...     agent_prompt="...",
        ...     initial_msg="分析を開始します",
        ...     dummy_input=[{"店舗名": "A店", "売上": 1000, "地域": "東京"}],
        ...     dummy_hint="年度ごとの売上データを入力してください。",
        ...     issue_order=1
        ... )
    """

    name: str = Field(..., max_length=255, description="課題名")
    description: str | None = Field(default=None, description="課題の説明")
    agent_prompt: str | None = Field(default=None, description="AIエージェント用のプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    dummy_input: list[dict] | None = Field(default=None, description="ダミー入力データ(pandas.to_dict, orient='records')形式")
    dummy_hint: str | None = Field(default=None, description="ダミー入力ヒント")
    issue_order: int = Field(default=0, description="表示順序")


class AnalysisIssueCreate(AnalysisIssueBase):
    """分析課題作成スキーマ。

    新規課題作成用に必要な情報を定義します。

    Attributes:
        validation_id (uuid.UUID): 親の施策ID
        name (str): 課題名
        description (str | None): 課題説明
        agent_prompt (str | None): AIエージェント用プロンプト
        initial_msg (str | None): 初期メッセージ
        dummy_input (list[dict] | None): ダミー入力データ(pandas.to_dict, orient='records')形式
        dummy_hint (str | None): ダミーヒント
        issue_order (int): 表示順序

    Example:
        >>> issue_create = AnalysisIssueCreate(
        ...     validation_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     name="新規参入",
        ...     description="新規市場への参入効果を分析します",
        ...     agent_prompt="...",
        ...     initial_msg="分析を開始します",
        ...     dummy_input=[{"店舗名": "A店", "売上": 1000, "地域": "東京"}],
        ...     dummy_hint="年度ごとの売上データを入力してください。",
        ...     issue_order=1
        ... )
    """

    validation_id: uuid.UUID = Field(..., description="施策ID")


class AnalysisIssueUpdate(BaseCamelCaseModel):
    """分析課題更新スキーマ。

    課題更新用に必要な情報を定義します。

    Attributes:
        name (str | None): 課題名
        description (str | None): 課題説明
        agent_prompt (str | None): AIエージェント用プロンプト
        initial_msg (str | None): 初期メッセージ
        dummy_input (list | None): ダミー入力データ(pandas.to_dict, orient='records')形式
        dummy_hint (str | None): ダミーヒント
        issue_order (int | None): 表示順序
    Example:
        >>> issue_update = AnalysisIssueUpdate(
        ...     name="新規参入",
        ...     description="新規市場への参入効果を分析します",
        ...     agent_prompt="...",
        ...     initial_msg="分析を開始します",
        ...     dummy_input=[{"店舗名": "A店", "売上": 1000, "地域": "東京"}],
        ...     dummy_hint="年度ごとの売上データを入力してください。",
        ...     issue_order=1
        ... )
    """

    name: str | None = Field(default=None, max_length=255, description="課題名")
    description: str | None = Field(default=None, description="課題の説明")
    agent_prompt: str | None = Field(default=None, description="AIエージェント用のプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    dummy_input: list[dict] | None = Field(default=None, description="ダミー入力データ(バイナリ)")
    dummy_hint: str | None = Field(default=None, description="ダミー入力ヒント")
    issue_order: int | None = Field(default=None, description="表示順序")


class AnalysisIssueCatalogResponse(BaseCamelCaseORMModel):
    """課題カタログレスポンススキーマ。

    一覧表示用、基本情報のみ(詳細・ダミーデータ含まず)。

    Attributes:
        id (uuid.UUID): 課題ID
        validation_id (uuid.UUID): 施策ID
        validation (str): 施策名(結合データ)
        validation_order (int): 施策表示順序(結合データ)
        name (str): 課題名
        issue_order (int): 表示順序
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "validation_id": "223e4567-e89b-12d3-a456-426614174000",
        ...     "validation": "市場拡大",
        ...     "validation_order": 1,
        ...     "name": "新規参入",
        ...     "issue_order": 1,
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    validation_id: uuid.UUID = Field(..., description="施策ID")
    validation: str = Field(..., description="施策名(結合データ)")
    validation_order: int = Field(..., description="施策表示順序(結合データ)")
    id: uuid.UUID = Field(..., description="課題ID")
    name: str = Field(..., description="課題名")
    issue_order: int = Field(..., description="表示順序")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnalysisIssueCatalogListResponse(BaseCamelCaseModel):
    """課題カタログ一覧レスポンススキーマ。

    課題カタログ一覧APIのレスポンス形式を定義します。

    Attributes:
        issues (list[AnalysisIssueCatalogResponse]): 課題カタログリスト
        total (int): 総件数

    Example:
        >>> response = AnalysisIssueCatalogListResponse(
        ...     issues=[issue1, issue2, issue3],
        ...     total=3
        ... )
    """

    issues: list[AnalysisIssueCatalogResponse] = Field(..., description="課題カタログリスト")
    total: int = Field(..., description="総件数")


class AnalysisIssueDetailResponse(BaseCamelCaseORMModel):
    """課題詳細情報レスポンススキーマ。

    詳細情報、初期軸設定、ダミーデータを含む。

    Attributes:
        id (uuid.UUID): 課題ID
        name (str): 課題名
        description (str | None): 課題説明
        agent_prompt (str | None): AIエージェント用プロンプト
        initial_msg (str | None): 初期メッセージ
        dummy_input (list[dict] | None): ダミー入力データ
        dummy_hint (str | None): ダミーヒント
        issue_order (int): 表示順序
        validation_id (uuid.UUID): 施策ID
        validation (str): 施策名(結合データ)
        validation_order (int): 施策表示順序(結合データ)
        initial_axis (list[AnalysisGraphAxisResponse]): 初期軸設定(結合データ)
        dummy_formula (list[AnalysisDummyFormulaResponse]): ダミー計算式(結合データ)
        dummy_chart (list[AnalysisDummyChartResponse]): ダミーチャート(結合データ)
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "validation_id": "223e4567-e89b-12d3-a456-426614174000",
        ...     "validation": "市場拡大",
        ...     "validation_order": 1,
        ...     "name": "新規参入",
        ...     "description": "新規市場への参入効果を分析します",
        ...     "agent_prompt": "あなたは優秀なデータ分析アシスタントです。...",
        ...     "initial_msg": "分析を開始します",
        ...     "dummy_input": [{"店舗名": "A店", "売上": 1000, "地域": "東京"}],
        ...     "dummy_hint": "年度ごとの売上データを入力してください。",
        ...     "issue_order": 1,
        ...     "initial_axis": [{name: "...", option: "...", multiple: false}, ...],
        ...     "dummy_formula": [{name: "...", value: "...", formula_order: 0}, ...],
        ...     "dummy_chart": ["plotly instance json", ...],
        ...     "created_at": "2025-01-01T00:00:00Z",
        ...     "updated_at": "2025-01-01T00:00:00Z"
        ... }
    """

    id: uuid.UUID = Field(..., description="課題ID")
    name: str = Field(..., max_length=255, description="課題名")
    description: str | None = Field(default=None, description="課題の説明")
    agent_prompt: str | None = Field(default=None, description="AIエージェント用のプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    dummy_input: list[dict] | None = Field(default=None, description="ダミー入力データ(pandas.to_dict, orient='records')形式")
    dummy_hint: str | None = Field(default=None, description="ダミー入力ヒント")
    issue_order: int = Field(default=0, description="表示順序")
    validation_id: uuid.UUID = Field(..., description="施策ID")
    validation: str = Field(..., description="施策名(結合データ)")
    validation_order: int = Field(..., description="施策表示順序(結合データ)")
    initial_axis: list[AnalysisGraphAxisResponse] = Field(default_factory=list, description="初期軸設定(結合データ)")
    dummy_formula: list[AnalysisDummyFormulaResponse] = Field(default_factory=list, description="ダミー計算式(結合データ)")
    dummy_chart: list[AnalysisDummyChartResponse] = Field(default_factory=list, description="ダミーチャート(結合データ)")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
