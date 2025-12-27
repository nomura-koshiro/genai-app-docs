"""分析検証マスタのスキーマ。"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class AnalysisValidationBase(BaseCamelCaseModel):
    """検証マスタ基本スキーマ。"""

    name: str = Field(..., max_length=255, description="検証名")
    validation_order: int = Field(..., description="表示順序")


class AnalysisValidationCreate(AnalysisValidationBase):
    """検証マスタ作成スキーマ。"""

    pass


class AnalysisValidationUpdate(BaseCamelCaseModel):
    """検証マスタ更新スキーマ。"""

    name: str | None = Field(default=None, max_length=255, description="検証名")
    validation_order: int | None = Field(default=None, description="表示順序")


class AnalysisValidationResponse(BaseCamelCaseORMModel):
    """検証マスタレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="ID")
    name: str = Field(..., description="検証名")
    validation_order: int = Field(..., description="表示順序")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnalysisValidationListResponse(BaseCamelCaseModel):
    """検証マスタ一覧レスポンススキーマ。"""

    validations: list[AnalysisValidationResponse] = Field(..., description="検証マスタリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")
