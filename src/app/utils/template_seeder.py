"""分析テンプレートデータのシード処理。

このモジュールは、validation.ymlとdummy/chart/*.jsonファイルから
データを読み込み、データベースにインポートする機能を提供します。

主な機能:
    - validation.ymlのパース
    - dummy/chart/*.jsonのパース
    - データベースへのバルクインサート
    - 既存データの更新・削除処理

使用例:
    >>> from app.utils.template_seeder import TemplateSeeder
    >>> from app.core.database import get_db
    >>>
    >>> async for db in get_db():
    ...     seeder = TemplateSeeder(db)
    ...     await seeder.seed_all()
"""

import json
from pathlib import Path
from typing import Any

import structlog
import yaml
from sqlalchemy import delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AnalysisDummyChartMaster,
    AnalysisDummyFormulaMaster,
    AnalysisGraphAxisMaster,
    AnalysisIssueMaster,
    AnalysisValidationMaster,
)

logger = structlog.get_logger(__name__)


class TemplateSeeder:
    """分析テンプレートのシード処理クラス。

    validation.ymlと dummy/chart/*.json からデータを読み込み、
    データベースにインポートします。

    Attributes:
        db (AsyncSession): データベースセッション
        base_dir (Path): データファイルのベースディレクトリ
        validation_file (Path): validation.yml のパス
        chart_dir (Path): dummy/chart ディレクトリのパス
    """

    def __init__(
        self,
        db: AsyncSession,
        base_dir: Path | None = None,
    ) -> None:
        """TemplateSeederを初期化します。

        Args:
            db (AsyncSession): データベースセッション
            base_dir (Path | None): データファイルのベースディレクトリ。
                指定しない場合はデフォルトパスを使用。
        """
        self.db = db
        self.base_dir = base_dir or Path(__file__).parent.parent / "data" / "analysis"
        self.validation_file = self.base_dir / "validation.yml"
        self.chart_dir = self.base_dir / "dummy" / "chart"

    async def seed_all(self, clear_existing: bool = True) -> dict[str, int]:
        """すべてのテンプレートデータをシードします。

        Args:
            clear_existing (bool): 既存データを削除するか（デフォルト: True）

        Returns:
            dict[str, int]: インポート結果の統計
                - validations_created: 作成された施策数
                - issues_created: 作成された課題数
                - charts_created: 作成されたチャート数
                - validations_deleted: 削除された施策数

        Raises:
            FileNotFoundError: validation.yml または chart ディレクトリが見つからない場合
            ValueError: YAMLファイルのパースエラー

        Example:
            >>> seeder = TemplateSeeder(db)
            >>> result = await seeder.seed_all()
            >>> print(f"Created {result['issues_created']} issues")
        """
        logger.info("テンプレートシーディングを開始します", base_dir=str(self.base_dir))

        result = {
            "validations_created": 0,
            "issues_created": 0,
            "charts_created": 0,
            "axes_created": 0,
            "formulas_created": 0,
            "validations_deleted": 0,
        }

        # 既存データの削除
        if clear_existing:
            deleted_counts = await self._clear_existing_data()
            result["validations_deleted"] = deleted_counts["validations"]

        # validation.yml の読み込み
        templates_data = self._parse_validation_yaml()
        logger.info("validation.ymlをパースしました", template_count=len(templates_data))

        # チャートデータの読み込み
        charts_data = self._parse_chart_jsons()
        logger.info("チャートJSONをパースしました", chart_count=len(charts_data))

        # 施策ごとにグループ化
        validation_groups: dict[str, list[dict[str, Any]]] = {}
        for template in templates_data:
            policy = template["policy"]
            if policy not in validation_groups:
                validation_groups[policy] = []
            validation_groups[policy].append(template)

        # 施策と課題の作成
        for validation_order, (policy, issues) in enumerate(validation_groups.items()):
            validation = await self._create_validation(policy, validation_order)
            result["validations_created"] += 1

            for issue_order, issue_data in enumerate(issues):
                issue = await self._create_issue(validation.id, issue_data, issue_order)
                result["issues_created"] += 1

                # 初期軸設定の作成
                for axis_order, axis_data in enumerate(issue_data.get("initial_axis", [])):
                    await self._create_graph_axis(issue.id, axis_data, axis_order)
                    result["axes_created"] += 1

                # ダミー計算式の作成
                dummy = issue_data.get("dummy", {})
                formulas = dummy.get("formula", [])
                if isinstance(formulas, list):
                    for formula_order, formula_data in enumerate(formulas):
                        await self._create_dummy_formula(issue.id, formula_data, formula_order)
                        result["formulas_created"] += 1

                # ダミーチャートの作成
                chart_names = dummy.get("chart", [])
                for chart_order, chart_name in enumerate(chart_names):
                    chart_data = charts_data.get(chart_name)
                    if chart_data:
                        await self._create_dummy_chart(issue.id, chart_data, chart_order)
                        result["charts_created"] += 1
                    else:
                        logger.warning(
                            "チャートファイルが見つかりません",
                            chart_name=chart_name,
                            policy=policy,
                            issue=issue_data["issue"],
                        )

        await self.db.commit()

        logger.info(
            "テンプレートシーディングが完了しました",
            validations_created=result["validations_created"],
            issues_created=result["issues_created"],
            charts_created=result["charts_created"],
            validations_deleted=result["validations_deleted"],
        )

        return result

    async def _clear_existing_data(self) -> dict[str, int]:
        """既存のテンプレートデータを削除します。

        Returns:
            dict[str, int]: 削除された件数
                - validations: 削除された施策数（課題等もCASCADE削除）
        """
        # 施策を削除（課題、軸、計算式、チャートもCASCADE削除される）
        result: Result[Any] = await self.db.execute(delete(AnalysisValidationMaster))
        validations_deleted = result.rowcount or 0  # type: ignore[attr-defined]

        logger.info("既存のテンプレートを削除しました", count=validations_deleted)

        return {"validations": validations_deleted}

    def _parse_validation_yaml(self) -> list[dict[str, Any]]:
        """validation.yml をパースします。

        Returns:
            list[dict[str, Any]]: パースされたテンプレートデータのリスト

        Raises:
            FileNotFoundError: validation.yml が見つからない場合
            ValueError: YAMLパースエラー
        """
        if not self.validation_file.exists():
            raise FileNotFoundError(f"validation.ymlが見つかりません: {self.validation_file}")

        with open(self.validation_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"validation.ymlの形式が無効です: 辞書型を期待しましたが、{type(data)}が見つかりました")

        templates = []

        for policy, issues in data.items():
            if not isinstance(issues, dict):
                logger.warning("不正な施策フォーマットです", policy=policy)
                continue

            for issue, config in issues.items():
                if not isinstance(config, dict):
                    logger.warning("不正な課題フォーマットです", policy=policy, issue=issue)
                    continue

                templates.append(
                    {
                        "policy": policy,
                        "issue": issue,
                        "description": config.get("description", ""),
                        "agent_prompt": config.get("agent_prompt", ""),
                        "initial_msg": config.get("initial_msg", ""),
                        "initial_axis": config.get("initial_axis", []),
                        "dummy": config.get("dummy", {}),
                    }
                )

        return templates

    def _parse_chart_jsons(self) -> dict[str, dict[str, Any]]:
        """dummy/chart/*.json をパースします。

        Returns:
            dict[str, dict[str, Any]]: チャート名をキーとしたチャートデータの辞書

        Raises:
            FileNotFoundError: chart ディレクトリが見つからない場合
        """
        if not self.chart_dir.exists():
            raise FileNotFoundError(f"チャートディレクトリが見つかりません: {self.chart_dir}")

        charts = {}

        for json_file in self.chart_dir.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    chart_data = json.load(f)

                charts[json_file.name] = chart_data

            except json.JSONDecodeError as e:
                logger.warning("チャートJSONのパースに失敗しました", file=json_file.name, error=str(e))

        return charts

    async def _create_validation(
        self,
        name: str,
        validation_order: int,
    ) -> AnalysisValidationMaster:
        """施策をデータベースに作成します。

        Args:
            name (str): 施策名
            validation_order (int): 表示順序

        Returns:
            AnalysisValidationMaster: 作成された施策
        """
        validation = AnalysisValidationMaster(
            name=name,
            validation_order=validation_order,
        )

        self.db.add(validation)
        await self.db.flush()

        return validation

    async def _create_issue(
        self,
        validation_id: Any,
        issue_data: dict[str, Any],
        issue_order: int,
    ) -> AnalysisIssueMaster:
        """課題をデータベースに作成します。

        Args:
            validation_id (Any): 施策ID
            issue_data (dict[str, Any]): 課題データ
            issue_order (int): 表示順序

        Returns:
            AnalysisIssueMaster: 作成された課題
        """
        dummy = issue_data.get("dummy", {})

        # dummy_inputをバイナリに変換
        dummy_input_data = dummy.get("input")
        dummy_input_bytes = None
        if dummy_input_data:
            dummy_input_bytes = json.dumps(dummy_input_data, ensure_ascii=False).encode("utf-8")

        issue = AnalysisIssueMaster(
            validation_id=validation_id,
            name=issue_data["issue"],
            description=issue_data.get("description"),
            agent_prompt=issue_data.get("agent_prompt"),
            initial_msg=issue_data.get("initial_msg"),
            dummy_hint=dummy.get("hint"),
            dummy_input=dummy_input_bytes,
            issue_order=issue_order,
        )

        self.db.add(issue)
        await self.db.flush()

        return issue

    async def _create_graph_axis(
        self,
        issue_id: Any,
        axis_data: dict[str, Any],
        axis_order: int,
    ) -> AnalysisGraphAxisMaster:
        """グラフ軸設定をデータベースに作成します。

        Args:
            issue_id (Any): 課題ID
            axis_data (dict[str, Any]): 軸データ
            axis_order (int): 表示順序

        Returns:
            AnalysisGraphAxisMaster: 作成されたグラフ軸設定
        """
        # optionをJSON文字列に変換
        option_data = axis_data.get("option", [])
        option_str = json.dumps(option_data, ensure_ascii=False) if isinstance(option_data, list) else str(option_data)

        axis = AnalysisGraphAxisMaster(
            issue_id=issue_id,
            name=axis_data.get("name", ""),
            axis_order=axis_order,
            option=option_str,
            multiple=axis_data.get("multiple", False),
        )

        self.db.add(axis)
        await self.db.flush()

        return axis

    async def _create_dummy_formula(
        self,
        issue_id: Any,
        formula_data: dict[str, Any],
        formula_order: int,
    ) -> AnalysisDummyFormulaMaster:
        """ダミー計算式をデータベースに作成します。

        Args:
            issue_id (Any): 課題ID
            formula_data (dict[str, Any]): 計算式データ
            formula_order (int): 表示順序

        Returns:
            AnalysisDummyFormulaMaster: 作成されたダミー計算式
        """
        formula = AnalysisDummyFormulaMaster(
            issue_id=issue_id,
            name=formula_data.get("name", ""),
            formula_order=formula_order,
            value=formula_data.get("value", ""),
        )

        self.db.add(formula)
        await self.db.flush()

        return formula

    async def _create_dummy_chart(
        self,
        issue_id: Any,
        chart_data: dict[str, Any],
        chart_order: int,
    ) -> AnalysisDummyChartMaster:
        """ダミーチャートをデータベースに作成します。

        Args:
            issue_id (Any): 課題ID
            chart_data (dict[str, Any]): Plotlyチャートデータ
            chart_order (int): チャート表示順序

        Returns:
            AnalysisDummyChartMaster: 作成されたダミーチャート
        """
        # チャートデータをバイナリに変換
        chart_bytes = json.dumps(chart_data, ensure_ascii=False).encode("utf-8")

        chart = AnalysisDummyChartMaster(
            issue_id=issue_id,
            chart=chart_bytes,
            chart_order=chart_order,
        )

        self.db.add(chart)
        await self.db.flush()

        return chart


async def seed_templates(
    db: AsyncSession,
    base_dir: Path | None = None,
    clear_existing: bool = True,
) -> dict[str, int]:
    """分析テンプレートデータをシードする便利関数。

    Args:
        db (AsyncSession): データベースセッション
        base_dir (Path | None): データファイルのベースディレクトリ
        clear_existing (bool): 既存データを削除するか

    Returns:
        dict[str, int]: インポート結果の統計

    Example:
        >>> from app.core.database import get_db
        >>> async for db in get_db():
        ...     result = await seed_templates(db)
        ...     print(f"Created {result['issues_created']} issues")
    """
    seeder = TemplateSeeder(db, base_dir)
    return await seeder.seed_all(clear_existing)
