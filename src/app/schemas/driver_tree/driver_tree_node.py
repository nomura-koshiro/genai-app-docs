import uuid

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel
from app.schemas.driver_tree.common import (
    DriverTreeInfo,
    DriverTreeNodeInfo,
    DriverTreeNodePolicyInfo,
    DriverTreeNodeTypeEnum,
    DriverTreePolicyStatusEnum,
)


# Request
class DriverTreeCreateNodeRequest(BaseCamelCaseModel):
    """ノード作成リクエスト。

    Request Body:
        - label: str - ノード名（必須）
        - position_x :int - 座標（必須）
        - position_y :int - 座標（必須）
        - node_type: str - ノードタイプ（"入力"|"計算"|"定数"）（必須）
    """

    label: str = Field(..., description="ノード名")
    node_type: DriverTreeNodeTypeEnum = Field(..., description="ノードタイプ")
    position_x: int = Field(..., description="X座標")
    position_y: int = Field(..., description="Y座標")


class DriverTreeNodeUpdateRequest(BaseCamelCaseModel):
    """ノード更新リクエスト。

    Request Body:
        - label: str - ノード名（オプション）
        - node_type: str - ノードタイプ（"入力"|"計算"|"定数"）（オプション）
        - position_x :int - 座標（オプション）
        - position_y :int - 座標（オプション）
        - operator: str - 計算ノード演算子（オプション）
        - children_id_list : list[uuid] - 計算ノードの子ノードIDリスト

    """

    label: str | None = Field(default=None, description="ノード名")
    node_type: DriverTreeNodeTypeEnum | None = Field(default=None, description="ノードタイプ")
    position_x: int | None = Field(default=None, description="X座標")
    position_y: int | None = Field(default=None, description="Y座標")
    operator: str | None = Field(default=None, description="演算子")
    children_id_list: list[uuid.UUID] | None = Field(default=None, description="計算ノードの子ノードIDリスト")


class DriverTreeNodePolicyCreateRequest(BaseCamelCaseModel):
    """施策作成リクエスト。

    Request Body:
        - name: str - 施策名
        - value: float - 施策値
        - description: str | None - 施策説明（オプション）
        - cost: float | None - コスト（オプション）
        - duration_months: int | None - 実施期間（月）（オプション）
        - status: str - 状態（オプション、デフォルト: planned）
    """

    name: str = Field(..., description="施策名")
    value: float = Field(..., description="施策値")
    description: str | None = Field(default=None, description="施策説明")
    cost: float | None = Field(default=None, description="コスト")
    duration_months: int | None = Field(default=None, description="実施期間（月）")
    status: DriverTreePolicyStatusEnum = Field(
        default=DriverTreePolicyStatusEnum.PLANNED,
        description="状態（planned/in_progress/completed）",
    )


class DriverTreeNodePolicyUpdateRequest(BaseCamelCaseModel):
    """施策更新リクエスト。

    Request Body:
        - name: str - 施策名(オプション)
        - value: float - 施策値(オプション)
        - description: str | None - 施策説明（オプション）
        - cost: float | None - コスト（オプション）
        - duration_months: int | None - 実施期間（月）（オプション）
        - status: str - 状態（オプション）
    """

    name: str | None = Field(default=None, description="施策名")
    value: float | None = Field(default=None, description="施策値")
    description: str | None = Field(default=None, description="施策説明")
    cost: float | None = Field(default=None, description="コスト")
    duration_months: int | None = Field(default=None, description="実施期間（月）")
    status: DriverTreePolicyStatusEnum | None = Field(default=None, description="状態")


# Response
class DriverTreeNodeCreateResponse(BaseCamelCaseModel):
    """ノード作成レスポンス。

    Response:
        - tree : DriverTreeInfo - ツリー全体構造
        - created_node_id: uuid - ノードID
    """

    tree: DriverTreeInfo = Field(..., description="ツリー全体構造")
    created_node_id: uuid.UUID = Field(..., description="作成されたノードID")


class DriverTreeNodeDetailResponse(BaseCamelCaseModel):
    """ノード詳細取得レスポンス。

    Response:
        - node : DriverTreeNodeInfo - ノード詳細情報
    """

    node: DriverTreeNodeInfo = Field(..., description="ノード詳細情報")


class DriverTreeNodeUpdateResponse(BaseCamelCaseModel):
    """ノード更新レスポンス。

    Response:
        - tree : DriverTreeInfo - ツリー全体構造
    """

    tree: DriverTreeInfo = Field(..., description="ツリー全体構造")


class DriverTreeNodeDeleteResponse(BaseCamelCaseModel):
    """ノード削除レスポンス。

    Response:
        - tree : DriverTreeInfo - ツリー全体構造
    """

    tree: DriverTreeInfo = Field(..., description="ツリー全体構造")


class DriverTreeNodePolicyCreateResponse(BaseCamelCaseModel):
    """施策作成レスポンス。

    Response:
        - node_id: uuid - ノードID
        - policies: list[dict] - 施策一覧
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    policies: list[DriverTreeNodePolicyInfo] = Field(default_factory=list, description="施策一覧")


class DriverTreeNodePolicyResponse(BaseCamelCaseModel):
    """施策一覧レスポンス。

    Response:
        - node_id: uuid - ノードID
        - policies: list[dict] - 施策一覧
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    policies: list[DriverTreeNodePolicyInfo] = Field(default_factory=list, description="施策一覧")


class DriverTreeNodePolicyUpdateResponse(BaseCamelCaseModel):
    """施策更新レスポンス。

    Response:
        - node_id: uuid - ノードID
        - policies: list[dict] - 施策一覧
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    policies: list[DriverTreeNodePolicyInfo] = Field(default_factory=list, description="施策一覧")


class DriverTreeNodePolicyDeleteResponse(BaseCamelCaseModel):
    """施策削除レスポンス。

    Response:
        - node_id: uuid - ノードID
        - policies: list[dict] - 施策一覧
    """

    node_id: uuid.UUID = Field(..., description="ノードID")
    policies: list[DriverTreeNodePolicyInfo] = Field(default_factory=list, description="施策一覧")
