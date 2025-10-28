"""ファイルサービスのテスト。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.services.sample_file import MAX_FILE_SIZE, SampleFileService


class TestSampleFileService:
    """SampleFileServiceのテストクラス。"""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, db_session: AsyncSession, tmp_path):
        """ファイルのアップロードが成功すること。"""
        # Arrange
        service = SampleFileService(db_session)
        service.upload_dir = tmp_path  # 一時ディレクトリを使用

        file_content = b"Test file content"
        file = UploadFile(
            filename="test.txt",
            file=MagicMock(read=AsyncMock(return_value=file_content)),
        )
        file.content_type = "text/plain"
        file.seek = AsyncMock()

        # Act
        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                result = await service.upload_file(file)

        # Assert
        assert result.filename == "test.txt"
        assert result.size == len(file_content)
        assert result.content_type == "text/plain"
        assert result.file_id.startswith("file_")
        assert result.user_id is None

    @pytest.mark.asyncio
    async def test_upload_file_with_user(self, db_session: AsyncSession, tmp_path):
        """ユーザー所有のファイルのアップロードが成功すること。"""
        # Arrange
        service = SampleFileService(db_session)
        service.upload_dir = tmp_path

        file_content = b"User file content"
        file = UploadFile(filename="user_file.txt", file=MagicMock())
        file.content_type = "text/plain"

        # Act
        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                result = await service.upload_file(file, user_id=123)

        # Assert
        assert result.user_id == 123

    @pytest.mark.asyncio
    async def test_upload_file_without_filename(self, db_session: AsyncSession):
        """ファイル名がない場合にエラーが発生すること。"""
        # Arrange
        service = SampleFileService(db_session)
        file = UploadFile(filename=None, file=MagicMock())

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.upload_file(file)

        assert "ファイル名が必要です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_invalid_mime_type(self, db_session: AsyncSession):
        """許可されていないMIMEタイプでエラーが発生すること。"""
        # Arrange
        service = SampleFileService(db_session)
        file = UploadFile(filename="test.exe", file=MagicMock())
        file.content_type = "application/x-msdownload"  # 許可されていない

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.upload_file(file)

        assert "許可されていないファイルタイプです" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_exceeds_size_limit(self, db_session: AsyncSession):
        """ファイルサイズが制限を超える場合にエラーが発生すること。"""
        # Arrange
        service = SampleFileService(db_session)
        file_content = b"x" * (MAX_FILE_SIZE + 1)  # 制限を超えるサイズ
        file = UploadFile(filename="large_file.txt", file=MagicMock())
        file.content_type = "text/plain"

        # Act & Assert
        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                with pytest.raises(ValidationError) as exc_info:
                    await service.upload_file(file)

                assert "ファイルサイズが大きすぎます" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_file_success(self, db_session: AsyncSession, tmp_path):
        """ファイルの取得が成功すること。"""
        # Arrange
        service = SampleFileService(db_session)
        service.upload_dir = tmp_path

        # ファイルをアップロード
        file_content = b"Test content"
        file = UploadFile(filename="get_test.txt", file=MagicMock())
        file.content_type = "text/plain"

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(file)

        # Act
        result = await service.get_file(uploaded_file.file_id)

        # Assert
        assert result.file_id == uploaded_file.file_id
        assert result.filename == "get_test.txt"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, db_session: AsyncSession):
        """存在しないファイルの取得でエラーが発生すること。"""
        # Arrange
        service = SampleFileService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_file("non-existent-file-id")

        assert "ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_file_success(self, db_session: AsyncSession, tmp_path):
        """ファイルの削除が成功すること。"""
        # Arrange
        service = SampleFileService(db_session)
        service.upload_dir = tmp_path

        # ファイルをアップロード
        file_content = b"Delete test"
        file = UploadFile(filename="delete_test.txt", file=MagicMock())
        file.content_type = "text/plain"

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(file)

        # Act
        result = await service.delete_file(uploaded_file.file_id)

        # Assert
        assert result is True
        # ファイルが削除されていることを確認
        with pytest.raises(NotFoundError):
            await service.get_file(uploaded_file.file_id)

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, db_session: AsyncSession):
        """存在しないファイルの削除でエラーが発生すること。"""
        # Arrange
        service = SampleFileService(db_session)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.delete_file("non-existent-file-id")

    @pytest.mark.asyncio
    async def test_list_files(self, db_session: AsyncSession, tmp_path):
        """ファイル一覧の取得が成功すること。"""
        # Arrange
        service = SampleFileService(db_session)
        service.upload_dir = tmp_path

        # 複数のファイルをアップロード
        for i in range(3):
            file_content = f"File {i}".encode()
            file = UploadFile(filename=f"list_file_{i}.txt", file=MagicMock())
            file.content_type = "text/plain"

            with patch.object(file, "read", return_value=file_content):
                with patch.object(file, "seek", return_value=None):
                    await service.upload_file(file)

        # Act
        files = await service.list_files()

        # Assert
        assert len(files) >= 3

    @pytest.mark.asyncio
    async def test_list_files_with_user_filter(self, db_session: AsyncSession, tmp_path):
        """ユーザーIDでフィルタしたファイル一覧の取得が成功すること。"""
        # Arrange
        service = SampleFileService(db_session)
        service.upload_dir = tmp_path

        # user1のファイルをアップロード
        for i in range(2):
            file_content = f"User1 File {i}".encode()
            file = UploadFile(filename=f"user1_file_{i}.txt", file=MagicMock())
            file.content_type = "text/plain"

            with patch.object(file, "read", return_value=file_content):
                with patch.object(file, "seek", return_value=None):
                    await service.upload_file(file, user_id=1)

        # user2のファイルをアップロード
        file_content = b"User2 File"
        file = UploadFile(filename="user2_file.txt", file=MagicMock())
        file.content_type = "text/plain"

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                await service.upload_file(file, user_id=2)

        # Act
        user1_files = await service.list_files(user_id=1)
        user2_files = await service.list_files(user_id=2)

        # Assert
        assert len(user1_files) == 2
        assert len(user2_files) == 1
        assert all(f.user_id == 1 for f in user1_files)
        assert all(f.user_id == 2 for f in user2_files)

    def test_generate_file_id(self, db_session: AsyncSession):
        """ファイルIDの生成が正しく動作すること。"""
        # Arrange
        service = SampleFileService(db_session)

        # Act
        file_id1 = service._generate_file_id()
        file_id2 = service._generate_file_id()

        # Assert
        assert file_id1.startswith("file_")
        assert file_id2.startswith("file_")
        assert file_id1 != file_id2  # 異なるIDが生成される

    def test_sanitize_filename(self, db_session: AsyncSession):
        """ファイル名のサニタイズが正しく動作すること。"""
        # Arrange
        service = SampleFileService(db_session)

        # Act & Assert
        assert service._sanitize_filename("test.txt") == "test.txt"
        assert service._sanitize_filename("file<>name.txt") == "filename.txt"
        assert service._sanitize_filename('file"name.txt') == "filename.txt"
        assert service._sanitize_filename("file/name.txt") == "filename.txt"
        assert service._sanitize_filename("  file.txt  ") == "file.txt"
        assert service._sanitize_filename("...file.txt...") == "file.txt"
        assert service._sanitize_filename("") == "unnamed_file"
        assert service._sanitize_filename("   ") == "unnamed_file"
