"""ファイルリポジトリのテスト。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sample_user import SampleUser
from app.repositories.sample_file import SampleFileRepository


class TestSampleFileRepository:
    """SampleFileRepositoryのテストクラス。"""

    @pytest.mark.asyncio
    async def test_create_file(self, db_session: AsyncSession):
        """ファイルの作成が成功すること。"""
        # Arrange
        repository = SampleFileRepository(db_session)

        # Act
        file = await repository.create_file(
            file_id="test-file-123",
            filename="test.txt",
            filepath="/uploads/test.txt",
            size=1024,
            content_type="text/plain",
        )

        # Assert
        assert file.id is not None
        assert file.file_id == "test-file-123"
        assert file.filename == "test.txt"
        assert file.filepath == "/uploads/test.txt"
        assert file.size == 1024
        assert file.content_type == "text/plain"
        assert file.user_id is None

    @pytest.mark.asyncio
    async def test_create_file_with_user(self, db_session: AsyncSession):
        """ユーザー所有のファイルの作成が成功すること。"""
        # Arrange
        user = SampleUser(
            email="file@example.com",
            username="fileuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repository = SampleFileRepository(db_session)

        # Act
        file = await repository.create_file(
            file_id="user-file-123",
            filename="user_file.txt",
            filepath="/uploads/user_file.txt",
            size=2048,
            content_type="text/plain",
            user_id=user.id,
        )

        # Assert
        assert file.user_id == user.id

    @pytest.mark.asyncio
    async def test_get_by_file_id(self, db_session: AsyncSession):
        """file_idでファイルを取得できること。"""
        # Arrange
        repository = SampleFileRepository(db_session)
        created_file = await repository.create_file(
            file_id="get-test-file",
            filename="get_test.txt",
            filepath="/uploads/get_test.txt",
            size=500,
            content_type="text/plain",
        )
        await db_session.commit()

        # Act
        file = await repository.get_by_file_id("get-test-file")

        # Assert
        assert file is not None
        assert file.id == created_file.id
        assert file.file_id == "get-test-file"

    @pytest.mark.asyncio
    async def test_get_by_file_id_not_found(self, db_session: AsyncSession):
        """存在しないfile_idでNoneが返されること。"""
        # Arrange
        repository = SampleFileRepository(db_session)

        # Act
        file = await repository.get_by_file_id("non-existent-file")

        # Assert
        assert file is None

    @pytest.mark.asyncio
    async def test_delete_file(self, db_session: AsyncSession):
        """ファイルの削除が成功すること。"""
        # Arrange
        repository = SampleFileRepository(db_session)
        await repository.create_file(
            file_id="delete-test-file",
            filename="delete_test.txt",
            filepath="/uploads/delete_test.txt",
            size=100,
            content_type="text/plain",
        )
        await db_session.commit()

        # Act
        result = await repository.delete_file("delete-test-file")
        await db_session.commit()

        # Assert
        assert result is True
        deleted_file = await repository.get_by_file_id("delete-test-file")
        assert deleted_file is None

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, db_session: AsyncSession):
        """存在しないファイルの削除でFalseが返されること。"""
        # Arrange
        repository = SampleFileRepository(db_session)

        # Act
        result = await repository.delete_file("non-existent-file")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_list_files(self, db_session: AsyncSession):
        """ファイル一覧の取得が成功すること。"""
        # Arrange
        repository = SampleFileRepository(db_session)
        for i in range(5):
            await repository.create_file(
                file_id=f"list-file-{i}",
                filename=f"file{i}.txt",
                filepath=f"/uploads/file{i}.txt",
                size=100 * i,
                content_type="text/plain",
            )
        await db_session.commit()

        # Act
        files = await repository.list_files()

        # Assert
        assert len(files) >= 5
        file_ids = [f.file_id for f in files]
        assert "list-file-0" in file_ids

    @pytest.mark.asyncio
    async def test_list_files_with_user_filter(self, db_session: AsyncSession):
        """ユーザーIDでフィルタしたファイル一覧の取得が成功すること。"""
        # Arrange
        user1 = SampleUser(email="user1@example.com", username="user1", hashed_password="pass")
        user2 = SampleUser(email="user2@example.com", username="user2", hashed_password="pass")
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        repository = SampleFileRepository(db_session)

        # user1のファイルを3つ作成
        for i in range(3):
            await repository.create_file(
                file_id=f"user1-file-{i}",
                filename=f"user1_file{i}.txt",
                filepath=f"/uploads/user1_file{i}.txt",
                size=100,
                content_type="text/plain",
                user_id=user1.id,
            )

        # user2のファイルを2つ作成
        for i in range(2):
            await repository.create_file(
                file_id=f"user2-file-{i}",
                filename=f"user2_file{i}.txt",
                filepath=f"/uploads/user2_file{i}.txt",
                size=100,
                content_type="text/plain",
                user_id=user2.id,
            )
        await db_session.commit()

        # Act
        user1_files = await repository.list_files(user_id=user1.id)
        user2_files = await repository.list_files(user_id=user2.id)

        # Assert
        assert len(user1_files) == 3
        assert len(user2_files) == 2
        assert all(f.user_id == user1.id for f in user1_files)
        assert all(f.user_id == user2.id for f in user2_files)

    @pytest.mark.asyncio
    async def test_list_files_with_pagination(self, db_session: AsyncSession):
        """ページネーションが正しく動作すること。"""
        # Arrange
        repository = SampleFileRepository(db_session)
        for i in range(10):
            await repository.create_file(
                file_id=f"page-file-{i}",
                filename=f"page{i}.txt",
                filepath=f"/uploads/page{i}.txt",
                size=100,
                content_type="text/plain",
            )
        await db_session.commit()

        # Act
        first_page = await repository.list_files(skip=0, limit=3)
        second_page = await repository.list_files(skip=3, limit=3)

        # Assert
        assert len(first_page) == 3
        assert len(second_page) == 3
        # 異なるファイルが取得されること
        first_ids = {f.file_id for f in first_page}
        second_ids = {f.file_id for f in second_page}
        assert len(first_ids & second_ids) == 0  # 重複なし

    @pytest.mark.asyncio
    async def test_list_files_ordered_by_created_at(self, db_session: AsyncSession):
        """ファイル一覧が作成日時の降順でソートされていること。"""
        # Arrange
        repository = SampleFileRepository(db_session)
        files_data = [
            ("oldest-file", "oldest.txt"),
            ("middle-file", "middle.txt"),
            ("newest-file", "newest.txt"),
        ]

        for file_id, filename in files_data:
            await repository.create_file(
                file_id=file_id,
                filename=filename,
                filepath=f"/uploads/{filename}",
                size=100,
                content_type="text/plain",
            )
            await db_session.commit()

        # Act
        files = await repository.list_files()

        # Assert
        assert len(files) >= 3
        # 最新のファイルが最初に来ること
        file_ids = [f.file_id for f in files[:3]]
        assert "newest-file" == file_ids[0]
