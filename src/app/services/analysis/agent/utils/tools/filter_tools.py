"""Filter step tools for analysis agent.

フィルタステップの設定取得・更新を行うツールを提供します。
カテゴリフィルタ、数値フィルタ、テーブルフィルタの3種類のフィルタを扱います。

Tools:
    - GetFilterTool: フィルタ設定取得
    - SetFilterTool: フィルタ設定更新
"""

import json
import uuid

from langchain.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.services.analysis.agent.state import AnalysisState

logger = get_logger(__name__)


class GetFilterTool(BaseTool):
    """フィルタ設定取得ツール。

    指定したステップのフィルタ設定を取得します。

    Attributes:
        name (str): ツール名（"get_filter"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetFilterTool(db, session_id)
        >>> result = await tool._arun("0")
        >>> print(result)
        ステップ0のフィルタ設定:
        カテゴリフィルタ:
          地域: 東京, 大阪
    """

    name: str = "get_filter"
    description: str = "指定したステップのフィルタ設定を取得します。入力形式: 'step_index' (数値)"

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

        指定したステップのフィルタ設定を取得します。

        Args:
            input_str (str): 'step_index' 形式の文字列
                - step_index: フィルタ設定を取得するステップのインデックス（0から始まる整数）

        Returns:
            str: フィルタ設定の詳細

        Example:
            >>> await tool._arun("0")
        """
        logger.info(
            "get_filter_tool_called",
            session_id=str(self.session_id),
            input=input_str,
            tool="get_filter",
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

            if all_steps[step_index].step_type != "filter":
                return (
                    f"実行失敗: ステップ{step_index}はフィルタステップではありません。"
                    f"フィルタ設定は'filter'タイプのステップでのみ利用可能です。"
                )

            state = AnalysisState(self.db, self.session_id)
            filters = await state.get_config(step_index)

            result = f"ステップ{step_index}のフィルタ設定:\n"

            # カテゴリフィルタ
            if filters.get("category_filter"):
                result += "カテゴリフィルタ:\n"
                for col, values in filters["category_filter"].items():
                    result += f"  {col}: {', '.join(map(str, values))}\n"
            else:
                result += "カテゴリフィルタ: 設定なし\n"

            # 数値フィルタ
            numeric = filters.get("numeric_filter", {})
            filter_type = numeric.get("filter_type", "range")

            result += f"数値フィルタ (タイプ: {filter_type}):\n"

            if filter_type == "range":
                if numeric.get("enable_min", False) or numeric.get("enable_max", False):
                    if numeric.get("enable_min", False):
                        result += f"  最小値: {numeric['min_value']} ({'含む' if numeric.get('include_min', True) else '含まない'})\n"
                    if numeric.get("enable_max", False):
                        result += f"  最大値: {numeric['max_value']} ({'含む' if numeric.get('include_max', True) else '含まない'})\n"
                else:
                    result += "  設定なし\n"

            elif filter_type == "topk":
                k_value = numeric.get("k_value", 0)
                if k_value > 0:
                    ascending = numeric.get("ascending", False)
                    order_text = "下位" if ascending else "上位"
                    result += f"  {order_text}{k_value}件を抽出\n"
                else:
                    result += "  設定なし\n"

            elif filter_type == "percentage":
                min_pct = numeric.get("min_percentile", 0)
                max_pct = numeric.get("max_percentile", 100)
                if min_pct > 0 or max_pct < 100:
                    result += f"  パーセンタイル範囲: {min_pct}% - {max_pct}%\n"
                else:
                    result += "  設定なし (全範囲)\n"

            # テーブルフィルタ
            table = filters.get("table_filter", {})
            if table.get("enable", False):
                key_cols = ", ".join(table["key_columns"])
                mode = "除外" if table["exclude_mode"] else "包含"
                result += f"テーブルフィルタ: キーカラム {key_cols}, モード: {mode}\n"
            else:
                result += "テーブルフィルタ: 設定なし\n"

            return result

        except Exception as e:
            logger.error(
                "get_filter_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: フィルタ設定の取得中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class SetFilterTool(BaseTool):
    """フィルタ設定ツール。

    指定したステップにフィルタ設定を適用します。
    カテゴリフィルタ、数値フィルタ、テーブルフィルタを設定できます。

    Attributes:
        name (str): ツール名（"set_filter"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = SetFilterTool(db, session_id)
        >>> filter_json = '{"category_filter": {"地域": ["東京", "大阪"]}, "numeric_filter": {}, "table_filter": {"enable": false}}'
        >>> result = await tool._arun(f"0, {filter_json}")
        >>> print(result)
        ステップ0にフィルタ設定を適用しました。
    """

    name: str = "set_filter"
    description: str = """
