"""ダミーチャートマスタ管理用スキーマ。"""

from pydantic import Field

from app.schemas.analysis.analysis_template import AnalysisDummyChartResponse
from app.schemas.base import BaseCamelCaseModel


class AnalysisDummyChartListResponse(BaseCamelCaseModel):
    """ダミーチャートマスタ一覧レスポンス。

    Attributes:
        charts: ダミーチャートマスタリスト
        total: 総件数
        skip: スキップ数
        limit: 取得件数
    """

    charts: list[AnalysisDummyChartResponse] = Field(default_factory=list, description="ダミーチャートマスタリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(default=0, description="スキップ数")
    limit: int = Field(default=100, description="取得件数")
