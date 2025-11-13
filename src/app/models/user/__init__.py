"""ユーザー関連のSQLAlchemyモデル。

このモジュールは、ユーザー管理機能に関連するデータベースモデルを提供します。

主なモデル:
    - UserAccount: ユーザーモデル（認証、プロフィール、システムロール）
    - SystemUserRole: システムロール（admin, user）

使用例:
    >>> from app.models.user import UserAccount, SystemUserRole
    >>> user = UserAccount(
    ...     email="user@example.com",
    ...     full_name="山田太郎",
    ...     system_role=SystemUserRole.USER
    ... )
"""

from app.models.user.user import SystemUserRole, UserAccount

__all__ = ["SystemUserRole", "UserAccount"]
