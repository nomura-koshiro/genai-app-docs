"""AIエージェントサービス。

このモジュールは、AIエージェントとのチャット機能を提供します。
最低限の実装として、エコーバック機能を提供しています。
"""

import secrets
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import SampleSession
from app.repositories import SampleSessionRepository

logger = get_logger(__name__)


class SampleAgentService:
    """AIエージェントサービス。

    AIエージェントとのチャット、セッション管理を提供します。
    現在は最低限の実装として、シンプルなエコーバック機能を提供しています。

    Note:
        本格的なAI機能を実装する場合は、LangChainやLangGraphを統合してください。
    """

    def __init__(self, db: AsyncSession):
        """エージェントサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = SampleSessionRepository(db)

    @measure_performance
    @async_timeout(300.0)
    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        user_id: uuid.UUID | None = None,
        context: dict | None = None,
    ) -> dict:
        """AIエージェントとチャットします。

        最低限の実装として、ユーザーメッセージをエコーバックします。
        セッションIDが指定されない場合は、新しいセッションを作成します。

        Args:
            message: ユーザーメッセージ
            session_id: セッション識別子（オプション）
            user_id: ユーザーID（オプション）
            context: 追加コンテキスト情報（オプション）

        Returns:
            dict: レスポンス情報
                - response: エージェントの応答メッセージ
                - session_id: セッション識別子
                - tokens_used: 使用されたトークン数（オプション）
                - model: 使用されたモデル名（オプション）

        Raises:
            ValidationError: メッセージが空の場合
        """
        if not message or not message.strip():
            raise ValidationError("メッセージは空にできません")

        logger.info(
            "チャットリクエスト受信",
            session_id=session_id,
            user_id=user_id,
            message_length=len(message),
        )

        # セッションの取得または作成
        if session_id:
            session = await self.repository.get_by_session_id(session_id)
            if not session:
                raise NotFoundError(
                    f"セッションが見つかりません: {session_id}",
                    details={"session_id": session_id},
                )
        else:
            # 新しいセッションを作成
            session_id = self._generate_session_id()
            session = await self.repository.create_session(session_id=session_id, user_id=user_id, metadata=context)
            await self.db.commit()
            logger.info("新しいセッションを作成しました", session_id=session_id)

        # ユーザーメッセージを保存
        await self.repository.add_message(session_id=session.id, role="user", content=message)

        # AIレスポンスを生成（最低限の実装：エコーバック）
        ai_response = self._generate_response(message, context)

        # アシスタントメッセージを保存
        await self.repository.add_message(
            session_id=session.id,
            role="assistant",
            content=ai_response,
            tokens_used=len(message) + len(ai_response),  # 簡易的なトークン数
            model="echo-v1",
        )

        await self.db.commit()

        logger.info(
            "チャットレスポンス生成完了",
            session_id=session_id,
            response_length=len(ai_response),
        )

        return {
            "response": ai_response,
            "session_id": session_id,
            "tokens_used": len(message) + len(ai_response),
            "model": "echo-v1",
        }

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

    def _generate_response(self, message: str, context: dict | None = None) -> str:
        """AIレスポンスを生成します。

        最低限の実装として、シンプルなエコーバックを提供します。

        Args:
            message: ユーザーメッセージ
            context: 追加コンテキスト情報

        Returns:
            str: エージェントの応答メッセージ

        Note:
            本格的なAI機能を実装する場合は、このメソッドを拡張してください。
            例: LangChainのチェーンを使用、OpenAI APIを呼び出し、など
        """
        # 最低限の実装：エコーバック
        return f"エコー: {message}"
