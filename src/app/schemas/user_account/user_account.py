"""Azure AD認証用ユーザーのPydanticスキーマ。

このモジュールは、Azure AD認証に対応したユーザー管理の
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    ユーザー情報:
        - UserAccountBase: 基本ユーザー情報（共通フィールド）
        - UserAccountUpdate: ユーザー情報更新リクエスト
        - UserAccountResponse: ユーザー情報レスポンス
        - UserAccountListResponse: ユーザー一覧レスポンス

使用方法:
    >>> from app.schemas.user_account.user_account import UserAccountResponse
    >>>
    >>> # ユーザー情報レスポンス
    >>> user = UserAccountResponse(
    ...     id=uuid.uuid4(),
    ...     azure_oid="azure-oid-12345",
    ...     email="user@company.com",
    ...     display_name="John Doe",
    ...     roles=["User"],
    ...     is_active=True,
    ...     created_at=datetime.now(UTC),
    ...     updated_at=datetime.now(UTC)
    ... )
"""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class UserAccountBase(BaseCamelCaseModel):
    """ベースユーザースキーマ。

    ユーザーの基本情報を定義します。他のユーザースキーマの基底クラスとして使用されます。

    Attributes:
        email (EmailStr): ユーザーメールアドレス
            - 自動的にメール形式検証が行われます
        display_name (str | None): 表示名
            - 最大255文字
        roles (list[str]): システムレベルのロール
            - 例: ["SystemAdmin", "User"]

    Example:
        >>> user = UserAccountBase(
        ...     email="john@company.com",
        ...     display_name="John Doe",
        ...     roles=["User"]
        ... )

    Note:
        - このクラスは直接使用せず、継承して使用します
        - EmailStr型により自動的にメール形式がバリデーションされます
    """

    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    display_name: str | None = Field(default=None, max_length=255, description="表示名")
    roles: list[str] = Field(default_factory=list, description="システムレベルのロール")


class UserAccountUpdate(BaseCamelCaseModel):
    """ユーザー情報更新リクエストスキーマ。

    ユーザー情報の更新時に使用します。

    Attributes:
        display_name (str | None): 表示名（オプション）
        roles (list[str] | None): システムレベルのロール（オプション）
        is_active (bool | None): アクティブフラグ（オプション）

    Example:
        >>> update = UserAccountUpdate(
        ...     display_name="John Smith",
        ...     roles=["SystemAdmin", "User"],
        ...     is_active=True
        ... )

    Note:
        - すべてのフィールドはオプションです
        - 指定されたフィールドのみが更新されます
        - email と azure_oid は更新できません
    """

    display_name: str | None = Field(default=None, max_length=255, description="表示名")
    roles: list[str] | None = Field(default=None, description="システムレベルのロール")
    is_active: bool | None = Field(default=None, description="アクティブフラグ")


