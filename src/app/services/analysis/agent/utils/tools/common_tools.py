"""Common analysis agent tools.

データ概要取得、ステップ管理、データ値取得など、
全ステップタイプで共通して使用されるツールを提供します。

Tools:
    - GetDataOverviewTool: データ概要取得
    - GetStepOverviewTool: ステップ概要取得
    - AddStepTool: ステップ追加
    - DeleteStepTool: ステップ削除
    - GetDataValueTool: データ値取得
"""

import json
import uuid

from langchain.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.services.analysis.agent.state import AnalysisState

logger = get_logger(__name__)


class GetDataOverviewTool(BaseTool):
    """データ概要取得ツール。

    ロードされたデータの概要情報を取得します。
    データセットの数、各データセットの行数、列名、値の一覧などを返します。

    Attributes:
        name (str): ツール名（"get_data_overview"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetDataOverviewTool(db, session_id)
        >>> result = await tool._arun()
        >>> print(result)
        データの概要:

        データセット original:
        データ: 1000件
          地域: 東京, 大阪, 名古屋
          商品: A, B, C
    """

    name: str = "get_data_overview"
    description: str = (
        "現在のデータセットの概要を取得します。"
        "データセットの数、各データセットの行数、列名などを含みます。"
    )

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

        Args:
            input_str (str): 入力文字列（使用しない）

        Returns:
            str: データ概要のテキスト形式

        Raises:
            Exception: データ取得中にエラーが発生した場合
        """
        logger.info(
            "get_data_overview_tool_called",
            session_id=str(self.session_id),
            tool="get_data_overview",
        )

        try:
            state = AnalysisState(self.db, self.session_id)
            overview = await state.get_data_overview()
            return overview
        except Exception as e:
            logger.error(
                "get_data_overview_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class GetStepOverviewTool(BaseTool):
    """ステップ概要取得ツール。

    現在の分析ステップの概要を取得します。
    各ステップの設定、フィルタ条件、結果データの概要などを含みます。

    Attributes:
        name (str): ツール名（"get_step_overview"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetStepOverviewTool(db, session_id)
        >>> result = await tool._arun()
        >>> print(result)
        現在の分析ステップ:

        Step 0: 売上フィルタ (filter)
          - データソース: original
          - カテゴリーフィルタ: 地域: ['東京', '大阪']
    """

    name: str = "get_step_overview"
    description: str = (
        "現在の分析ステップの概要を取得します。"
        "各ステップの設定、フィルタ条件、結果データの概要などを含みます。"
    )

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

        Args:
            input_str (str): 入力文字列（使用しない）

        Returns:
            str: ステップ概要のテキスト形式

        Raises:
            Exception: ステップ取得中にエラーが発生した場合
        """
        logger.info(
            "get_step_overview_tool_called",
            session_id=str(self.session_id),
            tool="get_step_overview",
        )

        try:
            state = AnalysisState(self.db, self.session_id)
            overview = await state.get_step_overview()
            return overview
        except Exception as e:
            logger.error(
                "get_step_overview_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class AddStepTool(BaseTool):
    """ステップ追加ツール。

    新しい分析ステップを追加します。
    ステップ名、ステップタイプ、データソースを指定します。

    Attributes:
        name (str): ツール名（"add_step"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = AddStepTool(db, session_id)
        >>> result = await tool._arun("売上フィルタ, filter, original")
        >>> print(result)
        ステップインデックス: 0に、ステップ「売上フィルタ」（タイプ: filter, データソース: original）を追加しました。
    """

    name: str = "add_step"
    description: str = """
新しい分析ステップを追加します。
入力: 'step_name, step_type, data_source'
    - step_name: 日本語で分かりやすい名前（重複禁止）
    - step_type: filter/aggregate/transform/summary
    - data_source: original/step_0/step_1など
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

        新しいステップを追加します。

        Args:
            input_str (str): 'step_name, step_type, data_source' 形式の文字列
                - step_name: 追加するステップの名前
                - step_type: 'filter', 'summary', 'aggregate', 'transform' のいずれか
                - data_source: 'original', 'step_0', 'step_1', ... のいずれか

        Returns:
            str: 実行結果メッセージ

        Example:
            >>> await tool._arun("売上フィルタ, filter, original")
        """
        logger.info(
            "add_step_tool_called",
            session_id=str(self.session_id),
            input=input_str,
            tool="add_step",
        )

        try:
            parts = input_str.split(",", 2)
            if len(parts) == 3:
                step_name = parts[0].strip()
                step_type = parts[1].strip().lower()
                data_source = parts[2].strip().lower()
            else:
                return "実行失敗: 入力形式が不正です。形式: 'step_name, step_type, data_source'"

            if step_type not in ["filter", "summary", "aggregate", "transform"]:
                return (
                    f"実行失敗: ステップタイプが不正です。"
                    f"'filter', 'summary', 'aggregate', 'transform' のいずれかを指定してください。"
                    f"指定値: {step_type}"
                )

            # ステップを追加
            state = AnalysisState(self.db, self.session_id)
            await state.add_step(step_name, step_type, data_source)

            # ステップ数を取得
            from app.repositories.analysis import AnalysisStepRepository

            step_repo = AnalysisStepRepository(self.db)
            all_steps = await step_repo.list_by_session(self.session_id, is_active=True)
            step_index = len(all_steps) - 1

            # 設定例を返す
            if step_type == "filter":
                example_prompt = """
{
    "category_filter": {
        "コラム1": [コラム1の値1, コラム1の値2],
        "コラム2": [コラム2の値1, コラム2の値2]
    },
    "numeric_filter": {
        "column": "値",
        "filter_type": "range | topk | percentage",

        // rangeタイプの場合
        "enable_min": 最小値を有効にするかどうか,
        "min_value": 最小値,
        "include_min": 最小値を含むかどうか,
        "enable_max": 最大値を有効にするかどうか,
        "max_value": 最大値,
        "include_max": 最大値を含むかどうか,

        // topkタイプの場合
        "k_value": 抽出件数,
        "ascending": false(上位K件) | true(下位K件),

        // percentageタイプの場合
        "min_percentile": 下位パーセンタイル(0-100),
        "max_percentile": 上位パーセンタイル(0-100)
    },
    "table_filter": {
        "table_df": str,  # フィルタ対象のDataFrame
        "key_columns": [フィルタ対象のキーとなるカラム名1, フィルタ対象のキーとなるカラム名2],
        "exclude_mode": 除外モードかどうか,  # Trueなら除外、Falseなら包含
        "enable": テーブルフィルタを有効にするかどうか
    }
}
"""
            elif step_type == "summary":
                example_prompt = """
{
    "formula": [
        {"target_subject": "科目1", "type": 計算方法, "formula_text": 計算式の名称, "unit": 単位},
        {"target_subject": "科目2", "type": 計算方法, "formula_text": 計算式の名称, "unit": 単位},
    ]
    "chart": {
        "graph_type": "グラフの種類",
        ... (# グラフの種類に応じて様々な設定が必要です)
    },
    "table": {
        "show_source_data": ソースデータを表示するかどうか,
        "table_name": "テーブルの名称"
    }
}
"""
            elif step_type == "aggregate":
                example_prompt = """
{
    "axis": ["コラム1", "コラム2"],
    "column":[{"subject": "科目1", "method": "sum"}, {"subject": ["科目2", "科目1"], "method": "-"}]
}
"""
            elif step_type == "transform":
                example_prompt = """
{
    "operations": [
        {
            "operation_type": "add_axis | modify_axis | add_subject | modify_subject",
            "target_name": "新しい名前または変更する名前",
            "calculation": {
                "type": "constant | copy | formula | mapping",

                // constantタイプの場合
                "constant_value": 定数値,

                // copyタイプの場合
                "copy_from": "コピー元の軸名または科目名",

                // formulaタイプの場合
                "formula_type": "+ | - | * | /",
                "operands": ["軸名1", "軸名2"] または ["科目名1", "科目名2"],
                "constant_value": 定数値（定数との計算の場合）,

                // mappingタイプの場合
                "operands": ["変換元の軸名または科目名"],
                "mapping_dict": {"元の値1": "新しい値1", "元の値2": "新しい値2"}
            }
        }
    ]
}
"""
            else:
                example_prompt = ""

            msg = (
                f"ステップインデックス: {step_index}に、"
                f"ステップ「{step_name}」（タイプ: {step_type}, データソース: {data_source}）を追加しました。"
            )
            msg += f"\n\n以下の設定例を参考にして具体的なsetをしてください。 {example_prompt}"

            logger.info(
                "add_step_tool_success",
                session_id=str(self.session_id),
                step_name=step_name,
                step_type=step_type,
                step_index=step_index,
            )

            return msg

        except Exception as e:
            logger.error(
                "add_step_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: ステップの追加中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class DeleteStepTool(BaseTool):
    """ステップ削除ツール。

    指定したインデックスの分析ステップを削除します。

    Attributes:
        name (str): ツール名（"delete_step"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = DeleteStepTool(db, session_id)
        >>> result = await tool._arun("0")
        >>> print(result)
        ステップ0「売上フィルタ」を削除しました。残りステップ数: 1
    """

    name: str = "delete_step"
    description: str = "指定したインデックスの分析ステップを削除します。入力形式: 'step_index' (数値)"

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

        指定したインデックスのステップを削除します。

        Args:
            input_str (str): 'step_index' 形式の文字列
                - step_index: 削除するステップのインデックス（0から始まる整数）

        Returns:
            str: ステップ削除の結果メッセージ

        Example:
            >>> await tool._arun("0")
        """
        logger.info(
            "delete_step_tool_called",
            session_id=str(self.session_id),
            input=input_str,
            tool="delete_step",
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

            # 削除前にステップ名を取得
            step_name = all_steps[step_index].step_name

            # ステップを削除
            state = AnalysisState(self.db, self.session_id)
            await state.delete_step(step_index)

            # 残りステップ数を取得
            remaining_steps = await step_repo.list_by_session(
                self.session_id, is_active=True
            )

            logger.info(
                "delete_step_tool_success",
                session_id=str(self.session_id),
                step_index=step_index,
                step_name=step_name,
            )

            return f"ステップ{step_index}「{step_name}」を削除しました。残りステップ数: {len(remaining_steps)}"

        except Exception as e:
            logger.error(
                "delete_step_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: ステップの削除中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class GetDataValueTool(BaseTool):
    """データ値取得ツール。

    指定したステップの入力データから特定の軸・科目の組み合わせに対応する値を取得します。

    Attributes:
        name (str): ツール名（"get_data_value"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetDataValueTool(db, session_id)
        >>> filter_json = '{"科目": "利益", "地域": "日本", "製品": "自動車部品"}'
        >>> result = await tool._arun(f"0, {filter_json}")
        >>> print(result)
        ステップ0の入力データで条件 (科目='利益', 地域='日本', 製品='自動車部品') に該当する値: 1234567
    """

    name: str = "get_data_value"
    description: str = (
        '指定したステップの入力データから特定の軸・科目の組み合わせに対応する値を取得します。'
        '入力形式: \'step_index, filter_json\' (例: \'0, {{"科目": "利益", "地域": "日本", "製品": "自動車部品"}}\')'
    )

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

        指定したステップの入力データから特定の軸・科目の組み合わせに対応する値を取得します。

        Args:
            input_str (str): 'step_index, filter_json' 形式の文字列
                - step_index: ステップのインデックス（0から始まる整数）
                - filter_json: 軸・科目の組み合わせを指定するJSON文字列

        Returns:
            str: 取得した値またはエラーメッセージ

        Example:
            >>> filter_json = '{"科目": "利益", "地域": "日本"}'
            >>> await tool._arun(f"0, {filter_json}")
        """
        logger.info(
            "get_data_value_tool_called",
            session_id=str(self.session_id),
            input=input_str[:100],
            tool="get_data_value",
        )

        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "入力形式が不正です。形式: 'step_index, filter_json'"

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

            try:
                filter_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            if not isinstance(filter_json, dict):
                return "実行失敗: フィルタ条件は辞書形式で指定してください。例: {'科目': '利益', '地域': '日本'}"

            # ステップの入力データを取得
            state = AnalysisState(self.db, self.session_id)
            source_data = await state.get_source_data(step_index)

            if source_data is None or source_data.empty:
                return f"ステップ{step_index}の入力データが存在しません。"

            # フィルタ条件を適用してデータを絞り込み
            filtered_data = source_data.copy()

            for column, value in filter_json.items():
                if column not in filtered_data.columns:
                    available_columns = list(filtered_data.columns)
                    return f"指定された列 '{column}' がデータに存在しません。利用可能な列: {', '.join(available_columns)}"

                if isinstance(value, list):
                    return "実行失敗: 値は単一の値で指定してください。リスト形式はサポートされていません。"

                # 値のマッチング
                mask = filtered_data[column] == value
                if not mask.any():
                    unique_values = filtered_data[column].unique()
                    available_values = ", ".join(map(str, unique_values))
                    return (
                        f"実行失敗: 指定された値 '{value}' が列 '{column}' に存在しません。"
                        f"利用可能な値: {available_values}"
                    )

                filtered_data = filtered_data[mask]

            # 結果の確認
            if filtered_data.empty:
                return f"指定された条件 {filter_json} に一致するデータが見つかりませんでした。"

            if len(filtered_data) == 1:
                # 単一の値が見つかった場合
                value = (
                    filtered_data.iloc[0]["値"]
                    if "値" in filtered_data.columns
                    else "値列が見つかりません"
                )
                condition_str = ", ".join([f"{k}='{v}'" for k, v in filter_json.items()])
                return f"ステップ{step_index}の入力データで条件 ({condition_str}) に該当する値: {value}"

            else:
                # 複数の値が見つかった場合
                if "値" in filtered_data.columns:
                    values = filtered_data["値"].tolist()
                    condition_str = ", ".join(
                        [f"{k}='{v}'" for k, v in filter_json.items()]
                    )
                    return (
                        f"ステップ{step_index}の入力データで条件 ({condition_str}) に該当する値が"
                        f"複数見つかりました: {values} (合計{len(values)}件)"
                    )
                else:
                    return (
                        f"指定された条件に該当するデータが{len(filtered_data)}件見つかりましたが、"
                        f"値列が存在しません。"
                    )

        except Exception as e:
            logger.error(
                "get_data_value_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: データ値の取得中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")
