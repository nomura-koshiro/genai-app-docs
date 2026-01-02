"""ユーザーセッションリポジトリ。

このモジュールは、ユーザーセッションのデータアクセスを提供します。
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_account.user_session import UserSession
from app.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession, uuid.UUID]):
    """ユーザーセッションリポジトリ。

    ユーザーセッションのCRUD操作を提供します。

    メソッド:
        - get_with_user: ユーザー情報付きで取得
        - get_by_token_hash: トークンハッシュで取得
        - list_active: アクティブセッションを取得
        - list_by_user: ユーザーのセッションを取得
        - count_active: アクティブセッション数を取得
        - count_logins_today: 本日のログイン数を取得
        - terminate_session: セッションを終了
        - terminate_all_user_sessions: ユーザーの全セッションを終了
        - cleanup_expired: 期限切れセッションをクリーンアップ
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(UserSession, db)

    async def get_with_user(self, id: uuid.UUID) -> UserSession | None:
        """ユーザー情報付きでセッションを取得します。

        Args:
            id: セッションID

        Returns:
            UserSession | None: セッション（ユーザー情報付き）
        """
        query = select(UserSession).options(selectinload(UserSession.user)).where(UserSession.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        """トークンハッシュでセッションを取得します。

        Args:
            token_hash: トークンハッシュ

        Returns:
            UserSession | None: セッション
        """
        query = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                and_(
                    UserSession.session_token_hash == token_hash,
                    UserSession.is_active == True,  # noqa: E712
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserSession]:
        """アクティブセッションを取得します。

        Args:
            user_id: ユーザーID
            ip_address: IPアドレス
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserSession]: セッションリスト
        """
        now = datetime.now(UTC)

        query = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                and_(
                    UserSession.is_active == True,  # noqa: E712
                    UserSession.expires_at > now,
                )
            )
        )

        if user_id:
            query = query.where(UserSession.user_id == user_id)
        if ip_address:
            query = query.where(UserSession.ip_address == ip_address)

        query = query.order_by(UserSession.last_activity_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserSession]:
        """ユーザーのセッションを取得します。

        Args:
            user_id: ユーザーID
            active_only: アクティブのみ
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserSession]: セッションリスト
        """
        query = select(UserSession).where(UserSession.user_id == user_id)

        if active_only:
            now = datetime.now(UTC)
            query = query.where(
                and_(
                    UserSession.is_active == True,  # noqa: E712
                    UserSession.expires_at > now,
                )
            )

        query = query.order_by(UserSession.last_activity_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_active(self) -> int:
        """アクティブセッション数を取得します。

        Returns:
            int: アクティブセッション数
        """
        now = datetime.now(UTC)

        query = (
            select(func.count())
            .select_from(UserSession)
            .where(
                and_(
                    UserSession.is_active == True,  # noqa: E712
                    UserSession.expires_at > now,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_logins_today(self) -> int:
        """本日のログイン数を取得します。

        Returns:
            int: 本日のログイン数
        """
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        query = select(func.count()).select_from(UserSession).where(UserSession.login_at >= today_start)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def terminate_session(
        self,
        session_id: uuid.UUID,
        reason: str,
    ) -> UserSession | None:
        """セッションを終了します。

        Args:
            session_id: セッションID
            reason: 終了理由

        Returns:
            UserSession | None: 終了したセッション
        """
        session = await self.get(session_id)
        if session is None:
            return None

        now = datetime.now(UTC)
        session.is_active = False
        session.logout_at = now
        session.logout_reason = reason

        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def terminate_all_user_sessions(
        self,
        user_id: uuid.UUID,
        reason: str,
    ) -> int:
        """ユーザーの全セッションを終了します。

        Args:
            user_id: ユーザーID
            reason: 終了理由

        Returns:
            int: 終了したセッション数
        """
        now = datetime.now(UTC)

        query = (
            update(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,  # noqa: E712
                )
            )
            .values(
                is_active=False,
                logout_at=now,
                logout_reason=reason,
            )
        )
        result: CursorResult[Any] = await self.db.execute(query)  # type: ignore[assignment]
        await self.db.flush()
        return result.rowcount or 0

    async def count_expired(self, before_date: datetime) -> int:
        """期限切れセッション数をカウントします。

        非アクティブかつ指定日より前のセッション数を取得します。

        Args:
            before_date: この日付より前のセッションをカウント

        Returns:
            int: セッション数
        """
        query = (
            select(func.count())
            .select_from(UserSession)
            .where(
                and_(
                    UserSession.is_active == False,  # noqa: E712
                    UserSession.logout_at < before_date,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_expired_date_range(
        self,
        before_date: datetime,
    ) -> tuple[datetime | None, datetime | None]:
        """期限切れセッションの日付範囲を取得します。

        Args:
            before_date: この日付より前のセッションを対象

        Returns:
            tuple[datetime | None, datetime | None]: (最古日時, 最新日時)
        """
        conditions = [
            UserSession.is_active == False,  # noqa: E712
            UserSession.logout_at < before_date,
        ]

        # 最古レコード
        oldest_query = select(func.min(UserSession.logout_at)).where(and_(*conditions))
        oldest_result = await self.db.execute(oldest_query)
        oldest = oldest_result.scalar_one_or_none()

        # 最新レコード
        newest_query = select(func.max(UserSession.logout_at)).where(and_(*conditions))
        newest_result = await self.db.execute(newest_query)
        newest = newest_result.scalar_one_or_none()

        return (oldest, newest)

    async def cleanup_expired(self, before_date: datetime) -> int:
        """期限切れセッションをクリーンアップします。

        非アクティブかつ指定日より前のセッションを削除します。

        Args:
            before_date: この日付より前のセッションを削除

        Returns:
            int: 削除件数
        """
        query = delete(UserSession).where(
            and_(
                UserSession.is_active == False,  # noqa: E712
                UserSession.logout_at < before_date,
            )
        )
        result: CursorResult[Any] = await self.db.execute(query)  # type: ignore[assignment]
        await self.db.flush()
        return result.rowcount or 0
