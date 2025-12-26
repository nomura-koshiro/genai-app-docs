"""ユーザーアカウントサービス共通ベース。

このモジュールは、ユーザーアカウントサービスの共通機能を提供します。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories import UserAccountRepository

logger = get_logger(__name__)


class UserAccountServiceBase:
    """ユーザーアカウントサービスの共通ベースクラス。"""

    def __init__(self, db: AsyncSession):
        """ユーザーアカウントサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = UserAccountRepository(db)
