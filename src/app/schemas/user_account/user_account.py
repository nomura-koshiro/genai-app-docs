"""Azure AD認証用ユーザーのPydanticスキーマ。

このモジュールは、Azure AD認証に対応したユーザー管理の
すべてのリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    ユーザー情報:
        - UserAccountBase: 基本ユーザー情報（共通フィールド）
        - UserAccountResponse: ユーザー情報レスポンス
        - UserAccountUpdate: ユーザー情報更新リクエスト
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

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserAccountBase(BaseModel):
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


class UserAccountResponse(UserAccountBase):
    """ユーザー情報レスポンススキーマ。

    APIレスポンスでユーザー情報を返す際に使用します。

    Attributes:
        id (uuid.UUID): ユーザーID（UUID）
        azure_oid (str): Azure AD Object ID
        email (EmailStr): ユーザーメールアドレス（UserAccountBaseから継承）
        display_name (str | None): 表示名（UserAccountBaseから継承）
        roles (list[str]): システムレベルのロール（UserAccountBaseから継承）
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
        last_login (datetime | None): 最終ログイン日時

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
    azure_oid: str = Field(..., description="Azure AD Object ID")
    is_active: bool = Field(..., description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    last_login: datetime | None = Field(default=None, description="最終ログイン日時")

    model_config = ConfigDict(from_attributes=True)


class UserAccountUpdate(BaseModel):
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


class UserAccountListResponse(BaseModel):
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
