"""プロジェクトメンバー管理のPydanticスキーマ。

このモジュールは、プロジェクトメンバーシップ管理の
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    メンバー管理:
        - ProjectMemberCreate: メンバー追加リクエスト
        - ProjectMemberUpdate: ロール更新リクエスト
        - ProjectMemberResponse: メンバー情報レスポンス
        - ProjectMemberWithUser: ユーザー情報付きメンバーレスポンス
        - ProjectMemberListResponse: メンバー一覧レスポンス

使用方法:
    >>> from app.schemas.project_member import ProjectMemberCreate
    >>>
    >>> # メンバー追加
    >>> member_data = ProjectMemberCreate(
    ...     user_id=uuid.uuid4(),
    ...     role=ProjectRole.MEMBER
    ... )
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_member import ProjectRole
from app.schemas.user import UserResponse

# ================================================================================
# プロジェクトメンバースキーマ
# ================================================================================


class ProjectMemberCreate(BaseModel):
    """プロジェクトメンバー追加リクエストスキーマ。

    プロジェクトに新しいメンバーを追加する際に使用します。

    Attributes:
        user_id (uuid.UUID): 追加するユーザーのID
        role (ProjectRole): プロジェクトロール（デフォルト: MEMBER）

    Example:
        >>> member = ProjectMemberCreate(
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.ADMIN
        ... )

    Note:
        - OWNER ロールの追加は OWNER のみが実行可能
        - 重複するメンバーは追加できません
    """

    user_id: uuid.UUID = Field(..., description="追加するユーザーのID")
    role: ProjectRole = Field(
        default=ProjectRole.MEMBER, description="プロジェクトロール（owner/admin/member/viewer）"
    )


class ProjectMemberUpdate(BaseModel):
    """プロジェクトメンバーロール更新リクエストスキーマ。

    メンバーのロールを更新する際に使用します。

    Attributes:
        role (ProjectRole): 新しいプロジェクトロール

    Example:
        >>> update = ProjectMemberUpdate(role=ProjectRole.ADMIN)

    Note:
        - OWNER ロールの変更は OWNER のみが実行可能
        - 最後の OWNER は削除・降格できません
    """

    role: ProjectRole = Field(..., description="新しいプロジェクトロール")


class ProjectMemberResponse(BaseModel):
    """プロジェクトメンバー情報レスポンススキーマ。

    APIレスポンスでメンバー情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): メンバーシップID（UUID）
        project_id (uuid.UUID): プロジェクトID
        user_id (uuid.UUID): ユーザーID
        role (ProjectRole): プロジェクトロール
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
    role: ProjectRole = Field(..., description="プロジェクトロール（owner/admin/member/viewer）")
    joined_at: datetime = Field(..., description="参加日時")
    added_by: uuid.UUID | None = Field(None, description="追加者のユーザーID")

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberWithUser(ProjectMemberResponse):
    """ユーザー情報付きプロジェクトメンバーレスポンススキーマ。

    メンバー情報とユーザー情報を含むレスポンスに使用します。

    Attributes:
        id (uuid.UUID): メンバーシップID（ProjectMemberResponseから継承）
        project_id (uuid.UUID): プロジェクトID（ProjectMemberResponseから継承）
        user_id (uuid.UUID): ユーザーID（ProjectMemberResponseから継承）
        role (ProjectRole): プロジェクトロール（ProjectMemberResponseから継承）
        joined_at (datetime): 参加日時（ProjectMemberResponseから継承）
        added_by (uuid.UUID | None): 追加者のユーザーID（ProjectMemberResponseから継承）
        user (UserResponse | None): ユーザー情報（ネストされたオブジェクト）

    Example:
        >>> member = ProjectMemberWithUser(
        ...     id=uuid.uuid4(),
        ...     project_id=uuid.uuid4(),
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.MEMBER,
        ...     joined_at=datetime.now(UTC),
        ...     added_by=uuid.uuid4(),
        ...     user=UserResponse(...)
        ... )

    Note:
        - ユーザー情報を含むため、N+1クエリ対策が必要です
        - selectinload を使用してユーザー情報を事前ロードしてください
    """

    user: UserResponse | None = Field(None, description="ユーザー情報")


class ProjectMemberListResponse(BaseModel):
    """プロジェクトメンバー一覧レスポンススキーマ。

    メンバー一覧APIのレスポンス形式を定義します。

    Attributes:
        members (list[ProjectMemberWithUser]): メンバーリスト
        total (int): 総件数
        project_id (uuid.UUID): プロジェクトID

    Example:
        >>> response = ProjectMemberListResponse(
        ...     members=[member1, member2, member3],
        ...     total=15,
        ...     project_id=uuid.uuid4()
        ... )

    Note:
        - ページネーション情報を含みます
        - total は全体の件数
    """

    members: list[ProjectMemberWithUser] = Field(..., description="メンバーリスト")
    total: int = Field(..., description="総件数")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")


class UserRoleResponse(BaseModel):
    """ユーザーのプロジェクトロールレスポンススキーマ。

    現在のユーザーのロール情報を返す際に使用します。

    Attributes:
        project_id (uuid.UUID): プロジェクトID
        user_id (uuid.UUID): ユーザーID
        role (ProjectRole): プロジェクトロール
        is_owner (bool): OWNER ロールかどうか
        is_admin (bool): ADMIN 以上のロールかどうか

    Example:
        >>> role_info = UserRoleResponse(
        ...     project_id=uuid.uuid4(),
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.ADMIN,
        ...     is_owner=False,
        ...     is_admin=True
        ... )

    Note:
        - 権限チェックに使用されます
        - is_owner: OWNER ロールのみ True
        - is_admin: OWNER または ADMIN の場合 True
    """

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    user_id: uuid.UUID = Field(..., description="ユーザーID")
    role: ProjectRole = Field(..., description="プロジェクトロール")
    is_owner: bool = Field(..., description="OWNER ロールかどうか")
    is_admin: bool = Field(..., description="ADMIN 以上のロールかどうか")
