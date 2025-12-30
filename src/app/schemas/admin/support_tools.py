"""サポートツールスキーマ。

このモジュールは、サポートツールのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class ImpersonateRequest(BaseCamelCaseModel):
    """ユーザー代行開始リクエストスキーマ。"""

    reason: str = Field(..., min_length=1, max_length=500, description="代行理由")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class ImpersonateUserInfo(BaseCamelCaseModel):
    """代行対象ユーザー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")


class ImpersonateResponse(BaseCamelCaseModel):
    """ユーザー代行レスポンス。"""

    impersonation_token: str = Field(..., description="代行トークン")
    target_user: ImpersonateUserInfo = Field(..., description="対象ユーザー")
    expires_at: datetime = Field(..., description="有効期限")


class ImpersonateEndResponse(BaseCamelCaseModel):
    """ユーザー代行終了レスポンス。"""

    success: bool = Field(..., description="成功フラグ")
    message: str = Field(..., description="メッセージ")


class DebugModeResponse(BaseCamelCaseModel):
    """デバッグモードレスポンス。"""

    enabled: bool = Field(..., description="デバッグモード状態")
    message: str = Field(..., description="メッセージ")
