"""通知関連のSQLAlchemyモデル。

このモジュールは、ユーザー通知機能に関連するデータベースモデルを提供します。

主なモデル:
    - UserNotification: ユーザー通知モデル

Enum定義はapp.models.enumsパッケージで一元管理されています:
    - NotificationTypeEnum: 通知タイプ
    - ReferenceTypeEnum: 参照タイプ
"""

from app.models.notification.user_notification import UserNotification

__all__ = [
    "UserNotification",
]
