"""分析概要生成サービス。

このモジュールは、データとステップの概要を生成する機能を提供します。

主な機能:
    - データ概要の取得（get_data_overview）
    - ステップ概要の取得（get_step_overview）

使用例:
    >>> from app.services.analysis.agent.overview_provider import AnalysisOverviewProvider
    >>>
    >>> async with get_db() as db:
    ...     overview_provider = AnalysisOverviewProvider(db, session_id)
    ...
    ...     # データ概要を取得
    ...     data_overview = await overview_provider.get_data_overview()
    ...     print(data_overview)
    ...
    ...     # ステップ概要を取得
    ...     step_overview = await overview_provider.get_step_overview()
    ...     print(step_overview)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.logging import get_logger
from app.repositories.analysis import AnalysisStepRepository
from app.services.analysis.agent.storage import AnalysisStorageService

logger = get_logger(__name__)


class AnalysisOverviewProvider:
    """分析概要生成クラス。

    データとステップの概要を生成する機能を提供します。

    Attributes:
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): セッションID
        step_repository (AnalysisStepRepository): ステップリポジトリ
        storage_service (AnalysisStorageService): ストレージサービス

    Example:
        >>> async with get_db() as db:
        ...     overview_provider = AnalysisOverviewProvider(db, session_id)
        ...     overview = await overview_provider.get_data_overview()
    """

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """分析概要生成を初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
            session_id (uuid.UUID): セッションのUUID

        Note:
            - セッションの存在確認は行わないため、呼び出し側で確認すること
        """
        self.db = db
        self.session_id = session_id
        self.step_repository = AnalysisStepRepository(db)
        self.storage_service = AnalysisStorageService()

        logger.info(
            "分析概要生成を初期化しました",
            session_id=str(session_id),
        )

    @measure_performance
    async def get_data_overview(self) -> str:
        """original_df及び全てのステップの結果データの概要を取得します。

        データ件数、カラム名と値の概要を返します。

        処理フロー:
            1. original.csvから元データを読み込み
            2. 各カラムのユニーク値を取得（「値」列を除く）
            3. 全ステップの結果データを順次読み込み
            4. 各ステップのデータ概要を生成
            5. 統合された概要文字列を返す

        Returns:
            str: データの件数と各カラムの情報
                - データセット名（original, step_0, step_1, ...）
                - データ件数
                - 各カラムのユニーク値（最大5件まで表示）

        Example:
            >>> overview = await overview_provider.get_data_overview()
            >>> print(overview)
            データの概要:

            データセット original:
            データ: 1000件
              地域: 東京, 大阪, 名古屋
              商品: A, B, C

            データセット step_0:
            データ: 500件
              地域: 東京, 大阪

            データセット step_1:
            データ: 300件
              地域: 東京

        Note:
            - original.csvが存在しない場合は「データ: なし」と表示されます
            - ステップの結果データがない場合は「データ: 未実行」と表示されます
            - データ読み込みエラーの場合は「データ: 読み込みエラー」と表示されます
            - 「値」カラムは概要に含まれません
        """
        logger.debug("データ概要を取得中", session_id=str(self.session_id))

        try:
            overview = "データの概要:\n"

            # original.csvから読み込み
            try:
                original_path = self.storage_service.generate_path(self.session_id, "original.csv")
                original_df = await self.storage_service.load_dataframe(original_path)

                overview += "\nデータセット original:\n"
                if original_df is None or original_df.empty:
                    overview += "データ: 空のデータ\n"
                else:
                    overview += f"データ: {len(original_df)}件\n"
                    for col in original_df.columns:
                        if col == "値":
                            continue
                        unique_values = original_df[col].unique()
                        overview += f"  {col}: {', '.join(map(str, unique_values))}\n"
            except Exception:
                overview += "\nデータセット original:\n"
                overview += "データ: なし\n"

            # すべてのステップの結果を取得
            all_steps = await self.step_repository.list_by_session(self.session_id, is_active=True)

            for i, step in enumerate(all_steps):
                overview += f"\nデータセット step_{i}:\n"

                if not step.result_data_path:
                    overview += "データ: 未実行\n"
                    continue

                try:
                    result_df = await self.storage_service.load_dataframe(step.result_data_path)

                    if result_df is None or result_df.empty:
                        overview += "データ: 空のデータ\n"
                    else:
                        overview += f"データ: {len(result_df)}件\n"
                        for col in result_df.columns:
                            if col == "値":
                                continue
                            unique_values = result_df[col].unique()
                            overview += f"  {col}: {', '.join(map(str, unique_values))}\n"
                except Exception as e:
                    overview += f"データ: 読み込みエラー ({str(e)})\n"

            logger.debug("データ概要を取得しました", session_id=str(self.session_id))

            return overview

        except Exception as e:
            logger.error(
                "データ概要取得中にエラーが発生しました",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_step_overview(self, index: int | None = None) -> str:
        """現在の全ての分析ステップの概要を取得します。

        各ステップの名前、タイプ、データソース、実行状態、設定内容を返します。

        処理フロー:
            1. 全ステップをDBから取得
            2. 対象ステップを選択（index指定時は1つ、None時は全て）
            3. 各ステップの基本情報を出力
            4. ステップタイプ別に設定を詳細表示
                - filter: カテゴリー、数値、テーブルフィルタ
                - aggregate: グループ化、集計方法
                - summary: 計算式、チャート、テーブル設定
                - transform: 変換操作
            5. 統合された概要文字列を返す

        Args:
            index (int | None): 特定のステップのみ取得する場合のインデックス
                - None: すべてのステップの概要
                - 0以上: 指定されたステップのみ

        Returns:
            str: ステップの概要
                - ステップ番号、名前、タイプ
                - データソース
                - 設定の詳細（フィルタ条件、集計方法など）

        Raises:
            IndexError: 以下の場合に発生
                - indexが範囲外（負の値または総ステップ数以上）

        Example:
            >>> # すべてのステップ概要
            >>> overview = await overview_provider.get_step_overview()
            >>> print(overview)
            現在の分析ステップ:

            Step 0: 売上フィルタ (filter)
              - データソース: original
              - カテゴリーフィルタ: 地域: ['東京', '大阪']
              - 数値フィルタ(範囲): 最小値 100 (含む), 最大値 1000 (含まない)
              - テーブルフィルタ: キーカラム 商品ID, モード: 包含

            Step 1: 地域別集計 (aggregate)
              - データソース: step_0
              - 集計: グループ化 地域, 商品
              - 集計方法: 売上 (sum), 数量 (count)
            >>>
            >>> # 特定のステップのみ
            >>> overview = await overview_provider.get_step_overview(index=0)
            現在の分析ステップ:

            Step 0: 売上フィルタ (filter)
              ...

        Note:
            - ステップが1つもない場合は「分析ステップは作成されていません」を返します
            - フィルタステップの数値フィルタは3種類（range, topk, percentage）に対応
            - サマリステップの計算式は最大5個まで表示されます
        """
        logger.debug("ステップ概要を取得中", session_id=str(self.session_id), index=index)

        # すべてのステップを取得
        all_steps = await self.step_repository.list_by_session(self.session_id, is_active=True)

        if not all_steps:
            return "分析ステップは作成されていません"

        overview = "現在の分析ステップ:\n\n"

        # 対象ステップを選択
        if index is not None:
            if index < 0 or index >= len(all_steps):
                raise IndexError(f"Step index out of range: {index}")
            selected_steps = [(index, all_steps[index])]
        else:
            selected_steps = list(enumerate(all_steps))

        # 各ステップの概要を生成
        for i, step in selected_steps:
            step_type = step.step_type
            step_name = step.step_name
            data_source = step.data_source

            overview += f"Step {i}: {step_name} ({step_type})\n"
            overview += f"  - データソース: {data_source}\n"

            config = step.config

            # フィルタステップ
            if step_type == "filter":
                category_filter = config.get("category_filter", {})
                overview += f"  - カテゴリーフィルタ: {', '.join([f'{k}: {v}' for k, v in category_filter.items()])}\n"

                numeric_filter = config.get("numeric_filter", {})
                filter_type = numeric_filter.get("filter_type", "range")

                if filter_type == "range":
                    enable_min = numeric_filter.get("enable_min", False)
                    enable_max = numeric_filter.get("enable_max", False)

                    if enable_min and not enable_max:
                        min_val = numeric_filter.get("min_value", 0)
                        include_text = "含む" if numeric_filter.get("include_min") else "含まない"
                        overview += f"  - 数値フィルタ(範囲): 最小値 {min_val} ({include_text})\n"
                    elif not enable_min and enable_max:
                        max_val = numeric_filter.get("max_value", 0)
                        include_text = "含む" if numeric_filter.get("include_max") else "含まない"
                        overview += f"  - 数値フィルタ(範囲): 最大値 {max_val} ({include_text})\n"
                    elif enable_min and enable_max:
                        min_val = numeric_filter.get("min_value", 0)
                        max_val = numeric_filter.get("max_value", 0)
                        min_text = "含む" if numeric_filter.get("include_min") else "含まない"
                        max_text = "含む" if numeric_filter.get("include_max") else "含まない"
                        overview += f"  - 数値フィルタ(範囲): 最小値 {min_val} ({min_text}), 最大値 {max_val} ({max_text})\n"
                    else:
                        overview += "  - 数値フィルタ(範囲): 設定なし\n"

                elif filter_type == "topk":
                    k_value = numeric_filter.get("k_value", 0)
                    if k_value > 0:
                        ascending = numeric_filter.get("ascending", False)
                        order_text = "下位" if ascending else "上位"
                        overview += f"  - 数値フィルタ(TopK): {order_text}{k_value}件を抽出\n"
                    else:
                        overview += "  - 数値フィルタ(TopK): 設定なし\n"

                elif filter_type == "percentage":
                    min_pct = numeric_filter.get("min_percentile", 0)
                    max_pct = numeric_filter.get("max_percentile", 100)
                    if min_pct > 0 or max_pct < 100:
                        overview += f"  - 数値フィルタ(パーセンタイル): {min_pct}% - {max_pct}%\n"
                    else:
                        overview += "  - 数値フィルタ(パーセンタイル): 全範囲\n"

                table_filter = config.get("table_filter", {})
                if table_filter.get("enable"):
                    key_cols = ", ".join(table_filter.get("key_columns", []))
                    mode = "除外" if table_filter.get("exclude_mode") else "包含"
                    overview += f"  - テーブルフィルタ: キーカラム {key_cols}, モード: {mode}\n"

            # 集計ステップ
            elif step_type == "aggregate":
                group_by = config.get("axis", [])
                agg_config = config.get("column", [])
                overview += f"  - 集計: グループ化 {', '.join(group_by)}\n"
                overview += f"  - 集計方法: {', '.join([f'{agg.get("subject")} ({agg.get("method")})' for agg in agg_config])}\n"

            # サマリステップ
            elif step_type == "summary":
                formulas = step.result_formula if step.result_formula else []
                overview += f"  - 計算式: {len(formulas)}個\n"
                for formula in formulas:
                    overview += f"    - {formula.get('name')}: {formula.get('result')} ({formula.get('unit')})\n"

                result_chart = step.result_chart
                chart_config = config.get("chart", {})
                if result_chart:
                    chart_type = chart_config.get("graph_type", "unknown")
                    overview += f"  - チャート設定: {chart_type}\n"
                else:
                    overview += "  - チャート設定: なし\n"

                table_config = config.get("table", {})
                if table_config:
                    show_source = table_config.get("show_source_data", False)
                    table_name = table_config.get("table_name", "N/A")
                    overview += f"  - テーブル設定: {table_name} (ソースデータ表示: {'あり' if show_source else 'なし'})\n"
                else:
                    overview += "  - テーブル設定: なし\n"

            # 変換ステップ
            elif step_type == "transform":
                transform_config = config
                operations = transform_config.get("operations", [])
                overview += f"  - 変換操作: {len(operations)}個\n"
                for j, operation in enumerate(operations):
                    op_type = operation.get("operation_type", "unknown")
                    target_name = operation.get("target_name", "unknown")
                    calc_type = operation.get("calculation", {}).get("type", "unknown")
                    overview += f"    - {j + 1}. {op_type}: {target_name} ({calc_type})\n"

        logger.debug("ステップ概要を取得しました", session_id=str(self.session_id))

        return overview
