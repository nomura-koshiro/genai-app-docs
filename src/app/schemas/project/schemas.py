"""プロジェクト管理のPydanticスキーマ。

このモジュールは、プロジェクト、メンバーシップ、ファイル管理の
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    プロジェクト:
        - ProjectBase: 基本プロジェクト情報
        - ProjectCreate: プロジェクト作成リクエスト
        - ProjectUpdate: プロジェクト更新リクエスト
        - ProjectResponse: プロジェクト情報レスポンス

    プロジェクトメンバー:
        - ProjectMemberBase: 基本メンバー情報
        - ProjectMemberCreate: メンバー追加リクエスト
        - ProjectMemberUpdate: メンバー更新リクエスト
        - ProjectMemberResponse: メンバー情報レスポンス

    プロジェクトファイル:
        - ProjectFileBase: 基本ファイル情報
        - ProjectFileResponse: ファイル情報レスポンス

使用方法:
    >>> from app.schemas.project.schemas import ProjectCreate
    >>> from app.schemas.project.member import ProjectMemberCreate
    >>>
    >>> # プロジェクト作成
    >>> project = ProjectCreate(
    ...     name="AI Project",
    ...     code="AI-001",
    ...     description="AI development project"
    ... )
    >>>
    >>> # メンバー追加
    >>> member = ProjectMemberCreate(
    ...     user_id=uuid.uuid4(),
    ...     role="member"
    ... )
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ================================================================================
# プロジェクトスキーマ
# ================================================================================


class ProjectBase(BaseModel):
    """ベースプロジェクトスキーマ。

    プロジェクトの基本情報を定義します。

    Attributes:
        name (str): プロジェクト名（最大255文字）
        code (str): プロジェクトコード（最大50文字、一意）
        description (str | None): プロジェクト説明
    """

    name: str = Field(..., min_length=1, max_length=255, description="プロジェクト名")
    code: str = Field(..., min_length=1, max_length=50, description="プロジェクトコード（一意識別子）")
    description: str | None = Field(None, description="プロジェクト説明")


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


class ProjectUpdate(BaseModel):
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


class ProjectResponse(ProjectBase):
    """プロジェクト情報レスポンススキーマ。

    APIレスポンスでプロジェクト情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): プロジェクトID（UUID）
        name (str): プロジェクト名（ProjectBaseから継承）
        code (str): プロジェクトコード（ProjectBaseから継承）
        description (str | None): プロジェクト説明（ProjectBaseから継承）
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
    is_active: bool = Field(..., description="アクティブフラグ")
    created_by: uuid.UUID | None = Field(None, description="作成者のユーザーID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    model_config = ConfigDict(from_attributes=True)