class UserAccountResponse(BaseCamelCaseORMModel):
    """ユーザー情報レスポンススキーマ。

    APIレスポンスでユーザー情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): ユーザーID（UUID）
        azure_oid (str): Azure ID (Azure AD Object ID)
        email (EmailStr): ユーザーメールアドレス
        display_name (str | None): 表示名
        roles (list[str]): システムレベルのロール
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
        last_login (datetime | None): 最終ログイン日時
        login_count (int): ログイン回数

    Example:
        >>> from datetime import UTC
        >>> user = UserAccountResponse(
        ...     id=uuid.uuid4(),
        ...     azure_oid="azure-oid-12345",
        ...     email="john@company.com",
        ...     display_name="John Doe",
        ...     roles=["User"],
        ...     is_active=True,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC),
        ...     last_login=None
        ... )

    Note:
        - from_attributesを有効にしているため、ORMモデルから直接変換可能です
        - パスワード情報は含まれません（Azure AD認証のため）
    """

    id: uuid.UUID = Field(..., description="ユーザーID（UUID）")
    azure_oid: str = Field(..., description="Azure ID (Azure AD Object ID)")
    email: EmailStr = Field(..., description="ユーザーメールアドレス")
    display_name: str | None = Field(default=None, max_length=255, description="表示名")
    roles: list[str] = Field(default_factory=list, description="システムレベルのロール")
    is_active: bool = Field(..., description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    last_login: datetime | None = Field(default=None, description="最終ログイン日時")
    login_count: int = Field(default=0, description="ログイン回数")


class UserAccountListResponse(BaseCamelCaseModel):
    """ユーザー一覧レスポンススキーマ。

    ユーザー一覧APIのレスポンス形式を定義します。

    Attributes:
        users (list[UserAccountResponse]): ユーザーリスト
        total (int): 総件数
        skip (int): スキップ数（オフセット）
        limit (int): 取得件数

    Example:
        >>> response = UserAccountListResponse(
        ...     users=[user1, user2, user3],
        ...     total=100,
        ...     skip=0,
        ...     limit=10
        ... )

    Note:
        - ページネーション情報を含みます
        - total は全体の件数、skip/limit はページング パラメータ
    """

    users: list[UserAccountResponse] = Field(..., description="ユーザーリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数（オフセット）")
    limit: int = Field(..., description="取得件数")


class UserAccountRoleUpdate(BaseCamelCaseModel):
    """ユーザーロール更新リクエストスキーマ。

    管理者がユーザーのシステムロールを更新する際に使用します。

    Attributes:
        roles (list[str]): 新しいシステムロール

    Example:
        >>> update = UserAccountRoleUpdate(
        ...     roles=["SystemAdmin", "User"]
        ... )

    Note:
        - 管理者権限が必要です
        - 有効なロール: "SystemAdmin", "User"
    """

    roles: list[str] = Field(..., description="システムレベルのロール", min_length=1)


class ProjectParticipationResponse(BaseCamelCaseORMModel):
    """プロジェクト参加情報レスポンススキーマ。

    ユーザーが参加しているプロジェクト情報を定義します。

    Attributes:
        project_id (uuid.UUID): プロジェクトID
        project_name (str): プロジェクト名
        role (str): プロジェクト内のロール
        joined_at (datetime): 参加日時
        is_active (bool): アクティブフラグ
    """

    project_id: uuid.UUID = Field(..., description="プロジェクトID")
    project_name: str = Field(..., description="プロジェクト名")
    role: str = Field(..., description="プロジェクト内のロール")
    joined_at: datetime = Field(..., description="参加日時")
    is_active: bool = Field(..., description="アクティブフラグ")


class RecentActivityResponse(BaseCamelCaseModel):
    """最近のアクティビティレスポンススキーマ。

    ユーザーの最近のアクティビティを定義します。

    Attributes:
        activity_type (str): アクティビティタイプ（例: "session_created", "tree_created"）
        description (str): アクティビティの説明
        timestamp (datetime): アクティビティ発生日時
        project_name (str | None): 関連するプロジェクト名
    """

    activity_type: str = Field(..., description="アクティビティタイプ")
    description: str = Field(..., description="アクティビティの説明")
    timestamp: datetime = Field(..., description="アクティビティ発生日時")
    project_name: str | None = Field(default=None, description="関連するプロジェクト名")


class UserActivityStats(BaseCamelCaseModel):
    """ユーザーアクティビティ統計情報。

    ユーザーの活動統計を定義します。

    Attributes:
        project_count (int): 参加プロジェクト数
        session_count (int): 作成した分析セッション数
        tree_count (int): 作成したDriver Tree数
    """

    project_count: int = Field(default=0, description="参加プロジェクト数")
    session_count: int = Field(default=0, description="作成した分析セッション数")
    tree_count: int = Field(default=0, description="作成したDriver Tree数")


class UserAccountDetailResponse(UserAccountResponse):
    """ユーザー詳細情報レスポンススキーマ。

    ユーザー詳細APIで統計情報、参加プロジェクト、最近のアクティビティを含めて返す際に使用します。

    Attributes:
        stats (UserActivityStats | None): ユーザーアクティビティ統計情報
        projects (list[ProjectParticipationResponse]): 参加プロジェクト一覧
        activities (list[RecentActivityResponse]): 最近のアクティビティ一覧
    """

    stats: UserActivityStats | None = Field(default=None, description="ユーザーアクティビティ統計情報")
    projects: list[ProjectParticipationResponse] = Field(default_factory=list, description="参加プロジェクト一覧")
    activities: list[RecentActivityResponse] = Field(default_factory=list, description="最近のアクティビティ一覧")
