"""Aggregation step tools for analysis agent.

集計ステップの設定取得・更新を行うツールを提供します。
グループ化軸と科目ごとの集計方法を設定できます。

Tools:
    - GetAggregationTool: 集計設定取得
    - SetAggregationTool: 集計設定更新
"""

import json
import uuid

from langchain.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.services.analysis.agent.state import AnalysisState

logger = get_logger(__name__)


class GetAggregationTool(BaseTool):
    """集計設定取得ツール。

    指定したステップの集計設定を取得します。

    Attributes:
        name (str): ツール名（"get_aggregation"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetAggregationTool(db, session_id)
        >>> result = await tool._arun("0")
        >>> print(result)
        ステップ0の集計設定:
        グループ化軸: 地域, 商品
        集計設定:
          名称: 売上合計, 科目: 売上, 方法: sum
    """

    name: str = "get_aggregation"
    description: str = "指定したステップの集計設定を取得します。入力形式: 'step_index' (数値)"

    db: AsyncSession
    session_id: uuid.UUID

    class Config:
        """Pydantic設定。"""

        arbitrary_types_allowed = True

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """初期化。

        Args:
            db (AsyncSession): データベースセッション
            session_id (uuid.UUID): 分析セッションID
        """
        super().__init__(db=db, session_id=session_id)

    @measure_performance
    async def _arun(self, input_str: str = "") -> str:
        """非同期実行。

        指定したステップの集計設定を取得します。

        Args:
            input_str (str): 'step_index' 形式の文字列
                - step_index: 集計設定を取得するステップのインデックス（0から始まる整数）

        Returns:
            str: 集計設定の詳細

        Example:
            >>> await tool._arun("0")
        """
        logger.info(
            "get_aggregation_tool_called",
            session_id=str(self.session_id),
            input=input_str,
            tool="get_aggregation",
        )

        try:
            step_index_str = input_str.strip()
            if not step_index_str:
                return "実行失敗: ステップインデックスが指定されていません。形式: 'step_index'"

            try:
                step_index = int(step_index_str)
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {step_index_str}"

            # ステップ一覧を取得
            from app.repositories.analysis import AnalysisStepRepository

            step_repo = AnalysisStepRepository(self.db)
            all_steps = await step_repo.list_by_session(self.session_id, is_active=True)

            if step_index < 0 or step_index >= len(all_steps):
                return (
                    f"実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(all_steps) - 1}, 指定値: {step_index}"
                )

            if all_steps[step_index].step_type != "aggregate":
                return (
                    f"実行失敗: ステップ{step_index}は集計ステップではありません。"
                    f"集計設定は'aggregate'タイプのステップでのみ利用可能です。"
                )

            state = AnalysisState(self.db, self.session_id)
            aggregation = await state.get_config(step_index)

            result = f"ステップ{step_index}の集計設定:\n"

            # グループ化軸
            if aggregation.get("axis"):
                result += f"グループ化軸: {', '.join(aggregation['axis'])}\n"
            else:
                result += "グループ化軸: 設定なし\n"

            # 集計設定
            if aggregation.get("column"):
                result += "集計設定:\n"
                for agg in aggregation["column"]:
                    result += f"  名称: {agg.get('name', 'N/A')}, 科目: {agg.get('subject', 'N/A')}, 方法: {agg.get('method', 'N/A')}\n"
            else:
                result += "集計設定: 設定なし\n"

            return result

        except Exception as e:
            logger.error(
                "get_aggregation_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: 集計設定の取得中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class SetAggregationTool(BaseTool):
    """集計設定ツール。

    指定したステップに集計設定を適用します。
    グループ化軸と科目ごとの集計方法を設定します。

    Attributes:
        name (str): ツール名（"set_aggregation"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = SetAggregationTool(db, session_id)
        >>> agg_json = '{"axis": ["地域"], "column": [{"name": "売上合計", "subject": "売上", "method": "sum"}]}'
        >>> result = await tool._arun(f"0, {agg_json}")
        >>> print(result)
        ステップ0に集計設定を適用しました。
    """

    name: str = "set_aggregation"
    description: str = """
指定したステップに集計設定を適用します。
入力形式: 'step_index, aggregation_json' (aggregation_jsonは集計設定のJSON)
aggregation_jsonは以下の集計を設定できます:
    - 集計軸: 'axis'はリスト形式で、グループ化する集計軸を指定します。例:
        - '地域'と'製品'が存在するデータに、地域ごとに集計したい場合:
          'axis' は ['地域'] となります。これによって、製品軸がなくなり、
          地域ごとに集計されたデータが出力されます。
        - '地域'と'製品'が存在するデータに、地域と製品ごとに集計したい場合:
          'axis' は ['地域', '製品'] となります。
          これによって、地域と製品ごとの集計が行われます。
    - 科目ごとの集計(合計、平均など): 'column' はリスト形式で、
      各科目の集計方法を指定します。その要素は、'name'(集計後の名称)、
      'subject'(科目名)と'method'(集計方法)を含む辞書です。例:
        - methodがsum, mean, count, max, minのとき、
          subjectはステップの入力データの科目名(例: '売り上げ高')を指定し、
          データ上の計算を行います。
            - 売り上げ高の合計: 辞書型式の要素として、
              'name': '売上高合計', 'subject': '売上高', 'method': 'sum'
            - 利益の合計: 辞書型式の要素として、
              'name': '利益合計', 'subject': '利益', 'method': 'sum'
        - methodが+, -, *, /のとき、subjectは他の集計科目の'name'を
          参照するリスト(例: ['売り上げ高', '商品の個数'])を指定し、
          計算式結果の四則演算を行います。
          ただしlistの長さは2つでなければなりません。
            - 利益率: 辞書型式の要素として、
              'name': '利益率', 'subject': ['売上高合計', '利益合計'],
              'method': '/'
"""

    db: AsyncSession
    session_id: uuid.UUID

    class Config:
        """Pydantic設定。"""

        arbitrary_types_allowed = True

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """初期化。

        Args:
            db (AsyncSession): データベースセッション
            session_id (uuid.UUID): 分析セッションID
        """
        super().__init__(db=db, session_id=session_id)

    @measure_performance
    async def _arun(self, input_str: str = "") -> str:
        """非同期実行。

        指定したステップの集計configに書き込みます。

        Args:
            input_str (str): 'step_index, aggregation_config' 形式の文字列
                - step_index: ステップのインデックス（0から始まる整数）
                - aggregation_config: configのJSON文字列

        Returns:
            str: 実行結果の詳細

        Example:
            >>> agg_json = '{"axis": ["地域"], "column": [{"name": "売上合計", "subject": "売上", "method": "sum"}]}'
            >>> await tool._arun(f"0, {agg_json}")
        """
        logger.info(
            "set_aggregation_tool_called",
            session_id=str(self.session_id),
            input=input_str[:100],
            tool="set_aggregation",
        )

        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, aggregation_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            # ステップ一覧を取得
            from app.repositories.analysis import AnalysisStepRepository

            step_repo = AnalysisStepRepository(self.db)
            all_steps = await step_repo.list_by_session(self.session_id, is_active=True)

            if step_index < 0 or step_index >= len(all_steps):
                return (
                    f"実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(all_steps) - 1}, 指定値: {step_index}"
                )

            if all_steps[step_index].step_type != "aggregate":
                return (
                    f"実行失敗: ステップ{step_index}は集計ステップではありません。"
                    f"集計設定は'aggregate'タイプのステップでのみ利用可能です。"
                )

            try:
                aggregation_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: 集計設定中にエラーが発生しました: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            state = AnalysisState(self.db, self.session_id)
            result_overview = await state.set_config(step_index, aggregation_json)

            logger.info(
                "set_aggregation_tool_success",
                session_id=str(self.session_id),
                step_index=step_index,
            )

            return f"ステップ{step_index}に集計設定を適用しました。\n{result_overview}"

        except Exception as e:
            logger.error(
                "set_aggregation_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: 集計設定中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")
