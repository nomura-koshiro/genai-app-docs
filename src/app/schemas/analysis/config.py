"""分析ステップ設定のPydanticスキーマ。

このモジュールは、各分析ステップ（Filter、Aggregate、Transform）の
設定（config）フィールドに使用するスキーマを定義します。

主なスキーマ:
    Filter設定:
        - NumericFilterConfig: 数値フィルタ設定
        - CategoryFilterConfig: カテゴリフィルタ設定
        - TableFilterConfig: テーブルフィルタ設定
        - FilterConfig: 統合フィルタ設定

    Aggregate設定:
        - AggregationFunction: 集計関数設定
        - SortConfig: ソート設定
        - AggregateConfig: 集計設定

    Transform設定:
        - TransformConfig: 変換設定

使用方法:
    >>> from app.schemas.analysis.config import FilterConfig, NumericFilterConfig
    >>>
    >>> # フィルタ設定
    >>> filter_config = FilterConfig(
    ...     category_filter={"地域": ["東京", "大阪"]},
    ...     numeric_filter=NumericFilterConfig(
    ...         column="売上",
    ...         filter_type="range",
    ...         enable_min=True,
    ...         min_value=1000,
    ...         include_min=True
    ...     )
    ... )
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ================================================================================
# Filter設定スキーマ
# ================================================================================


class NumericFilterConfig(BaseModel):
    """数値フィルタ設定スキーマ。

    数値カラムに対するフィルタリング設定を定義します。

    Attributes:
        column (str): 対象カラム名
        filter_type (Literal["range", "topk", "percentage"]): フィルタタイプ
        enable_min (bool): 最小値フィルタを有効化
        min_value (float | None): 最小値
        include_min (bool): 最小値を含むか
        enable_max (bool): 最大値フィルタを有効化
        max_value (float | None): 最大値
        include_max (bool): 最大値を含むか
        k_value (int | None): topkフィルタのk値
        ascending (bool): topkフィルタの昇順/降順
        min_percentile (float): パーセンタイルフィルタの最小値（0-100）
        max_percentile (float): パーセンタイルフィルタの最大値（0-100）

    Example:
        >>> numeric_filter = NumericFilterConfig(
        ...     column="売上",
        ...     filter_type="range",
        ...     enable_min=True,
        ...     min_value=1000,
        ...     include_min=True,
        ...     enable_max=True,
        ...     max_value=5000,
        ...     include_max=False
        ... )
    """

    model_config = ConfigDict(frozen=False)

    column: str = Field(..., description="対象カラム名")
    filter_type: Literal["range", "topk", "percentage"] = Field(..., description="フィルタタイプ")

    # Range フィルタ用
    enable_min: bool = Field(False, description="最小値フィルタを有効化")
    min_value: float | None = Field(default=None, description="最小値")
    include_min: bool = Field(True, description="最小値を含むか")
    enable_max: bool = Field(False, description="最大値フィルタを有効化")
    max_value: float | None = Field(default=None, description="最大値")
    include_max: bool = Field(True, description="最大値を含むか")

    # TopK フィルタ用
    k_value: int | None = Field(default=None, ge=1, description="topkフィルタのk値")
    ascending: bool = Field(False, description="topkフィルタの昇順/降順")

    # Percentage フィルタ用
    min_percentile: float = Field(0.0, ge=0.0, le=100.0, description="最小パーセンタイル")
    max_percentile: float = Field(100.0, ge=0.0, le=100.0, description="最大パーセンタイル")

    @field_validator("min_value", "max_value")
    @classmethod
    def validate_range_values(cls, v: float | None, info) -> float | None:
        """Range値のバリデーション。"""
        if v is not None and info.data.get("filter_type") == "range":
            # enable_min/enable_maxがTrueの場合、値が必須
            if info.field_name == "min_value" and info.data.get("enable_min"):
                if v is None:
                    raise ValueError("enable_minがTrueの場合、min_valueは必須です")
            if info.field_name == "max_value" and info.data.get("enable_max"):
                if v is None:
                    raise ValueError("enable_maxがTrueの場合、max_valueは必須です")
        return v

    @field_validator("k_value")
    @classmethod
    def validate_k_value(cls, v: int | None, info) -> int | None:
        """TopK値のバリデーション。"""
        if info.data.get("filter_type") == "topk" and v is None:
            raise ValueError("topkフィルタの場合、k_valueは必須です")
        return v


# カテゴリフィルタは dict[str, list[str]] の形式
# 例: {"地域": ["東京", "大阪"], "商品": ["A", "B"]}
CategoryFilterConfig = dict[str, list[str]]


class TableFilterConfig(BaseModel):
    """テーブルフィルタ設定スキーマ。

    別のテーブルを参照してフィルタリングする設定を定義します。

    Attributes:
        enable (bool): テーブルフィルタを有効化
        table_df (str | None): 参照するテーブルのステップ識別子（例: "step_0"）
        key_columns (list[str]): キーカラム名のリスト
        exclude_mode (bool): 除外モード（Trueの場合、参照テーブルにないものを抽出）

    Example:
        >>> table_filter = TableFilterConfig(
        ...     enable=True,
        ...     table_df="step_0",
        ...     key_columns=["地域"],
        ...     exclude_mode=False
        ... )
    """

    model_config = ConfigDict(frozen=False)

    enable: bool = Field(False, description="テーブルフィルタを有効化")
    table_df: str | None = Field(default=None, description="参照するテーブルのステップ識別子")
    key_columns: list[str] = Field(default_factory=list, description="キーカラム名のリスト")
    exclude_mode: bool = Field(False, description="除外モード")

    @field_validator("key_columns")
    @classmethod
    def validate_key_columns(cls, v: list[str], info) -> list[str]:
        """key_columnsのバリデーション。"""
        if info.data.get("enable") and not v:
            raise ValueError("enableがTrueの場合、key_columnsは必須です")
        return v

    @field_validator("table_df")
    @classmethod
    def validate_table_df(cls, v: str | None, info) -> str | None:
        """table_dfのバリデーション。"""
        if info.data.get("enable") and not v:
            raise ValueError("enableがTrueの場合、table_dfは必須です")
        return v


class FilterConfig(BaseModel):
    """統合フィルタ設定スキーマ。

    Filter ステップの設定を統合的に管理します。

    Attributes:
        category_filter (CategoryFilterConfig | None): カテゴリフィルタ設定
        numeric_filter (NumericFilterConfig | None): 数値フィルタ設定
        table_filter (TableFilterConfig | None): テーブルフィルタ設定

    Example:
        >>> filter_config = FilterConfig(
        ...     category_filter={"地域": ["東京", "大阪"]},
        ...     numeric_filter=NumericFilterConfig(
        ...         column="売上",
        ...         filter_type="range",
        ...         enable_min=True,
        ...         min_value=1000,
        ...         include_min=True
        ...     ),
        ...     table_filter=TableFilterConfig(enable=False)
        ... )
    """

    model_config = ConfigDict(frozen=False)

    category_filter: CategoryFilterConfig | None = Field(default=None, description="カテゴリフィルタ設定")
    numeric_filter: NumericFilterConfig | None = Field(default=None, description="数値フィルタ設定")
    table_filter: TableFilterConfig | None = Field(default=None, description="テーブルフィルタ設定")


# ================================================================================
# Aggregate設定スキーマ
# ================================================================================


class AggregationColumnConfig(BaseModel):
    """集計カラム設定スキーマ。

    1つの集計カラムの設定を定義します。

    Attributes:
        name (str): 集計結果のカラム名
        subject (str | list[str]): 対象カラム名（または演算用のカラム名リスト）
        method (str): 集計メソッド（sum/mean/count/max/min）または演算子（+/-/*/​/）

    Example:
        >>> # 基本集計
        >>> agg_col = AggregationColumnConfig(
        ...     name="売上合計",
        ...     subject="売上",
        ...     method="sum"
        ... )
        >>>
        >>> # 四則演算
        >>> profit_col = AggregationColumnConfig(
        ...     name="利益",
        ...     subject=["売上合計", "原価合計"],
        ...     method="-"
        ... )
    """

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., description="集計結果のカラム名")
    subject: str | list[str] = Field(..., description="対象カラム名")
    method: str = Field(..., description="集計メソッドまたは演算子")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """メソッドのバリデーション。"""
        valid_methods = ["sum", "mean", "count", "max", "min", "+", "-", "*", "/"]
        if v not in valid_methods:
            raise ValueError(f"methodは{valid_methods}のいずれかである必要があります")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str | list[str], info) -> str | list[str]:
        """subjectのバリデーション。"""
        method = info.data.get("method")
        # 演算子の場合、subjectはlist必須
        if method in ["+", "-", "*", "/"]:
            if not isinstance(v, list):
                raise ValueError("演算子を使用する場合、subjectはlistである必要があります")
            if len(v) < 2:
                raise ValueError("演算子を使用する場合、subjectは2つ以上必要です")
        # 集計メソッドの場合、subjectはstr必須
        else:
            if not isinstance(v, str):
                raise ValueError("集計メソッドを使用する場合、subjectはstrである必要があります")
        return v


class AggregateConfig(BaseModel):
    """集計設定スキーマ。

    Aggregate ステップの設定を定義します。

    Attributes:
        axis (list[str]): グループ化するカラム名のリスト
        column (list[AggregationColumnConfig]): 集計カラム設定のリスト

    Example:
        >>> aggregate_config = AggregateConfig(
        ...     axis=["地域", "商品"],
        ...     column=[
        ...         AggregationColumnConfig(
        ...             name="売上合計",
        ...             subject="売上",
        ...             method="sum"
        ...         ),
        ...         AggregationColumnConfig(
        ...             name="平均単価",
        ...             subject="単価",
        ...             method="mean"
        ...         )
        ...     ]
        ... )
    """

    model_config = ConfigDict(frozen=False)

    axis: list[str] = Field(..., min_length=1, description="グループ化するカラム名のリスト")
    column: list[AggregationColumnConfig] = Field(..., min_length=1, description="集計カラム設定のリスト")


# ================================================================================
# Transform設定スキーマ
# ================================================================================


class TransformCalculation(BaseModel):
    """変換計算設定スキーマ。

    operation内のcalculationフィールドを定義します。

    Attributes:
        type (str): 計算タイプ（constant/copy/formula/mapping）
        constant_value (Any | None): 定数値（type=constantの場合）
        copy_from (str | None): コピー元列名（type=copyの場合）
        formula_type (str | None): 数式タイプ（type=formulaの場合）
        operands (list[str] | None): オペランドリスト（type=formulaの場合）
        mapping_dict (dict[str, Any] | None): マッピング辞書（type=mappingの場合）

    Example:
        >>> # 定数
        >>> calc = TransformCalculation(type="constant", constant_value="2024")
        >>> # コピー
        >>> calc = TransformCalculation(type="copy", copy_from="売上")
        >>> # 数式
        >>> calc = TransformCalculation(
        ...     type="formula",
        ...     formula_type="+",
        ...     operands=["売上", "原価"]
        ... )
    """

    model_config = ConfigDict(frozen=False)

    type: Literal["constant", "copy", "formula", "mapping"] = Field(..., description="計算タイプ")

    # 各タイプ専用フィールド
    constant_value: Any | None = Field(default=None, description="定数値（type=constantの場合）")
    copy_from: str | None = Field(default=None, description="コピー元列名（type=copyの場合）")
    formula_type: str | None = Field(default=None, description="数式タイプ（type=formulaの場合）")
    operands: list[str] | None = Field(default=None, description="オペランドリスト（type=formulaの場合）")
    mapping_dict: dict[str, Any] | None = Field(default=None, description="マッピング辞書（type=mappingの場合）")
    source_column: str | None = Field(default=None, description="マッピング元列名（type=mappingの場合）")


class TransformOperation(BaseModel):
    """変換操作設定スキーマ。

    1つの変換操作を定義します。

    Attributes:
        operation_type (str): 操作タイプ（add_axis/modify_axis/add_subject/modify_subject）
        target_name (str): 対象列名
        calculation (TransformCalculation): 計算設定

    Example:
        >>> operation = TransformOperation(
        ...     operation_type="add_axis",
        ...     target_name="年度",
        ...     calculation=TransformCalculation(type="constant", constant_value="2024")
        ... )
    """

    model_config = ConfigDict(frozen=False)

    operation_type: Literal["add_axis", "modify_axis", "add_subject", "modify_subject"] = Field(..., description="操作タイプ")
    target_name: str = Field(..., description="対象列名")
    calculation: TransformCalculation = Field(..., description="計算設定")


class TransformConfig(BaseModel):
    """変換設定スキーマ。

    Transform ステップの設定を定義します。

    Attributes:
        operations (list[TransformOperation]): 変換操作のリスト

    Example:
        >>> transform_config = TransformConfig(
        ...     operations=[
        ...         TransformOperation(
        ...             operation_type="add_axis",
        ...             target_name="年度",
        ...             calculation=TransformCalculation(
        ...                 type="constant",
        ...                 constant_value="2024"
        ...             )
        ...         )
        ...     ]
        ... )
    """

    model_config = ConfigDict(frozen=False)

    operations: list[TransformOperation] = Field(..., min_length=1, description="変換操作のリスト")


# ================================================================================
# Agent/State設定スキーマ
# ================================================================================


class UploadFileData(BaseModel):
    """アップロードファイルデータスキーマ。

    data_manager.upload_data()で使用されるファイル情報を定義します。

    Attributes:
        id (str): 一意なファイルID（UUID文字列）
        file_name (str): ファイル名（例: "sales.csv"）
        table_name (str): テーブル名（例: "売上データ"）
        table_axis (list[str]): 軸候補のリスト（例: ["地域", "商品"]）
        data (Any): DataFrameオブジェクト（Pydantic非対応のためAny）

    Example:
        >>> upload_data = UploadFileData(
        ...     id=str(uuid.uuid4()),
        ...     file_name="sales.csv",
        ...     table_name="売上データ",
        ...     table_axis=["地域", "商品"],
        ...     data=df
        ... )
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    id: str = Field(..., description="一意なファイルID（UUID文字列）")
    file_name: str = Field(..., description="ファイル名")
    table_name: str = Field(..., description="テーブル名")
    table_axis: list[str] = Field(..., description="軸候補のリスト")
    data: Any = Field(..., description="DataFrameオブジェクト")  # pd.DataFrameはPydanticで直接サポート外


class ToolUsage(BaseModel):
    """ツール使用履歴スキーマ。

    ToolCallbackHandlerで使用されるツール使用情報を定義します。

    Attributes:
        tool (str): ツール名
        input (str): ツールへの入力
        output (str | None): ツールからの出力（実行前はNone）

    Example:
        >>> tool_usage = ToolUsage(
        ...     tool="GetDataOverviewTool",
        ...     input="",
        ...     output=None
        ... )
    """

    model_config = ConfigDict(frozen=False)

    tool: str = Field(..., description="ツール名")
    input: str = Field(..., description="ツールへの入力")
    output: str | None = Field(default=None, description="ツールからの出力")


class FormulaItemConfig(BaseModel):
    """数式計算設定スキーマ。

    Summary ステップの formula リストの各要素を定義します。

    Attributes:
        target_subject (str | list[str]): 対象科目名（単一または複数）
        type (str): 数式タイプ（sum/mean/count/max/min/+/-/*//）
        formula_text (str): 数式テキスト（表示用）
        unit (str | None): 単位（例: "円"、"個"）

    Example:
        >>> # 集計関数
        >>> formula = FormulaItemConfig(
        ...     target_subject="売上",
        ...     type="sum",
        ...     formula_text="売上合計",
        ...     unit="円"
        ... )
        >>> # 四則演算
        >>> formula = FormulaItemConfig(
        ...     target_subject=["売上合計", "100"],
        ...     type="/",
        ...     formula_text="売上（百円）",
        ...     unit="百円"
        ... )
    """

    model_config = ConfigDict(frozen=False)

    target_subject: str | list[str] = Field(..., description="対象科目名（単一または複数）")
    type: Literal["sum", "mean", "count", "max", "min", "+", "-", "*", "/", "arithmetic"] = Field(..., description="数式タイプ")
    formula_text: str = Field(..., description="数式テキスト（表示用）")
    unit: str | None = Field(default=None, description="単位")
    portion: float = Field(1.0, description="重み係数")


class SummaryConfig(BaseModel):
    """サマリー設定スキーマ。

    Summary ステップの設定を定義します。

    Attributes:
        formula (list[FormulaItemConfig] | None): 計算式リスト
        chart (dict[str, Any] | None): グラフ設定（graph_typeなど）

    Example:
        >>> config = SummaryConfig(
        ...     formula=[
        ...         FormulaItemConfig(
        ...             target_subject="売上",
        ...             type="sum",
        ...             formula_text="売上合計",
        ...             unit="円"
        ...         )
        ...     ],
        ...     chart={"graph_type": "bar", "x_axis": "地域", "y_axis": "売上"}
        ... )
    """

    model_config = ConfigDict(frozen=False)

    formula: list[FormulaItemConfig] | None = Field(default=None, description="計算式リスト")
    chart: dict[str, Any] | None = Field(default=None, description="グラフ設定")


# ================================================================================
# Validation設定スキーマ
# ================================================================================


class ValidationConfig(BaseModel):
    """分析セッションのバリデーション設定スキーマ。

    分析セッションで使用する施策と課題の設定を定義します。

    Attributes:
        policy (str): 施策名（例: "市場拡大"、"不採算製品の撤退"）
        issue (str): 課題名（例: "新規参入"、"利益改善効果"）

    Example:
        >>> config = ValidationConfig(
        ...     policy="市場拡大",
        ...     issue="新規参入"
        ... )
    """

    model_config = ConfigDict(frozen=True)

    policy: str = Field(..., description="施策名", min_length=1)
    issue: str = Field(..., description="課題名", min_length=1)
