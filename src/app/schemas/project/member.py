"""プロジェクトメンバー管理のPydanticスキーマ。

このモジュールは、プロジェクトメンバーシップ管理の
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    メンバー管理:
        - ProjectMemberCreate: メンバー追加リクエスト
        - ProjectMemberUpdate: ロール更新リクエスト
        - ProjectMemberResponse: メンバー情報レスポンス
        - ProjectMemberDetailResponse: メンバー詳細レスポンス（ユーザー情報含む）
        - ProjectMemberListResponse: メンバー一覧レスポンス

使用方法:
    >>> from app.schemas.project.member import ProjectMemberCreate
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

from app.models.project.member import ProjectRole
from app.schemas.user.user import UserResponse

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
        ...     role=ProjectRole.MEMBER
        ... )

    Note:
        - PROJECT_MANAGER 権限が必要
        - 重複するメンバーは追加できません
    """

    user_id: uuid.UUID = Field(..., description="追加するユーザーのID")
    role: ProjectRole = Field(
        default=ProjectRole.MEMBER, description="プロジェクトロール（project_manager/project_moderator/member/viewer）"
    )


class ProjectMemberUpdate(BaseModel):
    """プロジェクトメンバーロール更新リクエストスキーマ。

    メンバーのロールを更新する際に使用します。

    Attributes:
        role (ProjectRole): 新しいプロジェクトロール

    Example:
        >>> update = ProjectMemberUpdate(role=ProjectRole.MEMBER)

    Note:
        - PROJECT_MANAGER 権限が必要
        - 最後の PROJECT_MANAGER は降格できません
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
    role: ProjectRole = Field(..., description="プロジェクトロール（project_manager/project_moderator/member/viewer）")
    joined_at: datetime = Field(..., description="参加日時")
    added_by: uuid.UUID | None = Field(default=None, description="追加者のユーザーID")

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberDetailResponse(ProjectMemberResponse):
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
        >>> member = ProjectMemberDetailResponse(
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

    user: UserResponse | None = Field(default=None, description="ユーザー情報")


class ProjectMemberListResponse(BaseModel):
    """プロジェクトメンバー一覧レスポンススキーマ。

    メンバー一覧APIのレスポンス形式を定義します。

    Attributes:
        members (list[ProjectMemberDetailResponse]): メンバーリスト
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

    members: list[ProjectMemberDetailResponse] = Field(..., description="メンバーリスト")
    total: int = Field(..., description="総件数")
    project_id: uuid.UUID = Field(..., description="プロジェクトID")


class UserRoleResponse(BaseModel):
    """ユーザーのプロジェクトロールレスポンススキーマ。

    現在のユーザーのロール情報を返す際に使用します。

    Attributes:
        project_id (uuid.UUID): プロジェクトID
        user_id (uuid.UUID): ユーザーID
        role (ProjectRole): プロジェクトロール
        is_owner (bool): PROJECT_MANAGER ロールかどうか（後方互換性のため維持）
        is_admin (bool): PROJECT_MANAGER ロールかどうか（後方互換性のため維持）

    Example:
        >>> role_info = UserRoleResponse(
        ...     project_id=uuid.uuid4(),
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.PROJECT_MANAGER,
        ...     is_owner=True,
        ...     is_admin=True
        ... )

    Note:
        - 権限チェックに使用されます
        - is_owner: PROJECT_MANAGER ロールの場合 True（後方互換性のため維持）
        - is_admin: PROJECT_MANAGER ロールの場合 True（後方互換性のため維持）
    """

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    user_id: uuid.UUID = Field(..., description="ユーザーID")
    role: ProjectRole = Field(..., description="プロジェクトロール")
    is_owner: bool = Field(..., description="PROJECT_MANAGER ロールかどうか（後方互換性のため維持）")
    is_admin: bool = Field(..., description="PROJECT_MANAGER ロールかどうか（後方互換性のため維持）")


# ================================================================================
# 複数人登録スキーマ
# ================================================================================


class ProjectMemberBulkCreate(BaseModel):
    """プロジェクトメンバー複数人追加リクエストスキーマ。

    プロジェクトに複数のメンバーを一括追加する際に使用します。

    Attributes:
        members (list[ProjectMemberCreate]): 追加するメンバーのリスト

    Example:
        >>> bulk_create = ProjectMemberBulkCreate(
        ...     members=[
        ...         ProjectMemberCreate(user_id=uuid.uuid4(), role=ProjectRole.MEMBER),
        ...         ProjectMemberCreate(user_id=uuid.uuid4(), role=ProjectRole.VIEWER)
        ...     ]
        ... )

    Note:
        - 各メンバーは個別にバリデーションされます
        - 重複するメンバーは追加されません
        - 一部失敗しても成功したメンバーは追加されます
    """

    members: list[ProjectMemberCreate] = Field(..., min_length=1, max_length=100, description="追加するメンバーのリスト（最大100件）")


class ProjectMemberBulkError(BaseModel):
    """メンバー追加失敗情報スキーマ。

    複数人登録時の個別の失敗情報を表します。

    Attributes:
        user_id (uuid.UUID): 失敗したユーザーID
        role (ProjectRole): 指定されたロール
        error (str): エラーメッセージ

    Example:
        >>> error = ProjectMemberBulkError(
        ...     user_id=uuid.uuid4(),
        ...     role=ProjectRole.MEMBER,
        ...     error="ユーザーは既にプロジェクトのメンバーです"
        ... )
    """

    user_id: uuid.UUID = Field(..., description="失敗したユーザーID")
    role: ProjectRole = Field(..., description="指定されたロール")
    error: str = Field(..., description="エラーメッセージ")


