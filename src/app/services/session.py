"""ビジネスロジック用のセッションサービス。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.session import Message, Session
from app.repositories.session import SessionRepository


class SessionService:
    """セッション関連のビジネスロジック用サービス。"""

    def __init__(self, db: AsyncSession):
        """セッションサービスを初期化します。

        Args:
            db: データベースセッション
        """
        self.repository = SessionRepository(db)

    async def create_session(
        self, user_id: int | None = None, metadata: dict | None = None
    ) -> Session:
        """新しいセッションを作成します。

        Args:
            user_id: オプションのユーザーID
            metadata: オプションのセッションメタデータ

        Returns:
            作成されたセッションインスタンス
        """
        session_id = str(uuid.uuid4())
        session = await self.repository.create(
            session_id=session_id, user_id=user_id, metadata=metadata
        )
        return session

    async def get_session(self, session_id: str) -> Session:
        """session_idによってセッションを取得します。

        Args:
            session_id: セッション識別子

        Returns:
            セッションインスタンス

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        session = await self.repository.get_by_session_id(session_id)
        if not session:
            raise NotFoundError("Session not found", details={"session_id": session_id})
        return session

    async def delete_session(self, session_id: str) -> bool:
        """セッションを削除します。

        Args:
            session_id: セッション識別子

        Returns:
            削除された場合はTrue

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        session = await self.repository.get_by_session_id(session_id)
        if not session:
            raise NotFoundError("Session not found", details={"session_id": session_id})

        await self.repository.delete(session.id)
        return True

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: int | None = None,
        model: str | None = None,
    ) -> Message:
        """セッションにメッセージを追加します。

        Args:
            session_id: セッション識別子
            role: メッセージの役割（user/assistant/system）
            content: メッセージの内容
            tokens_used: 使用されたトークン数
            model: 生成に使用されたモデル

        Returns:
            作成されたメッセージインスタンス

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        session = await self.get_session(session_id)
        message = await self.repository.add_message(
            session_id=session.id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model=model,
        )
        return message

    async def get_user_sessions(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Session]:
        """ユーザーのセッションを取得します。

        Args:
            user_id: ユーザーID
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            ユーザーセッションのリスト
        """
        return await self.repository.get_user_sessions(
            user_id=user_id, skip=skip, limit=limit
        )
