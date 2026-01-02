"""ユーザー設定関連のPydanticスキーマ。

このモジュールは、ユーザー設定管理のリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    - UserSettingsResponse: ユーザー設定レスポンス
    - UserSettingsUpdate: ユーザー設定更新リクエスト
    - NotificationSettingsInfo: 通知設定情報
    - DisplaySettingsInfo: 表示設定情報
"""

from enum import Enum

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class ThemeEnum(str, Enum):
    """テーマ設定。"""

    light = "light"
    dark = "dark"
    system = "system"


class LanguageEnum(str, Enum):
    """言語設定。"""

    ja = "ja"
    en = "en"


class ProjectViewEnum(str, Enum):
    """プロジェクト表示形式。"""

    grid = "grid"
    list = "list"


class NotificationSettingsInfo(BaseCamelCaseModel):
    """通知設定情報。

    Attributes:
        email_enabled (bool): メール通知の有効化
        project_invite (bool): プロジェクト招待通知
        session_complete (bool): セッション完了通知
        tree_update (bool): ツリー更新通知
        system_announcement (bool): システムお知らせ通知
    """

    email_enabled: bool = Field(default=True, description="メール通知の有効化")
    project_invite: bool = Field(default=True, description="プロジェクト招待通知")
    session_complete: bool = Field(default=True, description="セッション完了通知")
    tree_update: bool = Field(default=True, description="ツリー更新通知")
    system_announcement: bool = Field(default=True, description="システムお知らせ通知")


class DisplaySettingsInfo(BaseCamelCaseModel):
    """表示設定情報。

    Attributes:
        items_per_page (int): ページあたり表示件数（10-100）
        default_project_view (ProjectViewEnum): デフォルトプロジェクト表示形式
        show_welcome_message (bool): ウェルカムメッセージ表示
    """

    items_per_page: int = Field(default=20, ge=10, le=100, description="ページあたり表示件数")
    default_project_view: ProjectViewEnum = Field(
        default=ProjectViewEnum.grid, description="デフォルトプロジェクト表示形式"
    )
    show_welcome_message: bool = Field(default=True, description="ウェルカムメッセージ表示")


class UserSettingsResponse(BaseCamelCaseORMModel):
    """ユーザー設定レスポンススキーマ。

    Attributes:
        theme (ThemeEnum): テーマ設定
        language (LanguageEnum): 言語設定
        timezone (str): タイムゾーン設定
        notifications (NotificationSettingsInfo): 通知設定
        display (DisplaySettingsInfo): 表示設定
    """

    theme: ThemeEnum = Field(default=ThemeEnum.light, description="テーマ設定")
    language: LanguageEnum = Field(default=LanguageEnum.ja, description="言語設定")
    timezone: str = Field(default="Asia/Tokyo", description="タイムゾーン設定")
    notifications: NotificationSettingsInfo = Field(..., description="通知設定")
    display: DisplaySettingsInfo = Field(..., description="表示設定")


class NotificationSettingsUpdate(BaseCamelCaseModel):
    """通知設定更新リクエスト。

    Attributes:
        email_enabled (bool | None): メール通知の有効化
        project_invite (bool | None): プロジェクト招待通知
        session_complete (bool | None): セッション完了通知
        tree_update (bool | None): ツリー更新通知
        system_announcement (bool | None): システムお知らせ通知
    """

    email_enabled: bool | None = Field(default=None, description="メール通知の有効化")
    project_invite: bool | None = Field(default=None, description="プロジェクト招待通知")
    session_complete: bool | None = Field(default=None, description="セッション完了通知")
    tree_update: bool | None = Field(default=None, description="ツリー更新通知")
    system_announcement: bool | None = Field(default=None, description="システムお知らせ通知")


class DisplaySettingsUpdate(BaseCamelCaseModel):
    """表示設定更新リクエスト。

    Attributes:
        items_per_page (int | None): ページあたり表示件数（10-100）
        default_project_view (ProjectViewEnum | None): デフォルトプロジェクト表示形式
        show_welcome_message (bool | None): ウェルカムメッセージ表示
    """

    items_per_page: int | None = Field(default=None, ge=10, le=100, description="ページあたり表示件数")
    default_project_view: ProjectViewEnum | None = Field(default=None, description="デフォルトプロジェクト表示形式")
    show_welcome_message: bool | None = Field(default=None, description="ウェルカムメッセージ表示")


class UserSettingsUpdate(BaseCamelCaseModel):
    """ユーザー設定更新リクエストスキーマ。

    すべてのフィールドはオプションで、指定されたフィールドのみが更新されます。

    Attributes:
        theme (ThemeEnum | None): テーマ設定
        language (LanguageEnum | None): 言語設定
        timezone (str | None): タイムゾーン設定
        notifications (NotificationSettingsUpdate | None): 通知設定
        display (DisplaySettingsUpdate | None): 表示設定
    """

    theme: ThemeEnum | None = Field(default=None, description="テーマ設定")
    language: LanguageEnum | None = Field(default=None, description="言語設定")
    timezone: str | None = Field(default=None, description="タイムゾーン設定")
    notifications: NotificationSettingsUpdate | None = Field(default=None, description="通知設定")
    display: DisplaySettingsUpdate | None = Field(default=None, description="表示設定")
