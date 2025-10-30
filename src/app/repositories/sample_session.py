"""セッション関連のリポジトリ。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.sample_session import SampleMessage, SampleSession
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class SampleSessionRepository(BaseRepository[SampleSession, int]):
    """サンプル: セッションリポジトリ。

    セッションのCRUD操作を提供します。
    """

    def __init__(self, db: AsyncSession):
        """セッションリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(SampleSession, db)

    async def get_by_session_id(self, session_id: str) -> SampleSession | None:
        """session_idでセッションを取得します。

        Args:
            session_id: セッション識別子

        Returns:
            SampleSession | None: セッションオブジェクト、存在しない場合はNone
        """
        result = await self.db.execute(
            select(SampleSession).options(selectinload(SampleSession.messages)).filter(SampleSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def create_session(self, session_id: str, user_id: int | None = None, metadata: dict | None = None) -> SampleSession:
        """新しいセッションを作成します。

        Args:
            session_id: セッション識別子
            user_id: ユーザーID（オプション）
            metadata: セッションメタデータ（オプション）

        Returns:
            SampleSession: 作成されたセッション
        """
        session = SampleSession(session_id=session_id, user_id=user_id, session_metadata=metadata)
        self.db.add(session)
        await self.db.flush()
        return session

    async def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        tokens_used: int | None = None,
        model: str | None = None,
    ) -> SampleMessage:
        """セッションにメッセージを追加します。

        Args:
            session_id: セッションID（データベースID）
            role: メッセージの役割（user/assistant/system）
            content: メッセージの内容
            tokens_used: 使用されたトークン数（オプション）
            model: 使用されたモデル名（オプション）

        Returns:
            SampleMessage: 作成されたメッセージ
        """
        message = SampleMessage(
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model=model,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def delete_session(self, session_id: str) -> bool:
        """セッションを削除します。

        Args:
            session_id: セッション識別子

        Returns:
            bool: 削除成功の場合True、セッションが存在しない場合False
        """
        session = await self.get_by_session_id(session_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.flush()
        return True