class ProjectMemberBulkResponse(BaseModel):
    """プロジェクトメンバー複数人追加レスポンススキーマ。

    複数人登録APIのレスポンス形式を定義します。

    Attributes:
        project_id (uuid.UUID): プロジェクトID
        added (list[ProjectMemberDetailResponse]): 追加に成功したメンバーリスト
        failed (list[ProjectMemberBulkError]): 追加に失敗したメンバーリスト
        total_requested (int): リクエストされたメンバー数
        total_added (int): 追加に成功したメンバー数
        total_failed (int): 追加に失敗したメンバー数

    Example:
        >>> response = ProjectMemberBulkResponse(
        ...     project_id=uuid.uuid4(),
        ...     added=[member1, member2],
        ...     failed=[error1],
        ...     total_requested=3,
        ...     total_added=2,
        ...     total_failed=1
        ... )

    Note:
        - 一部失敗しても成功したメンバーは追加されます
        - failed リストで失敗理由を確認できます
    """

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    added: list[ProjectMemberDetailResponse] = Field(..., description="追加に成功したメンバーリスト")
    failed: list[ProjectMemberBulkError] = Field(..., description="追加に失敗したメンバーリスト")
    total_requested: int = Field(..., description="リクエストされたメンバー数")
    total_added: int = Field(..., description="追加に成功したメンバー数")
    total_failed: int = Field(..., description="追加に失敗したメンバー数")


# ================================================================================
# 複数人更新スキーマ
# ================================================================================


class ProjectMemberRoleUpdate(BaseModel):
    """プロジェクトメンバーロール更新リクエストアイテムスキーマ。

    複数人更新時の個別のメンバー更新情報を表します。

    Attributes:
        member_id (uuid.UUID): 更新するメンバーシップID
        role (ProjectRole): 新しいプロジェクトロール

    Example:
        >>> update = ProjectMemberRoleUpdate(
        ...     member_id=uuid.uuid4(),
        ...     role=ProjectRole.ADMIN
        ... )
    """

    member_id: uuid.UUID = Field(..., description="更新するメンバーシップID")
    role: ProjectRole = Field(..., description="新しいプロジェクトロール")


class ProjectMemberBulkUpdate(BaseModel):
    """プロジェクトメンバー複数人ロール更新リクエストスキーマ。

    プロジェクトの複数メンバーのロールを一括更新する際に使用します。

    Attributes:
        updates (list[ProjectMemberRoleUpdate]): 更新するメンバーのリスト

    Example:
        >>> bulk_update = ProjectMemberBulkUpdate(
        ...     updates=[
        ...         ProjectMemberRoleUpdate(member_id=uuid.uuid4(), role=ProjectRole.ADMIN),
        ...         ProjectMemberRoleUpdate(member_id=uuid.uuid4(), role=ProjectRole.MEMBER)
        ...     ]
        ... )

    Note:
        - 各メンバーは個別にバリデーションされます
        - 一部失敗しても成功したメンバーは更新されます
    """

    updates: list[ProjectMemberRoleUpdate] = Field(..., min_length=1, max_length=100, description="更新するメンバーのリスト（最大100件）")


class ProjectMemberBulkUpdateError(BaseModel):
    """メンバー更新失敗情報スキーマ。

    複数人更新時の個別の失敗情報を表します。

    Attributes:
        member_id (uuid.UUID): 失敗したメンバーシップID
        role (ProjectRole): 指定されたロール
        error (str): エラーメッセージ

    Example:
        >>> error = ProjectMemberBulkUpdateError(
        ...     member_id=uuid.uuid4(),
        ...     role=ProjectRole.ADMIN,
        ...     error="メンバーが見つかりません"
        ... )
    """

    member_id: uuid.UUID = Field(..., description="失敗したメンバーシップID")
    role: ProjectRole = Field(..., description="指定されたロール")
    error: str = Field(..., description="エラーメッセージ")


class ProjectMemberBulkUpdateResponse(BaseModel):
    """プロジェクトメンバー複数人ロール更新レスポンススキーマ。

    複数人更新APIのレスポンス形式を定義します。

    Attributes:
        project_id (uuid.UUID): プロジェクトID
        updated (list[ProjectMemberDetailResponse]): 更新に成功したメンバーリスト
        failed (list[ProjectMemberBulkUpdateError]): 更新に失敗したメンバーリスト
        total_requested (int): リクエストされたメンバー数
        total_updated (int): 更新に成功したメンバー数
        total_failed (int): 更新に失敗したメンバー数

    Example:
        >>> response = ProjectMemberBulkUpdateResponse(
        ...     project_id=uuid.uuid4(),
        ...     updated=[member1, member2],
        ...     failed=[error1],
        ...     total_requested=3,
        ...     total_updated=2,
        ...     total_failed=1
        ... )

    Note:
        - 一部失敗しても成功したメンバーは更新されます
        - failed リストで失敗理由を確認できます
    """

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    updated: list[ProjectMemberDetailResponse] = Field(..., description="更新に成功したメンバーリスト")
    failed: list[ProjectMemberBulkUpdateError] = Field(..., description="更新に失敗したメンバーリスト")
    total_requested: int = Field(..., description="リクエストされたメンバー数")
    total_updated: int = Field(..., description="更新に成功したメンバー数")
    total_failed: int = Field(..., description="更新に失敗したメンバー数")
