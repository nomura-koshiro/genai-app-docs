"""ユーザー関連のSQLAlchemyモデル。

このモジュールは、ユーザー管理機能に関連するデータベースモデルを提供します。

主なモデル:
    - User: ユーザーモデル（認証、プロフィール、システムロール）
    - SystemRole: システムロール（admin, user）

使用例:
    >>> from app.models.user import User, SystemRole
    >>> user = User(
    ...     email="user@example.com",
    ...     full_name="山田太郎",
    ...     system_role=SystemRole.USER
    ... )
"""

from app.models.user.user import SystemRole, User

__all__ = ["SystemRole", "User"]
