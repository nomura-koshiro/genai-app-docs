import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel
from app.schemas.driver_tree.common import CategoryInfo, DriverTreeInfo, DriverTreeNodeCalculatedData, FormulaInfo


class DriverTreeListItem(BaseCamelCaseModel):
    """ツリー一覧アイテム。

    Attributes:
        tree_id: uuid - ツリーID
        name: str - ツリー名
        description: str - 説明
        status: str - ツリー状態（draft/active/completed）
        formula_master_name: str | None - 数式マスタ名（紐づいている数式テンプレートのドライバー型名）
        node_count: int - ノード数（ツリーに含まれるノード数）
        policy_count: int - 施策数（ツリーに関連する施策数）
        created_at: datetime - 作成日時
        updated_at: datetime - 更新日時

    """

    tree_id: uuid.UUID = Field(..., description="ツリーID")
    name: str = Field(..., description="ツリー名")
    description: str | None = Field(default=None, description="説明")
    status: str = Field(default="draft", description="ツリー状態（draft/active/completed）")
    formula_master_name: str | None = Field(default=None, description="数式マスタ名")
    node_count: int = Field(default=0, description="ノード数")
    policy_count: int = Field(default=0, description="施策数")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


# Request


class DriverTreeCreateTreeRequest(BaseCamelCaseModel):
    """ツリー作成リクエスト。

    Request Body:
        - name: str - ツリー名（必須）
        - description: str - 説明（オプション）
    """

    name: str = Field(..., description="ツリー名")
    description: str | None = Field(default=None, description="説明")


class DriverTreeImportFormulaRequest(BaseCamelCaseModel):
    """数式/データインポート

    Request Body:
        - position_x: int - ルートノードX座標
        - position_y: int - ルートノードY座標
        - formulas: list[str] - 数式リスト
        - sheet_id: uuid - 入力シートID(オプション)
    """

    position_x: int = Field(..., description="ルートノードX座標")
    position_y: int = Field(..., description="ルートノードY座標")
    formulas: list[str] = Field(..., description="数式リスト")
    sheet_id: uuid.UUID | None = Field(default=None, description="入力シートID")


# Response


class DriverTreeCreateTreeResponse(BaseCamelCaseModel):
    """ツリー作成レスポンス。

    Response:
        - tree_id: uuid - ツリーID
        - name: str - ツリー名
        - description: str - 説明
        - status: str - ツリー状態（draft/active/completed）
        - created_at: datetime - 作成日時
    """

    tree_id: uuid.UUID = Field(..., description="ツリーID")
    name: str = Field(..., description="ツリー名")
    description: str | None = Field(default=None, description="説明")
    status: str = Field(default="draft", description="ツリー状態（draft/active/completed）")
    created_at: datetime = Field(..., description="作成日時")


class DriverTreeListResponse(BaseCamelCaseModel):
    """ツリー一覧レスポンス。

    Response:
        - trees: list[dict] - ツリー一覧
    """

    trees: list[DriverTreeListItem] = Field(default_factory=list, description="ツリー一覧")


class DriverTreeGetTreeResponse(BaseCamelCaseModel):
    """ツリー取得レスポンス。

    Response:
        - tree: DriverTreeInfo - ツリー詳細情報
    """

    tree: DriverTreeInfo = Field(..., description="ツリー詳細情報")


class DriverTreeResetResponse(BaseCamelCaseModel):
    """ツリーリセットレスポンス。

    Response:
        - tree: dict - リセット後のツリー全体構造
        - reset_at: datetime - リセット日時
    """

    tree: DriverTreeInfo = Field(..., description="リセット後のツリー全体構造")
    reset_at: datetime = Field(..., description="リセット日時")


class DriverTreeDeleteResponse(BaseCamelCaseModel):
    """ツリー削除レスポンス。

    Response:
        - success: bool - 成功フラグ
        - deleted_at: datetime - 削除日時
    """

    success: bool = Field(..., description="成功フラグ")
    deleted_at: datetime = Field(..., description="削除日時")


