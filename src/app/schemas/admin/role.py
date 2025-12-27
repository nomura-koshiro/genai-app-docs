"""ロール関連のスキーマ定義。

システムロールおよびプロジェクトロールの一覧取得用スキーマを提供します。
"""

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


class RoleInfo(BaseCamelCaseModel):
    """ロール情報。

    Attributes:
        value: ロール値（APIで使用する値）
        label: 表示名
        description: ロールの説明
    """

    value: str = Field(..., description="ロール値")
    label: str = Field(..., description="表示名")
    description: str = Field(..., description="ロールの説明")


class SystemRoleListResponse(BaseCamelCaseModel):
    """システムロール一覧レスポンス。

    Response:
        - roles: list[RoleInfo] - システムロール一覧
    """

    roles: list[RoleInfo] = Field(default_factory=list, description="システムロール一覧")


class ProjectRoleListResponse(BaseCamelCaseModel):
    """プロジェクトロール一覧レスポンス。

    Response:
        - roles: list[RoleInfo] - プロジェクトロール一覧
    """

    roles: list[RoleInfo] = Field(default_factory=list, description="プロジェクトロール一覧")


class AllRolesResponse(BaseCamelCaseModel):
    """全ロール一覧レスポンス。

    Response:
        - system_roles: list[RoleInfo] - システムロール一覧
        - project_roles: list[RoleInfo] - プロジェクトロール一覧
    """

    system_roles: list[RoleInfo] = Field(default_factory=list, description="システムロール一覧")
    project_roles: list[RoleInfo] = Field(default_factory=list, description="プロジェクトロール一覧")
