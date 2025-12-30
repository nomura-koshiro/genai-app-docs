"""ドライバーツリーカテゴリマスタのスキーマ。"""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class DriverTreeCategoryBase(BaseCamelCaseModel):
    """カテゴリ基本スキーマ。"""

    category_id: int = Field(..., description="業界分類ID")
    category_name: str = Field(..., max_length=255, description="業界分類名")
    industry_id: int = Field(..., description="業界名ID")
    industry_name: str = Field(..., max_length=255, description="業界名")
    driver_type_id: int = Field(..., description="ドライバー型ID")
    driver_type: str = Field(..., max_length=255, description="ドライバー型")


class DriverTreeCategoryCreate(DriverTreeCategoryBase):
    """カテゴリ作成スキーマ。"""

    pass


class DriverTreeCategoryUpdate(BaseCamelCaseModel):
    """カテゴリ更新スキーマ。"""

    category_id: int | None = Field(default=None, description="業界分類ID")
    category_name: str | None = Field(default=None, max_length=255, description="業界分類名")
    industry_id: int | None = Field(default=None, description="業界名ID")
    industry_name: str | None = Field(default=None, max_length=255, description="業界名")
    driver_type_id: int | None = Field(default=None, description="ドライバー型ID")
    driver_type: str | None = Field(default=None, max_length=255, description="ドライバー型")


class DriverTreeCategoryResponse(BaseCamelCaseORMModel):
    """カテゴリレスポンススキーマ。"""

    id: int = Field(..., description="ID")
    category_id: int = Field(..., description="業界分類ID")
    category_name: str = Field(..., description="業界分類名")
    industry_id: int = Field(..., description="業界名ID")
    industry_name: str = Field(..., description="業界名")
    driver_type_id: int = Field(..., description="ドライバー型ID")
    driver_type: str = Field(..., description="ドライバー型")
    formula_count: int = Field(default=0, description="関連数式数")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class DriverTreeCategoryListResponse(BaseCamelCaseModel):
    """カテゴリ一覧レスポンススキーマ。"""

    categories: list[DriverTreeCategoryResponse] = Field(..., description="カテゴリリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")
