"""セッションサービスのテスト。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.sample_user import SampleUser
from app.services.sample_session import SampleSessionService


class TestSampleSessionService:
    """SampleSessionServiceのテストクラス。"""

    @pytest.mark.asyncio
    async def test_create_session(self, db_session: AsyncSession):
        """セッションの作成が成功すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # Act
        session = await service.create_session()

        # Assert
        assert session.id is not None
        assert session.session_id.startswith("session_")
        assert session.user_id is None
        assert session.session_metadata is None

    @pytest.mark.asyncio
    async def test_create_session_with_user(self, db_session: AsyncSession):
        """ユーザー所有のセッションの作成が成功すること。"""
        # Arrange
        user = SampleUser(
            email="session@example.com",
            username="sessionuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = SampleSessionService(db_session)

        # Act
        session = await service.create_session(user_id=user.id)

        # Assert
        assert session.user_id == user.id

    @pytest.mark.asyncio
    async def test_create_session_with_metadata(self, db_session: AsyncSession):
        """メタデータ付きセッションの作成が成功すること。"""
        # Arrange
        service = SampleSessionService(db_session)
        metadata = {"source": "web", "device": "desktop"}

        # Act
        session = await service.create_session(metadata=metadata)

        # Assert
        assert session.session_metadata == metadata

    @pytest.mark.asyncio
    async def test_get_session(self, db_session: AsyncSession):
        """セッションの取得が成功すること。"""
        # Arrange
        service = SampleSessionService(db_session)
        created_session = await service.create_session()

        # Act
        session = await service.get_session(created_session.session_id)

        # Assert
        assert session.id == created_session.id
        assert session.session_id == created_session.session_id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, db_session: AsyncSession):
        """存在しないセッションの取得でエラーが発生すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_session("non-existent-session")

        assert "セッションが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_session(self, db_session: AsyncSession):
        """セッションの更新が成功すること。"""
        # Arrange
        service = SampleSessionService(db_session)
        session = await service.create_session()
        new_metadata = {"updated": True, "version": 2}

        # Act
        updated_session = await service.update_session(
            session.session_id,
            metadata=new_metadata,
        )

        # Assert
        assert updated_session.session_metadata == new_metadata

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, db_session: AsyncSession):
        """存在しないセッションの更新でエラーが発生すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.update_session("non-existent-session", metadata={})

    @pytest.mark.asyncio
    async def test_delete_session(self, db_session: AsyncSession):
        """セッションの削除が成功すること。"""
        # Arrange
        service = SampleSessionService(db_session)
        session = await service.create_session()

        # Act
        result = await service.delete_session(session.session_id)

        # Assert
        assert result is True
        # 削除されたセッションの取得でエラーが発生すること
        with pytest.raises(NotFoundError):
            await service.get_session(session.session_id)

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, db_session: AsyncSession):
        """存在しないセッションの削除でエラーが発生すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.delete_session("non-existent-session")

    @pytest.mark.asyncio
    async def test_list_sessions(self, db_session: AsyncSession):
        """セッション一覧の取得が成功すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # 複数のセッションを作成
        for _ in range(3):
            await service.create_session()

        # Act
        sessions, total = await service.list_sessions()

        # Assert
        assert len(sessions) >= 3
        assert total >= 3

    @pytest.mark.asyncio
    async def test_list_sessions_with_user_filter(self, db_session: AsyncSession):
        """ユーザーIDでフィルタしたセッション一覧の取得が成功すること。"""
        # Arrange
        user1 = SampleUser(email="user1@example.com", username="user1", hashed_password="pass")
        user2 = SampleUser(email="user2@example.com", username="user2", hashed_password="pass")
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        service = SampleSessionService(db_session)

        # user1のセッションを2つ作成
        for _ in range(2):
            await service.create_session(user_id=user1.id)

        # user2のセッションを1つ作成
        await service.create_session(user_id=user2.id)

        # Act
        user1_sessions, user1_total = await service.list_sessions(user_id=user1.id)
        user2_sessions, user2_total = await service.list_sessions(user_id=user2.id)

        # Assert
        assert len(user1_sessions) == 2
        assert user1_total == 2
        assert len(user2_sessions) == 1
        assert user2_total == 1
        assert all(s.user_id == user1.id for s in user1_sessions)
        assert all(s.user_id == user2.id for s in user2_sessions)

    @pytest.mark.asyncio
    async def test_list_sessions_with_pagination(self, db_session: AsyncSession):
        """ページネーションが正しく動作すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # 10個のセッションを作成
        for _ in range(10):
            await service.create_session()

        # Act
        first_page, total1 = await service.list_sessions(skip=0, limit=3)
        second_page, total2 = await service.list_sessions(skip=3, limit=3)

        # Assert
        assert len(first_page) == 3
        assert len(second_page) == 3
        assert total1 == total2  # 総数は同じ
        assert total1 >= 10

        # 異なるセッションが取得されること
        first_ids = {s.session_id for s in first_page}
        second_ids = {s.session_id for s in second_page}
        assert len(first_ids & second_ids) == 0  # 重複なし

    @pytest.mark.asyncio
    async def test_list_sessions_ordered_by_updated_at(self, db_session: AsyncSession):
        """セッション一覧が更新日時の降順でソートされていること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # セッションを作成
        session1 = await service.create_session()
        _session2 = await service.create_session()
        _session3 = await service.create_session()

        # session1を更新（最新にする）
        await service.update_session(session1.session_id, metadata={"updated": True})

        # Act
        sessions, _ = await service.list_sessions(limit=3)

        # Assert
        assert len(sessions) >= 3
        # 更新したsession1が最初に来ること
        session_ids = [s.session_id for s in sessions[:3]]
        assert session1.session_id == session_ids[0]

    def test_generate_session_id(self, db_session: AsyncSession):
        """セッションIDの生成が正しく動作すること。"""
        # Arrange
        service = SampleSessionService(db_session)

        # Act
        session_id1 = service._generate_session_id()
        session_id2 = service._generate_session_id()

        # Assert
        assert session_id1.startswith("session_")
        assert session_id2.startswith("session_")
        assert session_id1 != session_id2  # 異なるIDが生成される
