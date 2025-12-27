"""分析課題マスタのスキーマ。"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class AnalysisIssueBase(BaseCamelCaseModel):
    """課題マスタ基本スキーマ。"""

    validation_id: uuid.UUID = Field(..., description="検証マスタID")
    name: str = Field(..., max_length=255, description="課題名")
    description: str | None = Field(default=None, description="説明")
    agent_prompt: str | None = Field(default=None, description="エージェントプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    dummy_hint: str | None = Field(default=None, description="ダミーヒント")
    issue_order: int = Field(..., description="表示順序")


class AnalysisIssueCreate(AnalysisIssueBase):
    """課題マスタ作成スキーマ。"""

    pass


class AnalysisIssueUpdate(BaseCamelCaseModel):
    """課題マスタ更新スキーマ。"""

    validation_id: uuid.UUID | None = Field(default=None, description="検証マスタID")
    name: str | None = Field(default=None, max_length=255, description="課題名")
    description: str | None = Field(default=None, description="説明")
    agent_prompt: str | None = Field(default=None, description="エージェントプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    dummy_hint: str | None = Field(default=None, description="ダミーヒント")
    issue_order: int | None = Field(default=None, description="表示順序")


class AnalysisIssueResponse(BaseCamelCaseORMModel):
    """課題マスタレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="ID")
    validation_id: uuid.UUID = Field(..., description="検証マスタID")
    name: str = Field(..., description="課題名")
    description: str | None = Field(default=None, description="説明")
    agent_prompt: str | None = Field(default=None, description="エージェントプロンプト")
    initial_msg: str | None = Field(default=None, description="初期メッセージ")
    dummy_hint: str | None = Field(default=None, description="ダミーヒント")
    issue_order: int = Field(..., description="表示順序")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnalysisIssueListResponse(BaseCamelCaseModel):
    """課題マスタ一覧レスポンススキーマ。"""

    issues: list[AnalysisIssueResponse] = Field(..., description="課題マスタリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")
