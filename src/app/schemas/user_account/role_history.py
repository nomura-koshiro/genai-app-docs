"""ロール履歴関連のPydanticスキーマ。

このモジュールは、ロール変更履歴に関連するリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    - RoleHistoryResponse: ロール履歴レスポンス
    - RoleHistoryListResponse: ロール履歴一覧レスポンス
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import RoleChangeActionEnum, RoleTypeEnum
from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class RoleHistoryResponse(BaseCamelCaseORMModel):
    """ロール履歴レスポンススキーマ。

    Attributes:
        id (uuid.UUID): 履歴ID
        user_id (uuid.UUID): 対象ユーザーID
        changed_by_id (uuid.UUID | None): 変更実行者ID
        changed_by_name (str | None): 変更実行者の表示名
        action (str): 変更アクション
        role_type (str): ロール種別
        project_id (uuid.UUID | None): プロジェクトID
        project_name (str | None): プロジェクト名
        old_roles (list[str]): 変更前ロール
        new_roles (list[str]): 変更後ロール
        reason (str | None): 変更理由
        changed_at (datetime): 変更日時
    """

    id: uuid.UUID = Field(..., description="履歴ID")
    user_id: uuid.UUID = Field(..., description="対象ユーザーID")
    changed_by_id: uuid.UUID | None = Field(default=None, description="変更実行者ID")
    changed_by_name: str | None = Field(default=None, description="変更実行者の表示名")
    action: RoleChangeActionEnum = Field(..., description="変更アクション")
    role_type: RoleTypeEnum = Field(..., description="ロール種別")
    project_id: uuid.UUID | None = Field(default=None, description="プロジェクトID")
    project_name: str | None = Field(default=None, description="プロジェクト名")
    old_roles: list[str] = Field(default_factory=list, description="変更前ロール")
    new_roles: list[str] = Field(default_factory=list, description="変更後ロール")
    reason: str | None = Field(default=None, description="変更理由")
    changed_at: datetime = Field(..., description="変更日時")


class RoleHistoryListResponse(BaseCamelCaseModel):
    """ロール履歴一覧レスポンススキーマ。

    Attributes:
        histories (list[RoleHistoryResponse]): 履歴リスト
        total (int): 総件数
        skip (int): スキップ数
        limit (int): 取得件数
    """

    histories: list[RoleHistoryResponse] = Field(default_factory=list, description="履歴リスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")
