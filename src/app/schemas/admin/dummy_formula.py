"""ダミー数式マスタ管理用スキーマ。"""

from pydantic import Field

from app.schemas.analysis.analysis_template import AnalysisDummyFormulaResponse
from app.schemas.base import BaseCamelCaseModel


class AnalysisDummyFormulaListResponse(BaseCamelCaseModel):
    """ダミー数式マスタ一覧レスポンス。

    Attributes:
        formulas: ダミー数式マスタリスト
        total: 総件数
        skip: スキップ数
        limit: 取得件数
    """

    formulas: list[AnalysisDummyFormulaResponse] = Field(default_factory=list, description="ダミー数式マスタリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(default=0, description="スキップ数")
    limit: int = Field(default=100, description="取得件数")