class DriverTreeCalculatedDataResponse(BaseCamelCaseModel):
    """計算ノードの計算データ取得レスポンス。
    Response:
        - calculated_data_list: list[DriverTreeNodeCalculatedData] - 計算ノードの計算データ一覧
    """

    calculated_data_list: list[DriverTreeNodeCalculatedData] = Field(..., description="計算ノードの計算データ一覧")


class DriverTreeCategoryListResponse(BaseCamelCaseModel):
    """ドライバーツリーカテゴリ一覧レスポンス。

    Response:
        - categories: list[CategoryInfo] - 業界分類リスト
    """

    categories: list[CategoryInfo] = Field(default_factory=list, description="業界分類リスト")


class DriverTreeFormulaGetResponse(BaseCamelCaseModel):
    """ドライバーツリー数式取得レスポンス。

    Response:
        - formula: FormulaInfo - 数式情報
    """

    formula: FormulaInfo = Field(..., description="数式情報")


class CalculationNodeSummary(BaseCamelCaseModel):
    """計算ノードサマリー。

    Attributes:
        node_id: ノードID
        label: ノード名
        total_value: 合計値
        avg_value: 平均値
        min_value: 最小値
        max_value: 最大値
        record_count: レコード数
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    label: str = Field(..., description="ノード名")
    total_value: float | None = Field(default=None, description="合計値")
    avg_value: float | None = Field(default=None, description="平均値")
    min_value: float | None = Field(default=None, description="最小値")
    max_value: float | None = Field(default=None, description="最大値")
    record_count: int = Field(default=0, description="レコード数")


class PolicyEffectInfo(BaseCamelCaseModel):
    """施策効果情報。

    施策適用前後の値と差分を表します。

    Attributes:
        policy_id: 施策ID
        policy_name: 施策名
        node_id: 対象ノードID
        node_label: 対象ノード名
        original_value: 施策適用前の値
        projected_value: 施策適用後の値
        difference: 差分（projected_value - original_value）
        difference_percent: 差分率（%）
    """

    policy_id: uuid.UUID = Field(..., description="施策ID")
    policy_name: str = Field(..., description="施策名")
    node_id: uuid.UUID = Field(..., description="対象ノードID")
    node_label: str = Field(..., description="対象ノード名")
    original_value: float = Field(..., description="施策適用前の値")
    projected_value: float = Field(..., description="施策適用後の値")
    difference: float = Field(..., description="差分")
    difference_percent: float | None = Field(default=None, description="差分率（%）")


class DriverTreeCalculationSummaryResponse(BaseCamelCaseModel):
    """ドライバーツリー計算結果サマリーレスポンス。

    Response:
        - tree_id: uuid - ツリーID
        - tree_name: str - ツリー名
        - root_summary: CalculationNodeSummary - ルートノードのサマリー
        - node_summaries: list[CalculationNodeSummary] - 各計算ノードのサマリー
        - policy_effects: list[PolicyEffectInfo] - 施策効果一覧
        - total_node_count: int - 総ノード数
        - calculation_node_count: int - 計算ノード数
        - error_node_count: int - エラーノード数
        - calculated_at: datetime - 計算日時
    """

    tree_id: uuid.UUID = Field(..., description="ツリーID")
    tree_name: str = Field(..., description="ツリー名")
    root_summary: CalculationNodeSummary | None = Field(default=None, description="ルートノードのサマリー")
    node_summaries: list[CalculationNodeSummary] = Field(default_factory=list, description="各計算ノードのサマリー")
    policy_effects: list[PolicyEffectInfo] = Field(default_factory=list, description="施策効果一覧")
    total_node_count: int = Field(default=0, description="総ノード数")
    calculation_node_count: int = Field(default=0, description="計算ノード数")
    error_node_count: int = Field(default=0, description="エラーノード数")
    calculated_at: datetime = Field(..., description="計算日時")
