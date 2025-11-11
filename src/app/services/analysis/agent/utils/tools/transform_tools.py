"""Transform step tools for analysis agent.

変換ステップの設定取得・更新を行うツールを提供します。
軸や科目の追加・変更、値の変換を設定できます。

Tools:
    - GetTransformTool: 変換設定取得
    - SetTransformTool: 変換設定更新
"""

import json
import uuid

from langchain.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.services.analysis.agent.state import AnalysisState

logger = get_logger(__name__)


class GetTransformTool(BaseTool):
    """変換設定取得ツール。

    指定したステップの変換設定を取得します。

    Attributes:
        name (str): ツール名（"get_transform"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = GetTransformTool(db, session_id)
        >>> result = await tool._arun("0")
        >>> print(result)
        ステップ0の変換設定:
        変換操作:
          1. add_axis: 新しい軸 (constant)
    """

    name: str = "get_transform"
    description: str = "指定したステップの変換設定を取得します。入力形式: 'step_index' (数値)"

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

        指定したステップの変換設定を取得します。

        Args:
            input_str (str): 'step_index' 形式の文字列
                - step_index: 変換設定を取得するステップのインデックス（0から始まる整数）

        Returns:
            str: 変換設定の詳細

        Example:
            >>> await tool._arun("0")
        """
        logger.info(
            "get_transform_tool_called",
            session_id=str(self.session_id),
            input=input_str,
            tool="get_transform",
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

            if all_steps[step_index].step_type != "transform":
                return (
                    f"実行失敗: ステップ{step_index}は変換ステップではありません。"
                    f"変換設定は'transform'タイプのステップでのみ利用可能です。"
                )

            state = AnalysisState(self.db, self.session_id)
            transform_config = await state.get_config(step_index)

            result = f"ステップ{step_index}の変換設定:\n"

            operations = transform_config.get("operations", [])
            if operations:
                result += "変換操作:\n"
                for i, operation in enumerate(operations):
                    op_type = operation.get("operation_type", "unknown")
                    target_name = operation.get("target_name", "unknown")
                    calc_type = operation.get("calculation", {}).get("type", "unknown")
                    result += f"  {i + 1}. {op_type}: {target_name} ({calc_type})\n"
            else:
                result += "変換操作: 設定なし\n"

            return result

        except Exception as e:
            logger.error(
                "get_transform_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: 変換設定の取得中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")


class SetTransformTool(BaseTool):
    """変換設定ツール。

    指定したステップに変換設定を適用します。
    軸や科目の追加・変更、値の変換を設定します。

    Attributes:
        name (str): ツール名（"set_transform"）
        description (str): ツールの説明
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID

    Example:
        >>> tool = SetTransformTool(db, session_id)
        >>> transform_json = (
        ...     '{"operations": [{"operation_type": "add_axis", '
        ...     '"target_name": "カテゴリ", "calculation": '
        ...     '{"type": "constant", "constant_value": "A"}}]}'
        ... )
        >>> result = await tool._arun(f"0, {transform_json}")
        >>> print(result)
        ステップ0に変換設定を適用しました。
    """

    name: str = "set_transform"
    description: str = """
指定したステップに変換設定を適用します。
入力形式: 'step_index, transform_json' (transform_jsonは変換設定のJSON)
transform_jsonは以下の変換操作を設定できます:
    - 操作の種類: 'operation_type'で以下の4つから選択します:
            - 'add_axis': 新しい軸を追加
            - 'modify_axis': 既存の軸を変更
            - 'add_subject': 新しい科目を追加
            - 'modify_subject': 既存の科目を変更
        - 計算方法: 'calculation'で以下の4つのタイプから選択します:
            **■ 定数設定(type: "constant")**: 固定値を設定
                - constant_value: 設定する定数値
                - 例: 新しい軸「カテゴリ」に「A」を設定する場合
            **■ コピー(type: "copy")**: 他の軸や科目の値をコピー
                - copy_from: コピー元の軸名または科目名
                - 例: 「地域」軸をコピーして「地域グループ」軸を作成する場合
            **■ 計算式(type: "formula")**: 四則演算による計算
                - formula_type: "+", "-", "*", "/"のいずれか
                - operands: 計算に使用する軸名または科目名のリスト
                  (constant_valueを使わない場合は2つの要素、
                  constant_valueを使う場合は1つの要素)
                - constant_value: 定数との計算の場合に指定
                  (constant_valueが指定された場合はoperands[1]の代わりとして
                  計算式に入れられる)
                - 例: 「売上」+「利益」=「合計収益」を作成する場合
            **■ 値変換(type: "mapping")**: 値のマッピング変換
                - operands: 変換元の軸名または科目名のリスト(1つ)
                - mapping_dict: 変換辞書 (辞書の要素は "元の値": "新しい値" です)
                - 例: 地域コード("JP", "US")を地域名("日本", "アメリカ")に変換する場合
        - 複数の変換操作を同時に設定することが可能で、
          前の操作で作成された軸や科目を次の操作で参照できます。
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

        指定したステップの変換configに書き込みます。

        Args:
            input_str (str): 'step_index, transform_config' 形式の文字列
                - step_index: ステップのインデックス（0から始まる整数）
                - transform_config: configのJSON文字列

        Returns:
            str: 実行結果の詳細

        Example:
            >>> transform_json = (
            ...     '{"operations": [{"operation_type": "add_axis", '
            ...     '"target_name": "カテゴリ", "calculation": '
            ...     '{"type": "constant", "constant_value": "A"}}]}'
            ... )
            >>> await tool._arun(f"0, {transform_json}")
        """
        logger.info(
            "set_transform_tool_called",
            session_id=str(self.session_id),
            input=input_str[:100],
            tool="set_transform",
        )

        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, transform_json'"

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

            if all_steps[step_index].step_type != "transform":
                return (
                    f"実行失敗: ステップ{step_index}は変換ステップではありません。"
                    f"変換設定は'transform'タイプのステップでのみ利用可能です。"
                )

            try:
                transform_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: 変換設定中にエラーが発生しました: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            state = AnalysisState(self.db, self.session_id)
            result_overview = await state.set_config(step_index, transform_json)

            logger.info(
                "set_transform_tool_success",
                session_id=str(self.session_id),
                step_index=step_index,
            )

            return f"ステップ{step_index}に変換設定を適用しました。\n{result_overview}"

        except Exception as e:
            logger.error(
                "set_transform_tool_error",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            return f"実行失敗: 変換設定中にエラーが発生しました: {str(e)}"

    def _run(self, input_str: str = "") -> str:
        """同期実行（サポートなし）。

        Raises:
            NotImplementedError: 同期実行はサポートされません
        """
        raise NotImplementedError("Use async version (_arun)")
