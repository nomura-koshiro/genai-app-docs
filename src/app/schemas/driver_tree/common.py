import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import (
    DriverTreeColumnRoleEnum,
    DriverTreeKpiEnum,
    DriverTreeNodeTypeEnum,
    DriverTreePolicyStatusEnum,
)
from app.schemas.base import BaseCamelCaseModel


class DriverTreeRelationshipInfo(BaseCamelCaseModel):
    """ノード関係情報詳細。

    計算ノードの親子関係を表す情報。

    Attributes:
        parent_id (uuid.UUID): 親ノードID
        operator (str): 演算子（+, -, *, / など）
        child_id_list (list[uuid.UUID] | None): 子ノードIDリスト（順番保持）
    """

    parent_id: uuid.UUID = Field(..., description="親ノードID")
    operator: str = Field(..., description="演算子")
    child_id_list: list[uuid.UUID] | None = Field(default=None, description="子ノードのIDリスト、順番保持")


class DriverTreeNodeData(BaseCamelCaseModel):
    """ノードデータ構造（API伝送用）。

    ExcelやCSVから読み込んだデータを表現します。
    Service層でpandas DataFrameとの相互変換を行います。

    Attributes:
        columns (list[str]): カラム名のリスト
        records (list[dict[str, Any]]): データレコード（行のリスト）
    """

    columns: list[str] = Field(..., description="カラム名のリスト")
    records: list[dict[str, Any]] = Field(..., description="データレコード（行のリスト）")


class DriverTreeNodeCalculatedData(BaseCamelCaseModel):
    """計算済みノードデータ構造。
    Attributes:
        - node_id: uuid - ノードID
        - label: str - ノード名
        - columns: list[str] - カラム名のリスト
        - records: list[dict[str, Any]] - データレコード（行のリスト）
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    label: str = Field(..., description="ノード名")
    columns: list[str] = Field(..., description="カラム名のリスト")
    records: list[dict[str, Any]] = Field(..., description="データレコード（行のリスト）")


class DriverTreeNodeInfo(BaseCamelCaseModel):
    """ノード情報

    Attributes:
        - node_id: uuid - ノードID
        - label: str - ノード名
        - node_type: str - ノードタイプ（入力|計算|定数）
        - position_x :int - 座標
        - position_y :int - 座標
        - data: DriverTreeNodeData - 入力ノードのデータ
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    label: str = Field(..., description="ノード名")
    node_type: DriverTreeNodeTypeEnum = Field(..., description="ノードタイプ")
    position_x: int = Field(..., description="X座標")
    position_y: int = Field(..., description="Y座標")
    data: DriverTreeNodeData | None = Field(default=None, description="入力ノードのデータ")


class DriverTreeInfo(BaseCamelCaseModel):
    """ツリー情報詳細。

    Attributes:
        tree_id: ツリーID
        name: ツリー名
        description: 説明
        root: ルートノード
        nodes: list[dict] ノード情報
        relationship: list[dict] ノード親関係情報
    """

    tree_id: uuid.UUID = Field(..., description="ツリーID")
    name: str = Field(..., description="ツリー名")
    description: str | None = Field(default=None, description="説明")
    root: DriverTreeNodeInfo
    nodes: list[DriverTreeNodeInfo]
    relationship: list[DriverTreeRelationshipInfo]


class DriverTreeNodePolicyInfo(BaseCamelCaseModel):
    """施策情報

    Attributes:
        - policy_id: uuid - 施策ID
        - name: str - 施策名
        - value: float - 施策値
        - description: str | None - 施策説明
        - cost: float | None - コスト
        - duration_months: int | None - 実施期間（月）
        - status: str - 状態（planned/in_progress/completed）
    """

    policy_id: uuid.UUID = Field(..., description="施策ID")
    name: str = Field(..., description="施策名")
    value: float = Field(..., description="施策値")
    description: str | None = Field(default=None, description="施策説明")
    cost: float | None = Field(default=None, description="コスト")
    duration_months: int | None = Field(default=None, description="実施期間（月）")
    status: DriverTreePolicyStatusEnum = Field(default=DriverTreePolicyStatusEnum.PLANNED, description="状態")


