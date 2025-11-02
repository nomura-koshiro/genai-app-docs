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
    >>> from app.schemas.project import ProjectCreate, ProjectMemberCreate
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

from app.models.project_member import ProjectRole


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

class ProjectMemberBase(BaseModel):
    """ベースプロジェクトメンバースキーマ。

    プロジェクトメンバーの基本情報を定義します。

    Attributes:
        role (ProjectRole): プロジェクトロール（owner/admin/member/viewer）
    """

    role: ProjectRole = Field(..., description="プロジェクトロール（owner/admin/member/viewer）")

class ProjectFileBase(BaseModel):
    """ベースプロジェクトファイルスキーマ。

    プロジェクトファイルの基本情報を定義します。

    Attributes:
        filename (str): 保存ファイル名
        original_filename (str): 元のファイル名
        file_size (int): ファイルサイズ（バイト）
        mime_type (str | None): MIMEタイプ
    """

    filename: str = Field(..., max_length=255, description="保存ファイル名")
    original_filename: str = Field(..., max_length=255, description="元のファイル名")
    file_size: int = Field(..., gt=0, description="ファイルサイズ（バイト）")
    mime_type: str | None = Field(None, max_length=100, description="MIMEタイプ")

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


# ================================================================================
# プロジェクトメンバースキーマ
# ================================================================================

class ProjectMemberResponse(ProjectMemberBase):
    """プロジェクトメンバー情報レスポンススキーマ。

    APIレスポンスでメンバー情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): メンバーシップID（UUID）
        project_id (uuid.UUID): プロジェクトID
        user_id (uuid.UUID): ユーザーID
        role (ProjectRole): プロジェクトロール（ProjectMemberBaseから継承）
        joined_at (datetime): 参加日時
        added_by (uuid.UUID | None): 追加者のユーザーID

    Example:
        >>> from datetime import UTC
        >>> member = ProjectMemberResponse(
        ...     id=uuid.uuid4(),
        ...     project_id=uuid.uuid4(),
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.MEMBER,
        ...     joined_at=datetime.now(UTC),
        ...     added_by=uuid.uuid4()
        ... )

    Note:
        - from_attributesを有効にしているため、ORMモデルから直接変換可能です
    """

    id: uuid.UUID = Field(..., description="メンバーシップID（UUID）")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    user_id: uuid.UUID = Field(..., description="ユーザーID")
    joined_at: datetime = Field(..., description="参加日時")
    added_by: uuid.UUID | None = Field(None, description="追加者のユーザーID")

    model_config = ConfigDict(from_attributes=True)


# ================================================================================
# プロジェクトファイルスキーマ
# ================================================================================

class ProjectFileResponse(ProjectFileBase):
    """プロジェクトファイル情報レスポンススキーマ。

    APIレスポンスでファイル情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): ファイルID（UUID）
        project_id (uuid.UUID): プロジェクトID
        filename (str): 保存ファイル名（ProjectFileBaseから継承）
        original_filename (str): 元のファイル名（ProjectFileBaseから継承）
        file_path (str): ファイルパス（Azure Blob Storage等）
        file_size (int): ファイルサイズ（ProjectFileBaseから継承）
        mime_type (str | None): MIMEタイプ（ProjectFileBaseから継承）
        uploaded_by (uuid.UUID): アップロード者のユーザーID
        uploaded_at (datetime): アップロード日時

    Example:
        >>> from datetime import UTC
        >>> file = ProjectFileResponse(
        ...     id=uuid.uuid4(),
        ...     project_id=uuid.uuid4(),
        ...     filename="document_abc123.pdf",
        ...     original_filename="important-document.pdf",
        ...     file_path="projects/proj-001/document_abc123.pdf",
        ...     file_size=1024000,
        ...     mime_type="application/pdf",
        ...     uploaded_by=uuid.uuid4(),
        ...     uploaded_at=datetime.now(UTC)
        ... )

    Note:
        - from_attributesを有効にしているため、ORMモデルから直接変換可能です
    """

    id: uuid.UUID = Field(..., description="ファイルID（UUID）")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    file_path: str = Field(..., max_length=512, description="ファイルパス（Azure Blob Storage等）")
    uploaded_by: uuid.UUID = Field(..., description="アップロード者のユーザーID")
    uploaded_at: datetime = Field(..., description="アップロード日時")

    model_config = ConfigDict(from_attributes=True)

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

class ProjectMemberCreate(ProjectMemberBase):
    """プロジェクトメンバー追加リクエストスキーマ。

    プロジェクトに新しいメンバーを追加する際に使用します。

    Attributes:
        user_id (uuid.UUID): 追加するユーザーのID
        role (ProjectRole): プロジェクトロール（ProjectMemberBaseから継承）

    Example:
        >>> member = ProjectMemberCreate(
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.MEMBER
        ... )
    """

    user_id: uuid.UUID = Field(..., description="追加するユーザーのID")

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

    name: str | None = Field(None, max_length=255, description="プロジェクト名")
    description: str | None = Field(None, description="プロジェクト説明")
    is_active: bool | None = Field(None, description="アクティブフラグ")

class ProjectMemberUpdate(BaseModel):
    """プロジェクトメンバー更新リクエストスキーマ。

    メンバーのロールを更新する際に使用します。

    Attributes:
        role (ProjectRole): 新しいプロジェクトロール

    Example:
        >>> update = ProjectMemberUpdate(role=ProjectRole.ADMIN)
    """

    role: ProjectRole = Field(..., description="新しいプロジェクトロール")
