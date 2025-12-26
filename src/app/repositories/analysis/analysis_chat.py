"""分析チャットリポジトリ。

このモジュールは、AnalysisChatモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analysis import AnalysisChat
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisChatRepository(BaseRepository[AnalysisChat, uuid.UUID]):
    """AnalysisChatモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    チャット履歴管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """チャットリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisChat, db)

    async def list_by_snapshot(self, snapshot_id: uuid.UUID) -> list[AnalysisChat]:
        """スナップショットのチャット一覧を取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            list[AnalysisChat]: チャット一覧（順序順）
        """
        result = await self.db.execute(
            select(AnalysisChat).where(AnalysisChat.snapshot_id == snapshot_id).order_by(AnalysisChat.chat_order.asc())
        )
        return list(result.scalars().all())

    async def get_by_role(
        self,
        snapshot_id: uuid.UUID,
        role: str,
    ) -> list[AnalysisChat]:
        """スナップショット内の特定ロールのチャットを取得します。

        Args:
            snapshot_id: スナップショットID
            role: ロール（user/assistant）

        Returns:
            list[AnalysisChat]: チャット一覧
        """
        result = await self.db.execute(
            select(AnalysisChat)
            .where(AnalysisChat.snapshot_id == snapshot_id)
            .where(AnalysisChat.role == role)
            .order_by(AnalysisChat.chat_order.asc())
        )
        return list(result.scalars().all())

    async def get_max_order(self, snapshot_id: uuid.UUID) -> int:
        """スナップショットの最大チャット順序を取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            int: 最大順序（存在しない場合は-1）
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.max(AnalysisChat.chat_order)).where(AnalysisChat.snapshot_id == snapshot_id))
        max_order = result.scalar_one()
        return max_order if max_order is not None else -1

    async def get_latest(self, snapshot_id: uuid.UUID) -> AnalysisChat | None:
        """スナップショットの最新チャットを取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            AnalysisChat | None: 最新チャット
        """
        result = await self.db.execute(
            select(AnalysisChat).where(AnalysisChat.snapshot_id == snapshot_id).order_by(AnalysisChat.chat_order.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_by_snapshot(self, snapshot_id: uuid.UUID) -> int:
        """スナップショットのチャットをすべて削除します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            int: 削除件数
        """
        result = await self.db.execute(delete(AnalysisChat).where(AnalysisChat.snapshot_id == snapshot_id))
        return result.rowcount

    async def bulk_create(
        self,
        snapshot_id: uuid.UUID,
        chat_list: list[list[str]],
    ) -> list[AnalysisChat]:
        """複数のチャットを一括作成します。

        Args:
            snapshot_id: スナップショットID
            chat_list: チャットのリスト（[["role", "message"], ...]形式）

        Returns:
            list[AnalysisChat]: 作成されたチャット
        """
        # 現在の最大順序を取得
        max_order = await self.get_max_order(snapshot_id)

        chats = []
        for i, (role, message) in enumerate(chat_list):
            chat = AnalysisChat(
                snapshot_id=snapshot_id,
                chat_order=max_order + 1 + i,
                role=role,
                message=message,
            )
            chats.append(chat)

        self.db.add_all(chats)
        await self.db.flush()
        return chats
