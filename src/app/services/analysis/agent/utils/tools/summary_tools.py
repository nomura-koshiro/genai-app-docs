"""Summary step tools for analysis agent.

サマリステップの設定取得・更新を行うツールを提供します。
計算式、チャート、テーブルの設定を行います。

Tools:
    - GetSummaryTool: サマリ設定取得
    - SetSummaryTool: サマリ設定更新
"""

import json
import uuid

from langchain.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.services.analysis.agent.state import AnalysisState

logger = get_logger(__name__)


class GetSummaryTool(BaseTool):
    """サマリ設定取得ツール。

    指定したステップのサマリ設定（計算式とチャート設定）を取得します。

    Attributes:
        name (str): ツール名（"get_summary"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetSummaryTool(db, session_id)
        >>> result = await tool._arun("0")
        >>> print(result)
        ステップ0のサマリ設定:
        計算式:
          1. 科目: 売上, 計算: sum, 単位: 円
    """

    name: str = "get_summary"
    description: str = "指定したステップのサマリ設定（計算式とチャート設定）を取得します。入力形式: 'step_index' (数値)"

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

        指定したステップのサマリ設定を取得します。

        Args:
            input_str (str): 'step_index' 形式の文字列
                - step_index: サマリ設定を取得するステップのインデックス（0から始まる整数）

        Returns:
            str: サマリ設定の詳細

        Example:
            >>> await tool._arun("0")
        """
        logger.info(
            "get_summary_tool_called",
            session_id=str(self.session_id),
            input=input_str,
            tool="get_summary",
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
            from app.repositories import AnalysisStepRepository

            step_repo = AnalysisStepRepository(self.db)
            all_steps = await step_repo.list_by_session(self.session_id, is_active=True)

            if step_index < 0 or step_index >= len(all_steps):
                return f"実行失敗: ステップインデックスが範囲外です。有効範囲: 0-{len(all_steps) - 1}, 指定値: {step_index}"

            if all_steps[step_index].step_type != "summary":
                return f"実行失敗: ステップ{step_index}はサマリステップではありません。"

            state = AnalysisState(self.db, self.session_id)
            summary = await state.get_config(step_index)

            result = f"ステップ{step_index}のサマリ設定:\n"

            # 計算式
            if summary.get("formula"):
                result += "計算式:\n"
                for i, formula in enumerate(summary["formula"]):
                    subject = formula.get("target_subject", "N/A")
                    calc_type = formula.get("type", "N/A")
                    unit = formula.get("unit", "N/A")
                    result += f"  {i + 1}. 科目: {subject}, 計算: {calc_type}, 単位: {unit}\n"
            else:
                result += "計算式: 設定なし\n"

            # チャート設定
            if summary.get("chart"):
                result += f"チャート設定: あり（タイプ: {summary['chart'].get('graph_type', 'unknown')})\n"
            else:
                result += "チャート設定: 設定なし\n"

            # テーブル設定
            if summary.get("table"):
                if "show_source_data" in summary["table"].keys() and summary["table"]["show_source_data"]:
                    result += f"テーブル設定: ステップの入力データを表記, 名称: {summary['table'].get('table_name', 'N/A')}\n"
                else:
                    result += "テーブル設定: ステップの入力データをを表記しない\n"

            return result

        except Exception as e:
            logger.error(
                "get_summary_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: サマリ設定の取得中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class SetSummaryTool(BaseTool):
    """サマリ設定ツール。

    指定したステップにサマリ設定（計算式とチャート設定）を設定します。

    Attributes:
        name (str): ツール名（"set_summary"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = SetSummaryTool(db, session_id)
        >>> summary_json = (
        ...     '{"formula": [{"target_subject": "売上", "type": "sum", '
        ...     '"formula_text": "売上合計", "unit": "円", "portion": 1.0}], '
        ...     '"chart": {}, "table": {"show_source_data": true, '
        ...     '"table_name": "サマリ表"}}'
        ... )
        >>> result = await tool._arun(f"0, {summary_json}")
        >>> print(result)
        ステップ0にサマリ設定を適用しました。計算式: 1個, チャート設定: なし, テーブル設定: サマリ表 で表記
    """

    name: str = "set_summary"
    description: str = """
