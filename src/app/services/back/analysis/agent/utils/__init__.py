"""分析エージェントユーティリティパッケージ。

このパッケージは分析エージェント用のLangChain BaseToolを提供します。
camp-backend-code-analysisからの移植版で、DB永続化されたAnalysisStateと統合されています。

利用可能なツール:
    - GetDataOverviewTool: データ概要取得
    - GetStepOverviewTool: ステップ概要取得
    - AddStepTool: ステップ追加
    - DeleteStepTool: ステップ削除
    - GetFilterTool: フィルタ設定取得
    - GetAggregationTool: 集計設定取得
    - GetTransformTool: 変換設定取得
    - GetSummaryTool: サマリ設定取得
    - SetFilterTool: フィルタ設定
    - SetAggregationTool: 集計設定
    - SetTransformTool: 変換設定
    - SetSummaryTool: サマリ設定
    - GetDataValueTool: データ値取得

使用例:
    >>> from app.services.analysis.agent.utils import (
    ...     GetDataOverviewTool,
    ...     AddStepTool,
    ... )
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> import uuid
    >>>
    >>> # ツールの初期化
    >>> async with get_db() as db:
    ...     session_id = uuid.uuid4()
    ...     overview_tool = GetDataOverviewTool(db, session_id)
    ...     add_step_tool = AddStepTool(db, session_id)
    ...
    ...     # ツールの実行
    ...     result = await overview_tool._arun()
    ...     print(result)

Note:
    - すべてのツールはLangChainのBaseToolを継承しています
    - ツールは非同期（async/await）で動作します
    - AnalysisStateを通じてDB永続化されたデータにアクセスします
"""

from app.services.analysis.agent.utils.tools import (
    AddStepTool,
    DeleteStepTool,
    GetAggregationTool,
    GetDataOverviewTool,
    GetDataValueTool,
    GetFilterTool,
    GetStepOverviewTool,
    GetSummaryTool,
    GetTransformTool,
    SetAggregationTool,
    SetFilterTool,
    SetSummaryTool,
    SetTransformTool,
)

__all__ = [
    # Common tools
    "GetDataOverviewTool",
    "GetStepOverviewTool",
    "AddStepTool",
    "DeleteStepTool",
    "GetDataValueTool",
    # Filter tools
    "GetFilterTool",
    "SetFilterTool",
    # Aggregation tools
    "GetAggregationTool",
    "SetAggregationTool",
    # Transform tools
    "GetTransformTool",
    "SetTransformTool",
    # Summary tools
    "GetSummaryTool",
    "SetSummaryTool",
]
