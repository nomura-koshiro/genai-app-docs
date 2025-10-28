"""ファイルモデルのテスト。"""

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sample_file import SampleFile
from app.models.sample_user import SampleUser


class TestSampleFileModel:
    """SampleFileモデルのテストクラス。"""

    @pytest.mark.asyncio
    async def test_create_file_success(self, db_session: AsyncSession):
        """ファイルの作成が成功すること。"""
        # Arrange
        file = SampleFile(
            file_id="test-file-123",
            filename="test.txt",
            filepath="/uploads/test.txt",
            size=1024,
            content_type="text/plain",
        )

        # Act
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        # Assert
        assert file.id is not None
        assert file.file_id == "test-file-123"
        assert file.filename == "test.txt"
        assert file.filepath == "/uploads/test.txt"
        assert file.size == 1024
        assert file.content_type == "text/plain"
        assert file.user_id is None  # ゲストユーザー
        assert isinstance(file.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_file_with_user(self, db_session: AsyncSession):
        """ユーザー所有のファイルの作成が成功すること。"""
        # Arrange - まずユーザーを作成
        user = SampleUser(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        file = SampleFile(
            file_id="user-file-123",
            user_id=user.id,
            filename="user_file.txt",
            filepath="/uploads/user_file.txt",
            size=2048,
            content_type="text/plain",
        )

        # Act
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        # Assert
        assert file.user_id == user.id
        assert file.filename == "user_file.txt"

    @pytest.mark.asyncio
    async def test_file_id_unique_constraint(self, db_session: AsyncSession):
        """file_idのユニーク制約が機能すること。"""
        # Arrange - 同じfile_idで2つのファイルを作成
        file1 = SampleFile(
            file_id="duplicate-file-id",
            filename="file1.txt",
            filepath="/uploads/file1.txt",
            size=100,
            content_type="text/plain",
        )
        db_session.add(file1)
        await db_session.commit()

        file2 = SampleFile(
            file_id="duplicate-file-id",  # 重複
            filename="file2.txt",
            filepath="/uploads/file2.txt",
            size=200,
            content_type="text/plain",
        )
        db_session.add(file2)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_deletion_sets_null(self, db_session: AsyncSession):
        """ユーザー削除時にファイルのuser_idがNULLになること。"""
        # Arrange
        user = SampleUser(
            email="delete@example.com",
            username="deleteuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        file = SampleFile(
            file_id="orphan-file",
            user_id=user.id,
            filename="orphan.txt",
            filepath="/uploads/orphan.txt",
            size=500,
            content_type="text/plain",
        )
        db_session.add(file)
        await db_session.commit()

        # Act - ユーザーを削除
        await db_session.delete(user)
        await db_session.commit()

        # Assert - ファイルは残り、user_idがNULLになる
        result = await db_session.execute(select(SampleFile).filter_by(file_id="orphan-file"))
        orphaned_file = result.scalar_one()
        assert orphaned_file.user_id is None

    @pytest.mark.asyncio
    async def test_file_repr(self, db_session: AsyncSession):
        """__repr__メソッドが正しく動作すること。"""
        # Arrange
        file = SampleFile(
            file_id="repr-test",
            filename="repr.txt",
            filepath="/uploads/repr.txt",
            size=100,
            content_type="text/plain",
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        # Act
        repr_str = repr(file)

        # Assert
        assert "SampleFile" in repr_str
        assert f"id={file.id}" in repr_str
        assert "file_id=repr-test" in repr_str
        assert "filename=repr.txt" in repr_str

    @pytest.mark.asyncio
    async def test_file_required_fields(self, db_session: AsyncSession):
        """必須フィールドが欠けている場合にエラーが発生すること。"""
        # Arrange - file_idを省略
        file = SampleFile(
            filename="missing_fileid.txt",
            filepath="/uploads/missing.txt",
            size=100,
            content_type="text/plain",
        )
        db_session.add(file)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_file_content_types(self, db_session: AsyncSession):
        """様々なコンテンツタイプのファイルを作成できること。"""
        # Arrange
        files = [
            SampleFile(
                file_id=f"file-{i}",
                filename=f"file{i}.{ext}",
                filepath=f"/uploads/file{i}.{ext}",
                size=1024 * i,
                content_type=content_type,
            )
            for i, (ext, content_type) in enumerate(
                [
                    ("txt", "text/plain"),
                    ("pdf", "application/pdf"),
                    ("jpg", "image/jpeg"),
                    ("png", "image/png"),
                    ("json", "application/json"),
                ],
                start=1,
            )
        ]

        # Act
        for file in files:
            db_session.add(file)
        await db_session.commit()

        # Assert
        result = await db_session.execute(select(SampleFile))
        saved_files = result.scalars().all()
        assert len(saved_files) >= 5
        content_types = [f.content_type for f in saved_files]
        assert "text/plain" in content_types
        assert "application/pdf" in content_types
        assert "image/jpeg" in content_types
