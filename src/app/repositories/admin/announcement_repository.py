"""お知らせリポジトリ。

このモジュールは、システムお知らせのデータアクセスを提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.system.system_announcement import SystemAnnouncement
from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository[SystemAnnouncement, uuid.UUID]):
    """お知らせリポジトリ。

    システムお知らせのCRUD操作と検索機能を提供します。

    メソッド:
        - get_with_creator: 作成者情報付きで取得
        - list_active: アクティブなお知らせを取得
        - list_for_user: ユーザー向けお知らせを取得
        - list_all: 全お知らせを取得（管理用）
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(SystemAnnouncement, db)

    async def get_with_creator(self, id: uuid.UUID) -> SystemAnnouncement | None:
        """作成者情報付きでお知らせを取得します。

        Args:
            id: お知らせID

        Returns:
            SystemAnnouncement | None: お知らせ（作成者情報付き）
        """
        query = select(SystemAnnouncement).options(selectinload(SystemAnnouncement.creator)).where(SystemAnnouncement.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        current_time: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAnnouncement]:
        """アクティブなお知らせを取得します。

        Args:
            current_time: 基準時刻（デフォルト: 現在時刻）
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAnnouncement]: お知らせリスト
        """
        if current_time is None:
            current_time = datetime.now(UTC)

        query = (
            select(SystemAnnouncement)
            .options(selectinload(SystemAnnouncement.creator))
            .where(
                and_(
                    SystemAnnouncement.is_active == True,  # noqa: E712
                    SystemAnnouncement.start_at <= current_time,
                    or_(
                        SystemAnnouncement.end_at.is_(None),
                        SystemAnnouncement.end_at >= current_time,
                    ),
                )
            )
            .order_by(SystemAnnouncement.priority, SystemAnnouncement.start_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_user(
        self,
        user_roles: list[str],
        *,
        current_time: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAnnouncement]:
        """ユーザー向けお知らせを取得します。

        対象ロールが空の場合は全員向け、指定がある場合はユーザーのロールに一致するもののみ。

        Args:
            user_roles: ユーザーのロールリスト
            current_time: 基準時刻
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAnnouncement]: お知らせリスト
        """
        if current_time is None:
            current_time = datetime.now(UTC)

        # target_roles が空または NULL の場合は全員向け
        # それ以外はユーザーのロールに一致するもの
        query = (
            select(SystemAnnouncement)
            .where(
                and_(
                    SystemAnnouncement.is_active == True,  # noqa: E712
                    SystemAnnouncement.start_at <= current_time,
                    or_(
                        SystemAnnouncement.end_at.is_(None),
                        SystemAnnouncement.end_at >= current_time,
                    ),
                    or_(
                        SystemAnnouncement.target_roles.is_(None),
                        SystemAnnouncement.target_roles == [],
                        # JSONBの配列と重複チェック
                        SystemAnnouncement.target_roles.op("?|")(user_roles),
                    ),
                )
            )
            .order_by(SystemAnnouncement.priority, SystemAnnouncement.start_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAnnouncement]:
        """全お知らせを取得します（管理用）。

        Args:
            is_active: アクティブフィルタ
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAnnouncement]: お知らせリスト
        """
        query = select(SystemAnnouncement).options(selectinload(SystemAnnouncement.creator))

        if is_active is not None:
            query = query.where(SystemAnnouncement.is_active == is_active)

        query = query.order_by(SystemAnnouncement.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
