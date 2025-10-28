"""エージェントサービスのテスト。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.sample_user import SampleUser
from app.services.sample_agent import SampleAgentService


class TestSampleAgentService:
    """SampleAgentServiceのテストクラス。"""

    @pytest.mark.asyncio
    async def test_chat_creates_new_session(self, db_session: AsyncSession):
        """新しいセッションでチャットできること。"""
        # Arrange
        service = SampleAgentService(db_session)
        message = "Hello, AI!"

        # Act
        result = await service.chat(message=message)

        # Assert
        assert "response" in result
        assert "session_id" in result
        assert result["session_id"].startswith("session_")
        assert "エコー: Hello, AI!" == result["response"]
        assert result["model"] == "echo-v1"
        assert result["tokens_used"] > 0

    @pytest.mark.asyncio
    async def test_chat_with_existing_session(self, db_session: AsyncSession):
        """既存のセッションでチャットできること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # 最初のメッセージで新しいセッションを作成
        first_result = await service.chat(message="First message")
        session_id = first_result["session_id"]

        # Act - 同じセッションで2つ目のメッセージ
        second_result = await service.chat(
            message="Second message",
            session_id=session_id,
        )

        # Assert
        assert second_result["session_id"] == session_id
        assert "エコー: Second message" == second_result["response"]

    @pytest.mark.asyncio
    async def test_chat_with_user_id(self, db_session: AsyncSession):
        """ユーザーIDを指定してチャットできること。"""
        # Arrange
        user = SampleUser(
            email="chat@example.com",
            username="chatuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = SampleAgentService(db_session)

        # Act
        result = await service.chat(
            message="User message",
            user_id=user.id,
        )

        # Assert
        assert result["session_id"] is not None
        # セッションを取得してuser_idを確認
        session = await service.get_session(result["session_id"])
        assert session.user_id == user.id

    @pytest.mark.asyncio
    async def test_chat_with_context(self, db_session: AsyncSession):
        """コンテキストを指定してチャットできること。"""
        # Arrange
        service = SampleAgentService(db_session)
        context = {"source": "web", "device": "mobile"}

        # Act
        result = await service.chat(
            message="Context message",
            context=context,
        )

        # Assert
        session = await service.get_session(result["session_id"])
        assert session.session_metadata == context

    @pytest.mark.asyncio
    async def test_chat_empty_message_error(self, db_session: AsyncSession):
        """空のメッセージでエラーが発生すること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # Act & Assert - 空文字列
        with pytest.raises(ValidationError) as exc_info:
            await service.chat(message="")

        assert "メッセージは空にできません" in str(exc_info.value)

        # Act & Assert - 空白のみ
        with pytest.raises(ValidationError):
            await service.chat(message="   ")

    @pytest.mark.asyncio
    async def test_chat_invalid_session_id_error(self, db_session: AsyncSession):
        """存在しないセッションIDでエラーが発生すること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.chat(
                message="Test message",
                session_id="non-existent-session",
            )

        assert "セッションが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_saves_messages(self, db_session: AsyncSession):
        """チャットでメッセージが保存されること。"""
        # Arrange
        service = SampleAgentService(db_session)
        message = "Test message"

        # Act
        result = await service.chat(message=message)

        # Assert - セッションを取得してメッセージを確認
        session = await service.get_session(result["session_id"])
        assert len(session.messages) == 2  # ユーザーメッセージ + アシスタントメッセージ

        user_message = session.messages[0]
        assistant_message = session.messages[1]

        assert user_message.role == "user"
        assert user_message.content == message

        assert assistant_message.role == "assistant"
        assert "エコー:" in assistant_message.content
        assert assistant_message.model == "echo-v1"
        assert assistant_message.tokens_used is not None and assistant_message.tokens_used > 0

    @pytest.mark.asyncio
    async def test_get_session(self, db_session: AsyncSession):
        """セッションの取得が成功すること。"""
        # Arrange
        service = SampleAgentService(db_session)
        chat_result = await service.chat(message="Test")
        session_id = chat_result["session_id"]

        # Act
        session = await service.get_session(session_id)

        # Assert
        assert session.session_id == session_id
        assert len(session.messages) == 2

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, db_session: AsyncSession):
        """存在しないセッションの取得でエラーが発生すること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.get_session("non-existent-session")

    @pytest.mark.asyncio
    async def test_delete_session(self, db_session: AsyncSession):
        """セッションの削除が成功すること。"""
        # Arrange
        service = SampleAgentService(db_session)
        chat_result = await service.chat(message="Test")
        session_id = chat_result["session_id"]

        # Act
        result = await service.delete_session(session_id)

        # Assert
        assert result is True
        # 削除されたセッションの取得でエラーが発生すること
        with pytest.raises(NotFoundError):
            await service.get_session(session_id)

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, db_session: AsyncSession):
        """存在しないセッションの削除でエラーが発生すること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.delete_session("non-existent-session")

    def test_generate_response(self, db_session: AsyncSession):
        """レスポンス生成が正しく動作すること。"""
        # Arrange
        service = SampleAgentService(db_session)
        message = "Hello"

        # Act
        response = service._generate_response(message)

        # Assert
        assert response == "エコー: Hello"

    def test_generate_response_with_context(self, db_session: AsyncSession):
        """コンテキスト付きレスポンス生成が正しく動作すること。"""
        # Arrange
        service = SampleAgentService(db_session)
        message = "Test"
        context = {"key": "value"}

        # Act
        response = service._generate_response(message, context)

        # Assert
        assert "エコー:" in response
        assert "Test" in response

    def test_generate_session_id(self, db_session: AsyncSession):
        """セッションIDの生成が正しく動作すること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # Act
        session_id1 = service._generate_session_id()
        session_id2 = service._generate_session_id()

        # Assert
        assert session_id1.startswith("session_")
        assert session_id2.startswith("session_")
        assert session_id1 != session_id2  # 異なるIDが生成される

    @pytest.mark.asyncio
    async def test_chat_conversation_flow(self, db_session: AsyncSession):
        """複数回のチャットで会話フローが正しく動作すること。"""
        # Arrange
        service = SampleAgentService(db_session)

        # Act - 会話フロー
        result1 = await service.chat(message="Message 1")
        session_id = result1["session_id"]

        _result2 = await service.chat(message="Message 2", session_id=session_id)
        _result3 = await service.chat(message="Message 3", session_id=session_id)

        # Assert
        session = await service.get_session(session_id)
        assert len(session.messages) == 6  # 3つのユーザーメッセージ + 3つのアシスタントメッセージ

        # メッセージの順序を確認
        roles = [msg.role for msg in session.messages]
        expected_roles = ["user", "assistant", "user", "assistant", "user", "assistant"]
        assert roles == expected_roles
