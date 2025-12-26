"""プロジェクト本体のPydanticスキーマ。

このモジュールは、プロジェクト本体のリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    - ProjectBase: 基本プロジェクト情報
    - ProjectCreate: プロジェクト作成リクエスト
    - ProjectUpdate: プロジェクト更新リクエスト
    - ProjectResponse: プロジェクト情報レスポンス

関連モジュール:
    - app.schemas.project.member: プロジェクトメンバー関連スキーマ
    - app.schemas.project.file: プロジェクトファイル関連スキーマ

使用方法:
    >>> from app.schemas.project.project import ProjectCreate
    >>>
    >>> # プロジェクト作成
    >>> project = ProjectCreate(
    ...     name="AI Project",
    ...     code="AI-001",
    ...     description="AI development project"
    ... )
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# プロジェクトスキーマ
# ================================================================================


class ProjectBase(BaseCamelCaseModel):
    """ベースプロジェクトスキーマ。

    プロジェクトの基本情報を定義します。

    Attributes:
        name (str): プロジェクト名（最大255文字）
        code (str): プロジェクトコード（最大50文字、一意）
        description (str | None): プロジェクト説明
    """

    name: str = Field(..., min_length=1, max_length=255, description="プロジェクト名")
    code: str = Field(..., min_length=1, max_length=50, description="プロジェクトコード（一意識別子）")
    description: str | None = Field(default=None, description="プロジェクト説明")


class ProjectCreate(ProjectBase):
    """プロジェクト作成リクエストスキーマ。

    新規プロジェクト作成時に使用します。

    Attributes:
        name (str): プロジェクト名（ProjectBaseから継承）
        code (str): プロジェクトコード（ProjectBaseから継承）
        description (str | None): プロジェクト説明（ProjectBaseから継承）

    Example:
        >>> project = ProjectCreate(
        ...     name="AI Development Project",
        ...     code="AI-001",
        ...     description="Project for AI model development"
        ... )
    """

    pass


class ProjectUpdate(BaseCamelCaseModel):
    """プロジェクト更新リクエストスキーマ。

    プロジェクト情報の更新時に使用します。

    Attributes:
        name (str | None): プロジェクト名（オプション）
        description (str | None): プロジェクト説明（オプション）
        is_active (bool | None): アクティブフラグ（オプション）

    Example:
        >>> update = ProjectUpdate(
        ...     name="Updated Project Name",
        ...     description="Updated description"
        ... )

    Note:
        - すべてのフィールドはオプションです
        - code は変更できません（一意識別子のため）
    """

    name: str | None = Field(default=None, max_length=255, description="プロジェクト名")
    description: str | None = Field(default=None, description="プロジェクト説明")
    is_active: bool | None = Field(default=None, description="アクティブフラグ")


class ProjectResponse(BaseCamelCaseORMModel):
    """プロジェクト情報レスポンススキーマ。

    APIレスポンスでプロジェクト情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): プロジェクトID（UUID）
        name (str): プロジェクト名
        code (str): プロジェクトコード
        description (str | None): プロジェクト説明
        is_active (bool): アクティブフラグ
        created_by (uuid.UUID | None): 作成者のユーザーID
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時

    Example:
        >>> from datetime import UTC
        >>> project = ProjectResponse(
        ...     id=uuid.uuid4(),
        ...     name="AI Project",
        ...     code="AI-001",
        ...     description="AI development project",
        ...     is_active=True,
        ...     created_by=uuid.uuid4(),
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC)
        ... )

    Note:
        - from_attributesを有効にしているため、ORMモデルから直接変換可能です
    """

    id: uuid.UUID = Field(..., description="プロジェクトID（UUID）")
    name: str = Field(..., min_length=1, max_length=255, description="プロジェクト名")
    code: str = Field(..., min_length=1, max_length=50, description="プロジェクトコード（一意識別子）")
    description: str | None = Field(default=None, description="プロジェクト説明")
    is_active: bool = Field(..., description="アクティブフラグ")
    created_by: uuid.UUID | None = Field(default=None, description="作成者のユーザーID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class ProjectListResponse(BaseCamelCaseModel):
    """プロジェクト一覧レスポンススキーマ。

    プロジェクト一覧APIのレスポンス形式を定義します。

    Attributes:
        projects (list[ProjectResponse]): プロジェクトリスト
        total (int): 総件数
        skip (int): スキップ数（オフセット）
        limit (int): 取得件数

    Example:
        >>> response = ProjectListResponse(
        ...     projects=[project1, project2, project3],
        ...     total=100,
        ...     skip=0,
        ...     limit=10
        ... )
    """

    projects: list[ProjectResponse] = Field(..., description="プロジェクトリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数（オフセット）")
    limit: int = Field(..., description="取得件数")
