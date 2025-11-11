"""セッション管理サービス。

このモジュールは、チャットセッションの管理機能を提供します。
セッションの作成、取得、更新、削除を行います。
"""

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.sample.sample_session import SampleSession
from app.repositories.sample.sample_session import SampleSessionRepository

logger = get_logger(__name__)


class SampleSessionService:
    """セッション管理サービス。

    チャットセッションのCRUD操作を提供します。
    セッション一覧取得、詳細取得、作成、更新、削除が可能です。
    """

    def __init__(self, db: AsyncSession):
        """セッションサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = SampleSessionRepository(db)

    @measure_performance
    async def list_sessions(
        self,
        user_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SampleSession], int]:
        """セッション一覧を取得します。

        Args:
            user_id: ユーザーID（指定した場合、該当ユーザーのセッションのみ）
            skip: スキップするセッション数
            limit: 返却する最大セッション数

        Returns:
            tuple[list[SampleSession], int]: (セッションリスト, 総セッション数)
        """
        logger.debug(
            "セッション一覧取得",
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        # クエリ構築
        query = select(SampleSession).options(selectinload(SampleSession.messages))

        if user_id is not None:
            query = query.filter(SampleSession.user_id == user_id)

        # 総数取得
        from sqlalchemy import func

        count_query = select(func.count(SampleSession.id))
        if user_id is not None:
            count_query = count_query.filter(SampleSession.user_id == user_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # ページネーション適用
        query = query.order_by(SampleSession.updated_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        logger.debug(
            "セッション一覧取得完了",
            total=total,
            returned=len(sessions),
        )

        return sessions, total

    @measure_performance
    async def get_session(self, session_id: str) -> SampleSession:
        """セッション情報と会話履歴を取得します。

        Args:
            session_id: セッション識別子

        Returns:
            SampleSession: セッションオブジェクト（メッセージを含む）

        Raises:
            NotFoundError: セッションが存在しない場合
        """
        logger.debug("セッション取得", session_id=session_id, action="get_session")

        session = await self.repository.get_by_session_id(session_id)
        if not session:
            raise NotFoundError(
                f"セッションが見つかりません: {session_id}",
                details={"session_id": session_id},
            )

        logger.debug(
            "セッション取得完了",
            session_id=session_id,
            message_count=len(session.messages),
        )

        return session

    @measure_performance
    @transactional
    async def create_session(
        self,
        user_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> SampleSession:
        """新しいセッションを作成します。

        Args:
            user_id: ユーザーID（オプション）
            metadata: セッションメタデータ（オプション）

        Returns:
            SampleSession: 作成されたセッション
        """
        session_id = self._generate_session_id()

        logger.info(
            "セッション作成",
            session_id=session_id,
            user_id=user_id,
        )

        session = await self.repository.create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )

        await self.db.commit()

        logger.info(
            "セッション作成完了",
            session_id=session_id,
        )

        return session

    @measure_performance
    @transactional
    async def update_session(
        self,
        session_id: str,
        metadata: dict | None = None,
    ) -> SampleSession:
        """セッション情報を更新します。

        Args:
            session_id: セッション識別子
            metadata: 更新するメタデータ

        Returns:
            SampleSession: 更新されたセッション

        Raises:
            NotFoundError: セッションが存在しない場合
        """
        logger.info(
            "セッション更新",
            session_id=session_id,
        )

        session = await self.repository.get_by_session_id(session_id)
        if not session:
            raise NotFoundError(
                f"セッションが見つかりません: {session_id}",
                details={"session_id": session_id},
            )

        # メタデータ更新
        if metadata is not None:
            session.session_metadata = metadata

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            "セッション更新完了",
            session_id=session_id,
        )

        return session

    @measure_performance
    @transactional
    async def delete_session(self, session_id: str) -> bool:
        """セッションと関連するメッセージを削除します。

        Args:
            session_id: セッション識別子

        Returns:
            bool: 削除成功の場合True

        Raises:
            NotFoundError: セッションが存在しない場合
        """
        logger.info("セッション削除", session_id=session_id)

        deleted = await self.repository.delete_session(session_id)
        if not deleted:
            raise NotFoundError(
                f"セッションが見つかりません: {session_id}",
                details={"session_id": session_id},
            )

        await self.db.commit()

        logger.info("セッション削除完了", session_id=session_id)

        return True

    def _generate_session_id(self) -> str:
        """セッションIDを生成します。

        Returns:
            str: ランダムなセッション識別子
        """
        return f"session_{secrets.token_urlsafe(16)}"
