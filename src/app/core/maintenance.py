"""メンテナンスモードヘルパー。

ミドルウェアからメンテナンスモード設定を取得するためのヘルパー関数を提供します。
データアクセス層への直接依存を避け、レイヤー分離を維持します。
"""

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SettingCategory
from app.repositories.admin import SystemSettingRepository


async def get_maintenance_settings(session: AsyncSession) -> dict[str, Any]:
    """メンテナンスモード設定を取得します。

    Args:
        session: データベースセッション

    Returns:
        dict: メンテナンスモード設定
            - enabled: メンテナンスモードが有効か
            - message: メンテナンスメッセージ
            - allow_admin_access: 管理者アクセスを許可するか
    """
    repository = SystemSettingRepository(session)

    # メンテナンスモード設定を並行取得
    maintenance_mode, maintenance_message, allow_admin = await asyncio.gather(
        repository.get_by_category_and_key(
            category=SettingCategory.MAINTENANCE,
            key="maintenance_mode",
        ),
        repository.get_by_category_and_key(
            category=SettingCategory.MAINTENANCE,
            key="maintenance_message",
        ),
        repository.get_by_category_and_key(
            category=SettingCategory.MAINTENANCE,
            key="allow_admin_access",
        ),
    )

    return {
        "enabled": _get_setting_value(maintenance_mode, False),
        "message": _get_setting_value(maintenance_message, ""),
        "allow_admin_access": _get_setting_value(allow_admin, True),
    }


def _get_setting_value(setting: Any, default: Any) -> Any:
    """設定値を取得します。

    SystemSettingのvalueはJSONB型なので、dictの場合はvalue自体を、
    それ以外の場合はそのまま返します。

    Args:
        setting: SystemSettingオブジェクト
        default: デフォルト値

    Returns:
        Any: 設定値
    """
    if setting is None:
        return default
    value = setting.value
    # JSONB型なので既にPythonオブジェクトに変換されている
    # valueがdictの場合、実際の値を取得（{"value": X}形式の場合）
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value