class DriverTreeColumnInfo(BaseCamelCaseModel):
    """カラム情報。

    Attributes:
        - column_id: uuid - カラムID（一意識別子）
        - column_name: str - カラム名
        - role: str - カラムの役割
        - items: list[str] - 項目例
    """

    column_id: uuid.UUID = Field(..., description="カラムID（一意識別子）")
    column_name: str = Field(..., description="カラム名")
    role: DriverTreeColumnRoleEnum = Field(default=DriverTreeColumnRoleEnum.UNUSED, description="カラムの役割")
    items: list[str] = Field(default_factory=list, description="項目例")


class DriverTreeSheetInfo(BaseCamelCaseModel):
    """シート情報。

    Attributes:
        - sheet_id: uuid - シートID
        - name: str - シート名
    """

    sheet_id: uuid.UUID = Field(..., description="シートID")
    sheet_name: str = Field(..., description="シート名")
    columns: list[DriverTreeColumnInfo] = Field(default_factory=list, description="カラム一覧")


class DriverTreeUploadedSheetInfo(BaseCamelCaseModel):
    """アップロード済みシート情報（Upload API用）。

    Attributes:
        - sheet_id: uuid - シートID
        - sheet_name: str - シート名
    """

    sheet_id: uuid.UUID = Field(..., description="シートID")
    sheet_name: str = Field(..., description="シート名")


class DriverTreeUploadedFileItem(BaseCamelCaseModel):
    """アップロード済みファイル情報（Upload API用）。

    Attributes:
        - file_id: uuid - ファイルID
        - filename: str - ファイル名
        - file_size: int - ファイルサイズ（バイト）
        - uploaded_at: datetime - アップロード日時
        - sheets: list[DriverTreeUploadedSheetInfo] - シート一覧（columns なし）
    """

    file_id: uuid.UUID = Field(..., description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    sheets: list[DriverTreeUploadedSheetInfo] = Field(default_factory=list, description="シート一覧")


class DriverTreeFileListItem(BaseCamelCaseModel):
    """ファイル一覧アイテム（List Files API用）。

    Attributes:
        - file_id: uuid - ファイルID
        - filename: str - ファイル名
        - uploaded_at: datetime - アップロード日時
        - sheets: - シート一覧
            - sheet_id: uuid - シートID
            - sheet_name: str - シート名
            - columns:  - カラム一覧
                - column_name: str - カラム名
                - role: str - カラムの役割
                - items: list[str] - 項目例
    """

    file_id: uuid.UUID = Field(..., description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    sheets: list[DriverTreeSheetInfo] = Field(default_factory=list, description="シート一覧")


class DriverTypeInfo(BaseCamelCaseModel):
    """ドライバー型情報。

    Attributes:
        driver_type_id: ドライバー型ID
        driver_type: ドライバー型
    """

    driver_type_id: int = Field(..., description="ドライバー型ID")
    driver_type: str = Field(..., description="ドライバー型")


class IndustryInfo(BaseCamelCaseModel):
    """業界名情報。

    Attributes:
        industry_id: 業界名ID
        industry_name: 業界名
        driver_types: ドライバー型リスト
    """

    industry_id: int = Field(..., description="業界名ID")
    industry_name: str = Field(..., description="業界名")
    driver_types: list[DriverTypeInfo] = Field(default_factory=list, description="ドライバー型リスト")


class CategoryInfo(BaseCamelCaseModel):
    """業界分類情報。

    Attributes:
        category_id: 業界分類ID
        category_name: 業界分類名
        industries: 業界名リスト
    """

    category_id: int = Field(..., description="業界分類ID")
    category_name: str = Field(..., description="業界分類名")
    industries: list[IndustryInfo] = Field(default_factory=list, description="業界名リスト")


class FormulaInfo(BaseCamelCaseModel):
    """数式情報。

    Attributes:
        formula_id: 数式ID
        driver_type_id: ドライバー型ID
        driver_type: ドライバー型
        kpi: KPI種別
        formulas: 数式リスト
    """

    formula_id: uuid.UUID = Field(..., description="数式ID")
    driver_type_id: int = Field(..., description="ドライバー型ID")
    driver_type: str = Field(..., description="ドライバー型")
    kpi: DriverTreeKpiEnum = Field(..., description="KPI種別")
    formulas: list[str] = Field(default_factory=list, description="数式リスト")