指定したステップにフィルタ設定を適用します。
入力形式: 'step_index, filter_json' (filter_jsonはフィルタ設定のJSON)
filter_jsonは以下のフィルタを設定できます (3つのフィルタを同時に設定することも可能です):
    - カテゴリフィルタ(特定の値を持つ行を選択):
      コラムごとに特定の値を持つ行を選択するためのフィルタを設定します。
        - カテゴリフィルタの設定では、dictの形で、以下の要素を含みます:
          'コラム1': ['残したいコラム1の値A', '残したいコラム1の値B']。例:
            - 地域を日本とアメリカ、製品を化学材料と自動車部品、
              科目を売り上げ高だけにしたい場合:
              '地域': ['日本', 'アメリカ'],
              '製品': ['化学材料', '自動車部品'],
              '科目': ['売り上げ高']
            - コラム1に存在する値1をなくしたい場合:
              'コラム1': ['値2', '値3', ...] など、
              コラム1に存在する値1ではないほかの値, 値2, 値3, ...を
              全部追加してください。
        - 特定の値を除外したい場合は、その特定な値以外のコラムに存在する
          すべての値をリストに追加してください。
        - カテゴリフィルタがいらない場合は空のdictを設定してください。
    - 数値フィルタ(値コラムに対する3種類のフィルタ):
      値コラムに対して、以下の3つのフィルタタイプから選択して設定できます。
        **■ 範囲指定フィルタ(filter_type: "range")**:
        最小値と最大値を指定して範囲内の値を選択
            - enable_min(下限フィルタを有効にするかどうか)、
              min_value(下限値)、include_min(下限値を含むかどうか)、
              enable_max(上限フィルタを有効にするかどうか)、
              max_value(上限値)、include_max(上限値を含むかどうか)を
              指定する必要があります。例:
                - 0以上の値だけ残したい場合:
                  "filter_type": "range", "enable_min": true,
                  "min_value": 0.0, "include_min": true, "enable_max": false
                - 100よりも小さい値だけ残したい場合:
                  "filter_type": "range", "enable_min": false,
                  "enable_max": true, "max_value": 100.0,
                  "include_max": false
                - 0以上100未満の値だけ残したい場合:
                  "filter_type": "range", "enable_min": true,
                  "min_value": 0.0, "include_min": true,
                  "enable_max": true, "max_value": 100.0,
                  "include_max": false
        **■ TopKフィルタ(filter_type: "topk")**: 上位K件または下位K件を抽出
            - k_value(抽出する件数)、ascending(false=上位K件、true=下位K件)を
              指定する必要があります。例:
                - 上位10件を取得したい場合:
                  "filter_type": "topk", "k_value": 10, "ascending": false
                - 下位5件を取得したい場合:
                  "filter_type": "topk", "k_value": 5, "ascending": true
                - 最大値の商品を取得したい場合:
                  "filter_type": "topk", "k_value": 1, "ascending": false
        **■ パーセンタイルフィルタ(filter_type: "percentage")**:
        パーセンタイル範囲で値を選択
            - min_percentile(下位パーセンタイル、0-100)、
              max_percentile(上位パーセンタイル、0-100)を指定する必要があります。例:
                - 中央50%のデータを取得したい場合:
                  "filter_type": "percentage", "min_percentile": 25,
                  "max_percentile": 75
                - 上位20%のデータを取得したい場合:
                  "filter_type": "percentage", "min_percentile": 80,
                  "max_percentile": 100
                - 下位10%を除外したい場合:
                  "filter_type": "percentage", "min_percentile": 10,
                  "max_percentile": 100
        - 数値フィルタは'値'コラム全体に対するフィルタとなっているので、
          特定な科目に対して数値フィルタを設定したい場合は、
          必ずまずその科目に対するカテゴリフィルタを設定してから
          次のステップで数値フィルタを設定してください。
        - 数値フィルタがいらない場合は空のdictを設定してください。
    - テーブルフィルタ(特定のコラムの組み合わせと同じものの選択):
      既存の中間テーブルを参照して、特定のコラムの組み合わせと同じ
      データ項目を除外または包含する設定を行います。
        - テーブルフィルタの設定では、'enable':(テーブルフィルタを使うかどうか)、
          'table_df'(除外対象の組み合わせを含むDataFrameの名前)、
          'key_columns'(組み合わせを特定するキー列)、
          'exclude_mode'(True=除外, False=包含)を指定する必要があります。例:
            - step_1で生成された中間データセットを参照して、
              特定の地域と製品の組み合わせを除外したい場合は、
              'table_df': 'step_1', 'key_columns': ['地域', '製品'],
              'exclude_mode': True, 'enable': True
            - step_2で生成された中間データセットを参照して、
              特定の地域と製品の組み合わせだけ包含したい場合は、
              'table_df': 'step_2', 'key_columns': ['地域', '製品'],
              'exclude_mode': False, 'enable': True
            - step_3で商品データをカテゴリフィルタで科目を利益率に設定、
              数値フィルタで値が0以上の部分だけを洗い出したが、
              利益率以外の科目も要るので、商品データに対してstep_3の
              中間データセットを参照して、商品名が同じのものだけを包含したい場合は、
              'table_df': 'step_3', 'key_columns': ['商品名'],
              'exclude_mode': False, 'enable': True
        - テーブルフィルタがいらない場合は空のdictを設定してください。
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

        指定したステップのフィルタconfigに書き込みます。

        Args:
            input_str (str): 'step_index, filter_config' 形式の文字列
                - step_index: ステップのインデックス（0から始まる整数）
                - filter_config: configのJSON文字列

        Returns:
            str: 実行結果の詳細

        Example:
            >>> filter_json = '{"category_filter": {"地域": ["東京"]}, "numeric_filter": {}, "table_filter": {"enable": false}}'
            >>> await tool._arun(f"0, {filter_json}")
        """
        logger.info(
            "set_filter_tool_called",
            session_id=str(self.session_id),
            input=input_str[:100],  # ログには先頭100文字のみ
            tool="set_filter",
        )

        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, filter_json'"

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

            if all_steps[step_index].step_type != "filter":
                return (
                    f"実行失敗: ステップ{step_index}はフィルタステップではありません。"
                    f"フィルタ設定は'filter'タイプのステップでのみ利用可能です。"
                )

            try:
                filter_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"フィルタ設定中にエラーが発生しました: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            state = AnalysisState(self.db, self.session_id)
            result_overview = await state.set_config(step_index, filter_json)

            logger.info(
                "set_filter_tool_success",
                session_id=str(self.session_id),
                step_index=step_index,
            )

            return f"ステップ{step_index}にフィルタ設定を適用しました。\n{result_overview}"

        except Exception as e:
            logger.error(
                "set_filter_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: フィルタ設定中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")
