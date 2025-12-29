"""システム関連モデル。

このモジュールは、システム管理に関連するデータベースモデルを提供します。

主なモデル:
    - UserActivity: ユーザー操作履歴
"""

from app.models.system.user_activity import UserActivity

__all__ = [
    "UserActivity",
]
