"""分析設定管理サービス。

このモジュールは、検証設定の取得、ダミーデータの管理などの
設定関連のビジネスロジックを提供します。

主な機能:
    - 検証設定（validation.yml）の取得
    - ダミーチャートデータの取得
"""

import json
from pathlib import Path

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.schemas.analysis_session import DummyDataResponse, ValidationConfigResponse

logger = get_logger(__name__)


class AnalysisConfigService:
    """分析設定管理サービスクラス。

    このサービスは、検証設定の取得、ダミーデータ管理などの
    設定関連の操作を提供します。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
    """

    def __init__(self, db: AsyncSession):
        """分析設定サービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db

    @measure_performance
    @async_timeout(10.0)
    async def get_validation_config(self) -> ValidationConfigResponse:
        """検証設定を取得します。

        このメソッドは、validation.ymlファイルから検証設定を読み込みます。

        Returns:
            ValidationConfigResponse: 検証設定
                - validation_config: 検証設定の全体

        Example:
            >>> config = await config_service.get_validation_config()
            >>> print(f"Policies: {config.validation_config.get('policies', [])}")
            Policies: ['市場拡大', '既存市場深耕', ...]

        Note:
            - 設定はapp/data/analysis/validation.ymlから読み込まれます
            - キャッシュは実装していません（必要に応じて追加）
        """
        logger.debug("検証設定を取得中", action="get_validation_config")

        try:
            config_path = Path(__file__).parent.parent / "data" / "analysis" / "validation.yml"

            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            logger.debug("検証設定を正常に取得しました")

            return ValidationConfigResponse(
                validation_config=config,
            )

        except Exception as e:
            logger.error(
                "検証設定の取得中にエラーが発生しました",
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                "検証設定の取得に失敗しました",
                details={"error": str(e)},
            ) from e

    @measure_performance
    @async_timeout(10.0)
    async def get_dummy_data(self, chart_type: str) -> DummyDataResponse:
        """ダミーチャートデータを取得します。

        このメソッドは、指定されたチャートタイプのダミーデータを返します。

        Args:
            chart_type (str): チャートタイプ
                - 例: "bar", "line", "pie", "scatter", など

        Returns:
            DummyDataResponse: ダミーデータレスポンス
                - formula: ダミー数式
                - input: ダミー入力データ
                - chart: ダミーチャート
                - hint: ヒント文章

        Raises:
            NotFoundError: 指定されたチャートタイプが存在しない場合
            ValidationError: ファイル読み込みエラー

        Example:
            >>> chart_data = await config_service.get_dummy_data("bar")
            >>> print(f"Hint: {chart_data.hint}")

        Note:
            - ダミーデータはapp/data/analysis/dummy/chart/配下から読み込まれます
        """
        logger.debug(
            "ダミーデータを取得中",
            chart_type=chart_type,
            action="get_dummy_data",
        )

        try:
            dummy_path = Path(__file__).parent.parent / "data" / "analysis" / "dummy" / "chart" / f"{chart_type}.json"

            if not dummy_path.exists():
                logger.warning(
                    "ダミーデータファイルが見つかりません",
                    chart_type=chart_type,
                    path=str(dummy_path),
                )
                raise NotFoundError(
                    "指定されたチャートタイプのダミーデータが存在しません",
                    details={"chart_type": chart_type},
                )

            with open(dummy_path, encoding="utf-8") as f:
                dummy_data = json.load(f)

            logger.debug(
                "ダミーデータを正常に取得しました",
                chart_type=chart_type,
            )

            return DummyDataResponse(
                formula=dummy_data.get("formula", []),
                input=dummy_data.get("input", []),
                chart=dummy_data.get("chart", []),
                hint=dummy_data.get("hint", ""),
            )

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ダミーデータの取得中にエラーが発生しました",
                chart_type=chart_type,
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                "ダミーデータの取得に失敗しました",
                details={"chart_type": chart_type, "error": str(e)},
            ) from e
