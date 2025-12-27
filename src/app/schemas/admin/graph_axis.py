"""グラフ軸マスタ管理用スキーマ。"""

from pydantic import Field

from app.schemas.analysis.analysis_template import AnalysisGraphAxisResponse
from app.schemas.base import BaseCamelCaseModel


class AnalysisGraphAxisListResponse(BaseCamelCaseModel):
    """グラフ軸マスタ一覧レスポンス。

    Attributes:
        axes: グラフ軸マスタリスト
        total: 総件数
        skip: スキップ数
        limit: 取得件数
    """

    axes: list[AnalysisGraphAxisResponse] = Field(default_factory=list, description="グラフ軸マスタリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(default=0, description="スキップ数")
    limit: int = Field(default=100, description="取得件数")
