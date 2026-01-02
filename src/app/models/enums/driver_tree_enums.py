"""ドライバーツリー関連のEnum定義。

このモジュールは、ドライバーツリー機能で使用する定数をEnumで定義します。
"""

from enum import StrEnum


class DriverTreeNodeTypeEnum(StrEnum):
    """ノードタイプ。

    Values:
        INPUT: 入力ノード
        CALCULATION: 計算ノード
        CONSTANT: 定数ノード
    """

    INPUT = "入力"
    CALCULATION = "計算"
    CONSTANT = "定数"


class DriverTreeColumnRoleEnum(StrEnum):
    """カラムの役割。

    Values:
        TRANSITION: 推移
        AXIS: 軸
        VALUE: 値
        UNUSED: 利用しない
    """

    TRANSITION = "推移"
    AXIS = "軸"
    VALUE = "値"
    UNUSED = "利用しない"


class DriverTreeKpiEnum(StrEnum):
    """KPI種別。

    Values:
        REVENUE: 売上
        COGS: 原価
        SGA: 販管費
        GROSS_PROFIT: 粗利
        OPERATING_INCOME: 営業利益
        EBITDA: EBITDA
    """

    REVENUE = "売上"
    COGS = "原価"
    SGA = "販管費"
    GROSS_PROFIT = "粗利"
    OPERATING_INCOME = "営業利益"
    EBITDA = "EBITDA"


class DriverTreePolicyStatusEnum(StrEnum):
    """施策状態。

    Values:
        PLANNED: 計画中
        IN_PROGRESS: 実施中
        COMPLETED: 完了
    """

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
