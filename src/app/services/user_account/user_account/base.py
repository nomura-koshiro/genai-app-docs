"""ユーザーアカウントサービス共通ベース。

このモジュールは、ユーザーアカウントサービスの共通機能を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import UserAccount
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

    async def _get_user_or_raise(self, user_id: uuid.UUID) -> UserAccount:
        """ユーザーを取得します。存在しない場合は例外を発生させます。

        Args:
            user_id: ユーザーID

        Returns:
            UserAccount: ユーザーモデルインスタンス

        Raises:
            NotFoundError: ユーザーが見つからない場合
        """
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning("ユーザーが見つかりません", user_id=str(user_id))
            raise NotFoundError(
                "ユーザーが見つかりません",
                details={"user_id": str(user_id)},
            )
        return user

    async def _validate_email_uniqueness(
        self,
        email: str,
        exclude_user_id: uuid.UUID | None = None,
    ) -> None:
        """メールアドレスの一意性を検証します。

        Args:
            email: チェックするメールアドレス
            exclude_user_id: チェックから除外するユーザーID（更新時に指定）

        Raises:
            ValidationError: メールアドレスが既に使用されている場合
        """
        existing_user = await self.repository.get_by_email(email)
        if existing_user and (exclude_user_id is None or existing_user.id != exclude_user_id):
            raise ValidationError(
                "このメールアドレスは既に使用されています",
                details={"email": email},
            )
