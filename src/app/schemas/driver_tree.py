"""Driver Tree機能用のPydanticスキーマ定義。

このモジュールは、ドライバーツリー機能に関連する
リクエスト/レスポンススキーマを定義します。

主なスキーマ:
    - DriverTreeNodeCreate: ノード作成リクエスト
    - DriverTreeNodeUpdate: ノード更新リクエスト
    - DriverTreeNodeResponse: ノードレスポンス（木構造）
    - DriverTreeResponse: ツリーレスポンス
    - DriverTreeFormulaCreateRequest: 数式からツリー作成リクエスト
    - DriverTreeCategoryResponse: カテゴリーレスポンス

使用例:
    >>> from app.schemas.driver_tree import DriverTreeNodeCreate
    >>>
    >>> # ルートノード作成
    >>> root = DriverTreeNodeCreate(
    ...     tree_id=tree_id,
    ...     label="粗利",
    ...     x=0,
    ...     y=0
    ... )
"""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class DriverTreeNodeCreate(BaseModel):
    """ノード作成リクエスト。

    Attributes:
        tree_id: 所属するツリーのID
        label: ノードのラベル（KPI名や計算要素名）
        parent_id: 親ノードID（Noneの場合はルートノード）
        operator: 親ノードとの演算子（+, -, *, /, %など）
        x: X座標（ツリー表示用）
        y: Y座標（ツリー表示用）
    """

    tree_id: uuid.UUID = Field(..., description="所属するツリーのID")
    label: str = Field(..., min_length=1, max_length=100, description="ノードのラベル")
    parent_id: uuid.UUID | None = Field(None, description="親ノードID（Noneの場合はルートノード）")
    operator: str | None = Field(None, max_length=10, description="親ノードとの演算子")
    x: int | None = Field(None, ge=0, description="X座標")
    y: int | None = Field(None, ge=0, description="Y座標")


class DriverTreeNodeUpdate(BaseModel):
    """ノード更新リクエスト。"""

    label: str | None = Field(None, min_length=1, max_length=100, description="ノードのラベル")
    parent_id: uuid.UUID | None = Field(None, description="親ノードID")
    operator: str | None = Field(None, max_length=10, description="演算子")
    x: int | None = Field(None, ge=0, description="X座標")
    y: int | None = Field(None, ge=0, description="Y座標")


class DriverTreeNodeResponse(BaseModel):
    """ノードレスポンス（木構造）。"""

    id: uuid.UUID = Field(..., description="ノードID")
    tree_id: uuid.UUID = Field(..., description="所属するツリーのID")
    label: str = Field(..., description="ノードのラベル")
    parent_id: uuid.UUID | None = Field(None, description="親ノードID")
    operator: str | None = Field(None, description="演算子")
    x: int | None = Field(None, description="X座標")
    y: int | None = Field(None, description="Y座標")
    children: list["DriverTreeNodeResponse"] = Field(default_factory=list, description="子ノードのリスト")

    class Config:
        from_attributes = True


class DriverTreeResponse(BaseModel):
    """ツリーレスポンス。"""

    id: uuid.UUID = Field(..., description="ツリーID")
    name: str | None = Field(None, description="ツリー名")
    root_node_id: uuid.UUID | None = Field(None, description="ルートノードID")
    root_node: DriverTreeNodeResponse | None = Field(None, description="ルートノード（木構造全体を含む）")

    class Config:
        from_attributes = True


class DriverTreeFormulaCreateRequest(BaseModel):
    """数式からツリー作成リクエスト。"""

    name: str | None = Field(None, max_length=200, description="ツリー名")
    formulas: list[str] = Field(..., min_length=1, description="数式のリスト")


class DriverTreeCategoryResponse(BaseModel):
    """カテゴリーレスポンス。"""

    id: uuid.UUID = Field(..., description="カテゴリーID")
    industry_class: str = Field(..., description="業種大分類")
    industry: str = Field(..., description="業種")
    tree_type: str = Field(..., description="ツリータイプ")
    kpi: str = Field(..., description="KPI名")
    formulas: list[str] = Field(..., description="数式のリスト")
    category_metadata: dict[str, Any] = Field(default_factory=dict, description="メタデータ")

    class Config:
        from_attributes = True


class DriverTreeKPIListResponse(BaseModel):
    """KPI一覧レスポンス。"""

    kpis: list[str] = Field(..., description="KPI名のリスト")


class DriverTreeFormulaResponse(BaseModel):
    """数式レスポンス。"""

    formulas: list[str] = Field(..., description="数式のリスト")
