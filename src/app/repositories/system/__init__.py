"""システム関連リポジトリ。

このモジュールは、システム管理に関連するデータアクセスリポジトリを提供します。

主なリポジトリ:
    - UserActivityRepository: ユーザー操作履歴
"""

from app.repositories.system.user_activity import UserActivityRepository

__all__ = [
    "UserActivityRepository",
]
