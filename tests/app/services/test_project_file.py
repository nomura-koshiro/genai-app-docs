"""ProjectFileServiceのテスト。"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.services.project_file import MAX_FILE_SIZE, ProjectFileService


class TestProjectFileService:
    """ProjectFileServiceのテストクラス。"""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, db_session, tmp_path):
        """ファイルアップロード成功のテスト。"""
        # Arrange
        user = User(
            azure_oid="upload-user-oid",
            email="uploaduser@company.com",
            display_name="Upload User",
        )
        project = Project(
            name="Upload Project",
            code="UPLOAD-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # メンバーとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        service.upload_dir = tmp_path

        file_content = b"Test file content"
        mock_file = MagicMock()
        file = UploadFile(filename="test.pdf", file=mock_file)
        type(file).content_type = property(lambda self: "application/pdf")

        # Act
        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                result = await service.upload_file(project.id, file, uploaded_by=user.id)

        # Assert
        assert result.filename == "test.pdf"
        assert result.original_filename == "test.pdf"
        assert result.file_size == len(file_content)
        assert result.mime_type == "application/pdf"
        assert result.uploaded_by == user.id

    @pytest.mark.asyncio
    async def test_upload_file_not_member(self, db_session):
        """非メンバーのアップロード失敗テスト。"""
        # Arrange
        user = User(
            azure_oid="non-member-oid",
            email="nonmember@company.com",
            display_name="Non Member",
        )
        project = Project(
            name="Non Member Project",
            code="NONMEMBER-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        service = ProjectFileService(db_session)
        mock_file = MagicMock()
        file = UploadFile(filename="test.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        # Act & Assert
        with pytest.raises(AuthorizationError) as exc_info:
            await service.upload_file(project.id, file, uploaded_by=user.id)

        assert "not a member" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_upload_file_viewer_no_permission(self, db_session):
        """VIEWERロールのアップロード失敗テスト。"""
        # Arrange
        user = User(
            azure_oid="viewer-oid",
            email="viewer@company.com",
            display_name="Viewer User",
        )
        project = Project(
            name="Viewer Project",
            code="VIEWER-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # VIEWERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.VIEWER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        mock_file = MagicMock()
        file = UploadFile(filename="test.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        # Act & Assert
        with pytest.raises(AuthorizationError) as exc_info:
            await service.upload_file(project.id, file, uploaded_by=user.id)

        assert "Insufficient permissions" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_invalid_mime_type(self, db_session):
        """無効なMIMEタイプのアップロード失敗テスト。"""
        # Arrange
        user = User(
            azure_oid="mime-user-oid",
            email="mimeuser@company.com",
            display_name="MIME User",
        )
        project = Project(
            name="MIME Project",
            code="MIME-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        mock_file = MagicMock()
        file = UploadFile(filename="test.exe", file=mock_file)
        type(file).content_type = property(lambda self: "application/x-msdownload")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.upload_file(project.id, file, uploaded_by=user.id)

        assert "許可されていないファイルタイプです" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_exceeds_size_limit(self, db_session):
        """ファイルサイズ超過のアップロード失敗テスト。"""
        # Arrange
        user = User(
            azure_oid="size-user-oid",
            email="sizeuser@company.com",
            display_name="Size User",
        )
        project = Project(
            name="Size Project",
            code="SIZE-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        file_content = b"x" * (MAX_FILE_SIZE + 1)
        mock_file = MagicMock()
        file = UploadFile(filename="large.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        # Act & Assert
        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                with pytest.raises(ValidationError) as exc_info:
                    await service.upload_file(project.id, file, uploaded_by=user.id)

                assert "ファイルサイズが大きすぎます" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_file_success(self, db_session, tmp_path):
        """ファイル取得成功のテスト。"""
        # Arrange
        user = User(
            azure_oid="get-user-oid",
            email="getuser@company.com",
            display_name="Get User",
        )
        project = Project(
            name="Get Project",
            code="GET-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.VIEWER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        service.upload_dir = tmp_path

        # ファイルをアップロード（MEMBERロールで）
        member.role = ProjectRole.MEMBER
        await db_session.commit()

        file_content = b"Test content"
        mock_file = MagicMock()
        file = UploadFile(filename="get.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(project.id, file, uploaded_by=user.id)

        # VIEWERに戻す
        member.role = ProjectRole.VIEWER
        await db_session.commit()

        # Act
        result = await service.get_file(uploaded_file.id, user.id)

        # Assert
        assert result.id == uploaded_file.id
        assert result.filename == "get.txt"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, db_session):
        """存在しないファイルの取得テスト。"""
        # Arrange
        user = User(
            azure_oid="notfound-user-oid",
            email="notfounduser@company.com",
            display_name="Not Found User",
        )
        project = Project(
            name="Not Found Project",
            code="NOTFOUND-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.VIEWER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        non_existent_id = uuid.uuid4()

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.get_file(non_existent_id, user.id)

    @pytest.mark.asyncio
    async def test_list_project_files(self, db_session, tmp_path):
        """プロジェクトファイル一覧取得のテスト。"""
        # Arrange
        user = User(
            azure_oid="list-user-oid",
            email="listuser@company.com",
            display_name="List User",
        )
        project = Project(
            name="List Project",
            code="LIST-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        service.upload_dir = tmp_path

        # 複数のファイルをアップロード
        for i in range(3):
            file_content = f"File {i}".encode()
            mock_file = MagicMock()
            file = UploadFile(filename=f"list{i}.txt", file=mock_file)
            type(file).content_type = property(lambda self: "text/plain")

            with patch.object(file, "read", return_value=file_content):
                with patch.object(file, "seek", return_value=None):
                    await service.upload_file(project.id, file, uploaded_by=user.id)

        # Act
        files, total = await service.list_project_files(project.id, user.id)

        # Assert
        assert len(files) == 3
        assert total == 3

    @pytest.mark.asyncio
    async def test_delete_file_by_uploader(self, db_session, tmp_path):
        """アップロード者によるファイル削除のテスト。"""
        # Arrange
        user = User(
            azure_oid="delete-user-oid",
            email="deleteuser@company.com",
            display_name="Delete User",
        )
        project = Project(
            name="Delete Project",
            code="DELETE-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        service.upload_dir = tmp_path

        # ファイルをアップロード
        file_content = b"Delete test"
        mock_file = MagicMock()
        file = UploadFile(filename="delete.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(project.id, file, uploaded_by=user.id)

        # Act
        result = await service.delete_file(uploaded_file.id, user.id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_by_admin(self, db_session, tmp_path):
        """ADMIN による他人のファイル削除のテスト。"""
        # Arrange
        uploader = User(
            azure_oid="uploader-oid",
            email="uploader@company.com",
            display_name="Uploader",
        )
        admin = User(
            azure_oid="admin-oid",
            email="admin@company.com",
            display_name="Admin",
        )
        project = Project(
            name="Admin Delete Project",
            code="ADMINDEL-001",
        )
        db_session.add(uploader)
        db_session.add(admin)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(uploader)
        await db_session.refresh(admin)
        await db_session.refresh(project)

        # uploaderをMEMBERとして追加
        uploader_member = ProjectMember(
            project_id=project.id,
            user_id=uploader.id,
            role=ProjectRole.MEMBER,
        )
        # adminをADMINとして追加
        admin_member = ProjectMember(
            project_id=project.id,
            user_id=admin.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        db_session.add(uploader_member)
        db_session.add(admin_member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        service.upload_dir = tmp_path

        # uploaderがファイルをアップロード
        file_content = b"Admin delete test"
        mock_file = MagicMock()
        file = UploadFile(filename="admindel.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(project.id, file, uploaded_by=uploader.id)

        # Act - adminが削除
        result = await service.delete_file(uploaded_file.id, admin.id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_by_member_no_permission(self, db_session, tmp_path):
        """一般MEMBERによる他人のファイル削除失敗のテスト。"""
        # Arrange
        uploader = User(
            azure_oid="uploader2-oid",
            email="uploader2@company.com",
            display_name="Uploader2",
        )
        other_member = User(
            azure_oid="othermember-oid",
            email="othermember@company.com",
            display_name="Other Member",
        )
        project = Project(
            name="Member Delete Project",
            code="MEMBERDEL-001",
        )
        db_session.add(uploader)
        db_session.add(other_member)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(uploader)
        await db_session.refresh(other_member)
        await db_session.refresh(project)

        # 両方をMEMBERとして追加
        uploader_member = ProjectMember(
            project_id=project.id,
            user_id=uploader.id,
            role=ProjectRole.MEMBER,
        )
        other_member_member = ProjectMember(
            project_id=project.id,
            user_id=other_member.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(uploader_member)
        db_session.add(other_member_member)
        await db_session.commit()

        service = ProjectFileService(db_session)
        service.upload_dir = tmp_path

        # uploaderがファイルをアップロード
        file_content = b"Member delete test"
        mock_file = MagicMock()
        file = UploadFile(filename="memberdel.txt", file=mock_file)
        type(file).content_type = property(lambda self: "text/plain")

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(project.id, file, uploaded_by=uploader.id)

        # Act & Assert - other_memberが削除しようとする
        with pytest.raises(AuthorizationError) as exc_info:
            await service.delete_file(uploaded_file.id, other_member.id)

        assert "Only the file uploader or project admin/owner" in str(exc_info.value)

    def test_sanitize_filename(self, db_session):
        """ファイル名サニタイズのテスト。"""
        # Arrange
        service = ProjectFileService(db_session)

        # Act & Assert
        assert service._sanitize_filename("test.txt") == "test.txt"
        assert service._sanitize_filename("file<>name.txt") == "filename.txt"
        assert service._sanitize_filename('file"name.txt') == "filename.txt"
        assert service._sanitize_filename("file/name.txt") == "filename.txt"
        assert service._sanitize_filename("file\\name.txt") == "filename.txt"
        assert service._sanitize_filename("  file.txt  ") == "file.txt"
        assert service._sanitize_filename("...file.txt...") == "file.txt"
        assert service._sanitize_filename("") == "unnamed_file"
        assert service._sanitize_filename("   ") == "unnamed_file"
