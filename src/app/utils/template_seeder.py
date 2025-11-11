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

from app.models.analysis import AnalysisTemplate, AnalysisTemplateChart

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
                - templates_created: 作成されたテンプレート数
                - charts_created: 作成されたチャート数
                - templates_deleted: 削除されたテンプレート数
                - charts_deleted: 削除されたチャート数

        Raises:
            FileNotFoundError: validation.yml または chart ディレクトリが見つからない場合
            ValueError: YAMLファイルのパースエラー

        Example:
            >>> seeder = TemplateSeeder(db)
            >>> result = await seeder.seed_all()
            >>> print(f"Created {result['templates_created']} templates")
        """
        logger.info("template_seeding_started", base_dir=str(self.base_dir))

        result = {
            "templates_created": 0,
            "charts_created": 0,
            "templates_deleted": 0,
            "charts_deleted": 0,
        }

        # 既存データの削除
        if clear_existing:
            deleted_counts = await self._clear_existing_data()
            result["templates_deleted"] = deleted_counts["templates"]
            result["charts_deleted"] = deleted_counts["charts"]

        # validation.yml の読み込み
        templates_data = self._parse_validation_yaml()
        logger.info("validation_yaml_parsed", template_count=len(templates_data))

        # チャートデータの読み込み
        charts_data = self._parse_chart_jsons()
        logger.info("chart_jsons_parsed", chart_count=len(charts_data))

        # テンプレートとチャートの作成
        for idx, template_data in enumerate(templates_data):
            template = await self._create_template(template_data, idx)
            result["templates_created"] += 1

            # テンプレートに紐づくチャートを作成
            policy = template_data["policy"]
            issue = template_data["issue"]
            chart_names = template_data.get("dummy", {}).get("chart", [])

            for chart_idx, chart_name in enumerate(chart_names):
                chart_data = charts_data.get(chart_name)
                if chart_data:
                    await self._create_chart(template.id, chart_name, chart_data, chart_idx)
                    result["charts_created"] += 1
                else:
                    logger.warning(
                        "chart_file_not_found",
                        chart_name=chart_name,
                        policy=policy,
                        issue=issue,
                    )

        await self.db.commit()

        logger.info(
            "template_seeding_completed",
            templates_created=result["templates_created"],
            charts_created=result["charts_created"],
            templates_deleted=result["templates_deleted"],
            charts_deleted=result["charts_deleted"],
        )

        return result

    async def _clear_existing_data(self) -> dict[str, int]:
        """既存のテンプレートデータを削除します。

        Returns:
            dict[str, int]: 削除された件数
                - templates: 削除されたテンプレート数
                - charts: 削除されたチャート数（CASCADE削除）
        """
        # テンプレートを削除（チャートもCASCADE削除される）
        result: Result[Any] = await self.db.execute(delete(AnalysisTemplate))
        templates_deleted = result.rowcount or 0  # type: ignore[attr-defined]

        logger.info("existing_templates_cleared", count=templates_deleted)

        return {"templates": templates_deleted, "charts": 0}  # charts は CASCADE で削除

    def _parse_validation_yaml(self) -> list[dict[str, Any]]:
        """validation.yml をパースします。

        Returns:
            list[dict[str, Any]]: パースされたテンプレートデータのリスト

        Raises:
            FileNotFoundError: validation.yml が見つからない場合
            ValueError: YAMLパースエラー
        """
        if not self.validation_file.exists():
            raise FileNotFoundError(f"validation.yml not found: {self.validation_file}")

        with open(self.validation_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid validation.yml format: expected dict, got {type(data)}")

        templates = []

        for policy, issues in data.items():
            if not isinstance(issues, dict):
                logger.warning("invalid_policy_format", policy=policy)
                continue

            for issue, config in issues.items():
                if not isinstance(config, dict):
                    logger.warning("invalid_issue_format", policy=policy, issue=issue)
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
            raise FileNotFoundError(f"Chart directory not found: {self.chart_dir}")

        charts = {}

        for json_file in self.chart_dir.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    chart_data = json.load(f)

                charts[json_file.name] = chart_data

            except json.JSONDecodeError as e:
                logger.warning("chart_json_parse_error", file=json_file.name, error=str(e))

        return charts

    async def _create_template(
        self,
        template_data: dict[str, Any],
        display_order: int,
    ) -> AnalysisTemplate:
        """テンプレートをデータベースに作成します。

        Args:
            template_data (dict[str, Any]): テンプレートデータ
            display_order (int): 表示順序

        Returns:
            AnalysisTemplate: 作成されたテンプレート
        """
        dummy = template_data.get("dummy", {})

        template = AnalysisTemplate(
            policy=template_data["policy"],
            issue=template_data["issue"],
            description=template_data["description"],
            agent_prompt=template_data["agent_prompt"],
            initial_msg=template_data["initial_msg"],
            initial_axis=template_data["initial_axis"],
            dummy_formula=dummy.get("formula"),
            dummy_input=dummy.get("input"),
            dummy_hint=dummy.get("hint"),
            is_active=True,
            display_order=display_order,
        )

        self.db.add(template)
        await self.db.flush()

        return template

    async def _create_chart(
        self,
        template_id: Any,
        chart_name: str,
        chart_data: dict[str, Any],
        chart_order: int,
    ) -> AnalysisTemplateChart:
        """チャートをデータベースに作成します。

        Args:
            template_id (Any): テンプレートID
            chart_name (str): チャート名
            chart_data (dict[str, Any]): Plotlyチャートデータ
            chart_order (int): チャート表示順序

        Returns:
            AnalysisTemplateChart: 作成されたチャート
        """
        # チャートタイプの推定（dataの最初の要素のtypeから取得）
        chart_type = None
        if isinstance(chart_data.get("data"), list) and len(chart_data["data"]) > 0:
            chart_type = chart_data["data"][0].get("type")

        chart = AnalysisTemplateChart(
            template_id=template_id,
            chart_name=chart_name,
            chart_data=chart_data,
            chart_order=chart_order,
            chart_type=chart_type,
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
        ...     print(f"Created {result['templates_created']} templates")
    """
    seeder = TemplateSeeder(db, base_dir)
    return await seeder.seed_all(clear_existing)
