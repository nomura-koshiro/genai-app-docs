"""セッション管理スキーマ。

このモジュールは、ユーザーセッション管理のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# フィルタスキーマ
# ================================================================================


class SessionFilter(BaseCamelCaseModel):
    """セッションフィルタスキーマ。"""

    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


# ================================================================================
# リクエストスキーマ
# ================================================================================


class SessionTerminateRequest(BaseCamelCaseModel):
    """セッション終了リクエストスキーマ。"""

    reason: str = Field(default="FORCED", description="終了理由")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class SessionUserInfo(BaseCamelCaseModel):
    """セッションのユーザー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: str = Field(..., description="メールアドレス")


class DeviceInfo(BaseCamelCaseModel):
    """デバイス情報。"""

    os: str | None = Field(default=None, description="OS")
    browser: str | None = Field(default=None, description="ブラウザ")


class SessionResponse(BaseCamelCaseORMModel):
    """セッションレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="セッションID")
    user: SessionUserInfo = Field(..., description="ユーザー情報")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    device_info: DeviceInfo | None = Field(default=None, description="デバイス情報")
    login_at: datetime = Field(..., description="ログイン日時")
    last_activity_at: datetime = Field(..., description="最終アクティビティ日時")
    expires_at: datetime = Field(..., description="有効期限")
    is_active: bool = Field(..., description="アクティブフラグ")


class SessionStatistics(BaseCamelCaseModel):
    """セッション統計情報。"""

    active_sessions: int = Field(..., description="アクティブセッション数")
    logins_today: int = Field(..., description="本日のログイン数")


class SessionListResponse(BaseCamelCaseModel):
    """セッション一覧レスポンススキーマ。"""

    items: list[SessionResponse] = Field(..., description="セッションリスト")
    total: int = Field(..., description="総件数")
    statistics: SessionStatistics = Field(..., description="統計情報")


class SessionTerminateResponse(BaseCamelCaseModel):
    """セッション終了レスポンススキーマ。"""

    terminated_count: int = Field(..., description="終了したセッション数")
    message: str = Field(..., description="メッセージ")