指定したステップにサマリ設定（計算式とチャート設定）を設定します。
入力形式: 'step_index, summary_json' (summary_jsonはサマリ設定のJSON)
summary_jsonは以下の設定を含みます:
    - 計算式の設定: 特定の科目に対して計算式を設定し、結果を表示します。
      計算方法(合計、平均など)と表示用のテキストと単位を指定する必要があります。
        - 計算式の設定では、'target_subject'(対象)、'type'(計算方法)、
          'formula_text'(表示用のテキスト)、'unit'(単位),
          'portion'(重み、値が掛ける係数)を指定する必要があります。
        - 'type'に応じて計算式の操作対象が変わります。
            - 'type'が+, -, *, /のとき、'target_subject'は他の計算式の
              'formula_text'を参照するリスト
              (例: ['売り上げ高', '商品の個数'])を指定し、
              計算式結果の四則演算を行います。
              ただしlistの長さは2つでなければなりません。
            - 'type'がsum, mean, count, max, minのとき、
              'target_subject'はステップの入力データの科目名
              (例: '売り上げ高')を指定し、データ上の計算を行います。
        - 複数の計算式を同時に設定することも可能です。
    - チャートの設定(例: 折れ線グラフ、棒グラフなど)を行うことができます。
      チャートの種類と表示する科目を指定する必要があります。
        - 'graph_type'(チャートの種類)をまず指定し、
          次に表示する科目を設定する必要があります。
        - オプションで、'title'(チャートの名称)も設定できます。
    - 出力テーブルの設定: そのステップのソースデータを出力することができます。
      table_configで'show_source_data'(ソースデータを表示するかどうか)と
      'table_name'(テーブルの名称)を指定する必要があります。例:
        - そのステップのソースデータをそのまま出力したい場合は、
          'show_source_data': true, 'table_name': 'ソースデータ'
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

        指定したステップのサマリconfigに書き込みます。

        Args:
            input_str (str): 'step_index, summary_config' 形式の文字列
                - step_index: ステップのインデックス（0から始まる整数）
                - summary_config: configのJSON文字列

        Returns:
            str: 実行結果の詳細

        Example:
            >>> summary_json = (
            ...     '{"formula": [{"target_subject": "売上", "type": "sum", '
            ...     '"formula_text": "売上合計", "unit": "円", "portion": 1.0}], '
            ...     '"chart": {}, "table": {"show_source_data": true, '
            ...     '"table_name": "サマリ表"}}'
            ... )
            >>> await tool._arun(f"0, {summary_json}")
        """
        logger.info(
            "set_summary_tool_called",
            session_id=str(self.session_id),
            input=input_str[:100],
            tool="set_summary",
        )

        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, summary_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            # ステップ一覧を取得
            from app.repositories import AnalysisStepRepository

            step_repo = AnalysisStepRepository(self.db)
            all_steps = await step_repo.list_by_session(self.session_id, is_active=True)

            if step_index < 0 or step_index >= len(all_steps):
                return f"実行失敗: ステップインデックスが範囲外です。有効範囲: 0-{len(all_steps) - 1}, 指定値: {step_index}"

            if all_steps[step_index].step_type != "summary":
                return f"実行失敗: ステップ{step_index}はサマリステップではありません。"

            try:
                summary_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: サマリ設定中にエラーが発生しました:  JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            state = AnalysisState(self.db, self.session_id)
            await state.set_config(step_index, summary_json)

            formulas_count = len(summary_json.get("formula", []))
            chart_status = "あり" if summary_json.get("chart") else "なし"
            table_config = summary_json.get("table", {})
            table_status = (
                f"{table_config.get('table_name', '名称未設定')} で表記" if table_config.get("show_source_data", False) else "表記しない"
            )

            logger.info(
                "set_summary_tool_success",
                session_id=str(self.session_id),
                step_index=step_index,
            )

            return (
                f"ステップ{step_index}にサマリ設定を適用しました。"
                f"計算式: {formulas_count}個, チャート設定: {chart_status}, "
                f"テーブル設定: {table_status}"
            )

        except Exception as e:
            logger.error(
                "set_summary_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: サマリ設定中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")
