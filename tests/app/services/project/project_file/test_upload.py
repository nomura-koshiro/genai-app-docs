"""ProjectFileUploadServiceのテスト。"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from app.core.exceptions import AuthorizationError, NotFoundError, PayloadTooLargeError, ValidationError
from app.models import Project, ProjectFile, ProjectMember, ProjectRole, UserAccount
from app.services.project.project_file.upload import ALLOWED_MIME_TYPES, ProjectFileUploadService


class TestProjectFileUploadService:
    """ProjectFileUploadServiceのテストクラス。"""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, db_session, mock_storage_service):
        """[test_upload-001] ファイルアップロード成功のテスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-success-oid",
            email="uploadsuccess@company.com",
            display_name="Upload Success User",
        )
        project = Project(
            name="Upload Success Project",
            code="UPLOAD-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        file_content = b"Test file content for upload"
        file = MagicMock(spec=UploadFile)
        file.filename = "test_upload.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock(return_value=None)

        mock_storage_service.upload.return_value = True

        # Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            result = await service.upload_file(project.id, file, user.id)

        # Assert
        assert result.filename == "test_upload.pdf"
        assert result.original_filename == "test_upload.pdf"
        assert result.file_size == len(file_content)
        assert result.mime_type == "application/pdf"
        assert result.uploaded_by == user.id
        assert result.project_id == project.id
        mock_storage_service.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_as_project_manager(self, db_session, mock_storage_service):
        """[test_upload-002] PROJECT_MANAGERロールでのアップロード成功テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-manager-oid",
            email="uploadmanager@company.com",
            display_name="Upload Manager",
        )
        project = Project(
            name="Upload Manager Project",
            code="UPLOAD-002",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # PROJECT_MANAGERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.PROJECT_MANAGER,
        )
        db_session.add(member)
        await db_session.commit()

        file_content = b"Manager upload content"
        file = MagicMock(spec=UploadFile)
        file.filename = "manager_upload.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock(return_value=None)

        mock_storage_service.upload.return_value = True

        # Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            result = await service.upload_file(project.id, file, user.id)

        # Assert
        assert result.filename == "manager_upload.pdf"
        assert result.uploaded_by == user.id

    @pytest.mark.asyncio
    async def test_upload_file_viewer_no_permission(self, db_session, mock_storage_service):
        """[test_upload-003] VIEWERロールでのアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-viewer-oid",
            email="uploadviewer@company.com",
            display_name="Upload Viewer",
        )
        project = Project(
            name="Upload Viewer Project",
            code="UPLOAD-003",
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

        file = MagicMock(spec=UploadFile)
        file.filename = "viewer_upload.pdf"
        file.content_type = "application/pdf"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(AuthorizationError) as exc_info:
                await service.upload_file(project.id, file, user.id)

        assert "Insufficient permissions" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_not_member(self, db_session, mock_storage_service):
        """[test_upload-004] 非メンバーによるアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-nonmember-oid",
            email="uploadnonmember@company.com",
            display_name="Upload Non Member",
        )
        project = Project(
            name="Upload Non Member Project",
            code="UPLOAD-004",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # メンバーとして追加しない

        file = MagicMock(spec=UploadFile)
        file.filename = "nonmember_upload.pdf"
        file.content_type = "application/pdf"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(AuthorizationError) as exc_info:
                await service.upload_file(project.id, file, user.id)

        assert "not a member" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_upload_file_no_filename(self, db_session, mock_storage_service):
        """[test_upload-005] ファイル名なしでのアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-noname-oid",
            email="uploadnoname@company.com",
            display_name="Upload No Name",
        )
        project = Project(
            name="Upload No Name Project",
            code="UPLOAD-005",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        file = MagicMock(spec=UploadFile)
        file.filename = None  # ファイル名なし
        file.content_type = "application/pdf"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(ValidationError) as exc_info:
                await service.upload_file(project.id, file, user.id)

        assert "ファイル名が必要です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_invalid_mime_type(self, db_session, mock_storage_service):
        """[test_upload-006] 無効なMIMEタイプでのアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-invalidmime-oid",
            email="uploadinvalidmime@company.com",
            display_name="Upload Invalid MIME",
        )
        project = Project(
            name="Upload Invalid MIME Project",
            code="UPLOAD-006",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        file = MagicMock(spec=UploadFile)
        file.filename = "malicious.exe"
        file.content_type = "application/x-msdownload"  # 許可されていないMIMEタイプ

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(ValidationError) as exc_info:
                await service.upload_file(project.id, file, user.id)

        assert "許可されていないファイル形式です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_exceeds_size_limit(self, db_session, mock_storage_service):
        """[test_upload-007] ファイルサイズ超過でのアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-toolarge-oid",
            email="uploadtoolarge@company.com",
            display_name="Upload Too Large",
        )
        project = Project(
            name="Upload Too Large Project",
            code="UPLOAD-007",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        # 50MB + 1 byte（最大サイズを超える）
        max_size = 50 * 1024 * 1024
        file_content = b"x" * (max_size + 1)
        file = MagicMock(spec=UploadFile)
        file.filename = "large_file.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock(return_value=None)

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(PayloadTooLargeError) as exc_info:
                await service.upload_file(project.id, file, user.id)

        assert "ファイルサイズが許可されている最大サイズ" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_storage_failure_cleanup(self, db_session, mock_storage_service):
        """[test_upload-008] ストレージ保存後のDB保存失敗時のクリーンアップテスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="upload-cleanup-oid",
            email="uploadcleanup@company.com",
            display_name="Upload Cleanup",
        )
        project = Project(
            name="Upload Cleanup Project",
            code="UPLOAD-008",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        file_content = b"Test file content"
        file = MagicMock(spec=UploadFile)
        file.filename = "cleanup_test.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock(return_value=None)

        mock_storage_service.upload.return_value = True
        mock_storage_service.exists.return_value = True
        mock_storage_service.delete.return_value = True

        # リポジトリのcreateでエラーを発生させる
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)

            # repositoryのcreateをモックしてエラーを発生させる
            with patch.object(service.repository, "create", side_effect=Exception("DB Error")):
                with pytest.raises(Exception) as exc_info:
                    await service.upload_file(project.id, file, user.id)

                assert "DB Error" in str(exc_info.value)
                # ストレージからファイルが削除されることを確認
                mock_storage_service.delete.assert_called_once()


class TestProjectFileUploadServiceNewVersion:
    """ProjectFileUploadService.upload_new_versionのテストクラス。"""

    @pytest.mark.asyncio
    async def test_upload_new_version_success(self, db_session, mock_storage_service):
        """[test_upload-009] 新バージョンアップロード成功のテスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="version-success-oid",
            email="versionsuccess@company.com",
            display_name="Version Success User",
        )
        project = Project(
            name="Version Success Project",
            code="VERSION-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        # 親ファイルを作成
        parent_file_id = uuid.uuid4()
        parent_file = ProjectFile(
            id=parent_file_id,
            project_id=project.id,
            filename="original.pdf",
            original_filename="original.pdf",
            file_path=f"projects/{project.id}/{parent_file_id}_original.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=user.id,
            version=1,
            is_latest=True,
        )
        db_session.add(parent_file)
        await db_session.commit()

        file_content = b"New version content"
        file = MagicMock(spec=UploadFile)
        file.filename = "original_v2.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock(return_value=None)

        mock_storage_service.upload.return_value = True

        # Act
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            result = await service.upload_new_version(parent_file_id, file, user.id)

        # Assert
        assert result.version == 2
        assert result.parent_file_id == parent_file_id
        assert result.is_latest is True
        assert result.original_filename == "original.pdf"  # 元のファイル名を引き継ぐ
        assert result.file_size == len(file_content)

        # 親ファイルのis_latestがFalseになっていることを確認
        await db_session.refresh(parent_file)
        assert parent_file.is_latest is False

    @pytest.mark.asyncio
    async def test_upload_new_version_parent_not_found(self, db_session, mock_storage_service):
        """[test_upload-010] 親ファイルが存在しない場合の新バージョンアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="version-notfound-oid",
            email="versionnotfound@company.com",
            display_name="Version Not Found User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        non_existent_parent_id = uuid.uuid4()

        file = MagicMock(spec=UploadFile)
        file.filename = "new_version.pdf"
        file.content_type = "application/pdf"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(NotFoundError) as exc_info:
                await service.upload_new_version(non_existent_parent_id, file, user.id)

        assert "親ファイルが見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_new_version_viewer_no_permission(self, db_session, mock_storage_service):
        """[test_upload-011] VIEWERロールでの新バージョンアップロード失敗テスト。"""
        # Arrange
        uploader = UserAccount(
            azure_oid="version-uploader-oid",
            email="versionuploader@company.com",
            display_name="Version Uploader",
        )
        viewer = UserAccount(
            azure_oid="version-viewer-oid",
            email="versionviewer@company.com",
            display_name="Version Viewer",
        )
        project = Project(
            name="Version Viewer Project",
            code="VERSION-002",
        )
        db_session.add(uploader)
        db_session.add(viewer)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(uploader)
        await db_session.refresh(viewer)
        await db_session.refresh(project)

        # uploaderをMEMBER、viewerをVIEWERとして追加
        uploader_member = ProjectMember(
            project_id=project.id,
            user_id=uploader.id,
            role=ProjectRole.MEMBER,
        )
        viewer_member = ProjectMember(
            project_id=project.id,
            user_id=viewer.id,
            role=ProjectRole.VIEWER,
        )
        db_session.add(uploader_member)
        db_session.add(viewer_member)
        await db_session.commit()

        # 親ファイルを作成
        parent_file_id = uuid.uuid4()
        parent_file = ProjectFile(
            id=parent_file_id,
            project_id=project.id,
            filename="parent.pdf",
            original_filename="parent.pdf",
            file_path=f"projects/{project.id}/{parent_file_id}_parent.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=uploader.id,
            version=1,
            is_latest=True,
        )
        db_session.add(parent_file)
        await db_session.commit()

        file = MagicMock(spec=UploadFile)
        file.filename = "new_version.pdf"
        file.content_type = "application/pdf"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(AuthorizationError) as exc_info:
                await service.upload_new_version(parent_file_id, file, viewer.id)

        assert "Insufficient permissions" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_new_version_invalid_mime_type(self, db_session, mock_storage_service):
        """[test_upload-012] 無効なMIMEタイプでの新バージョンアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="version-invalidmime-oid",
            email="versioninvalidmime@company.com",
            display_name="Version Invalid MIME",
        )
        project = Project(
            name="Version Invalid MIME Project",
            code="VERSION-003",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        # 親ファイルを作成
        parent_file_id = uuid.uuid4()
        parent_file = ProjectFile(
            id=parent_file_id,
            project_id=project.id,
            filename="valid.pdf",
            original_filename="valid.pdf",
            file_path=f"projects/{project.id}/{parent_file_id}_valid.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=user.id,
            version=1,
            is_latest=True,
        )
        db_session.add(parent_file)
        await db_session.commit()

        file = MagicMock(spec=UploadFile)
        file.filename = "malicious.exe"
        file.content_type = "application/x-msdownload"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(ValidationError) as exc_info:
                await service.upload_new_version(parent_file_id, file, user.id)

        assert "許可されていないファイル形式です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_new_version_no_filename(self, db_session, mock_storage_service):
        """[test_upload-013] ファイル名なしでの新バージョンアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="version-noname-oid",
            email="versionnoname@company.com",
            display_name="Version No Name",
        )
        project = Project(
            name="Version No Name Project",
            code="VERSION-004",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # MEMBERとして追加
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        # 親ファイルを作成
        parent_file_id = uuid.uuid4()
        parent_file = ProjectFile(
            id=parent_file_id,
            project_id=project.id,
            filename="parent.pdf",
            original_filename="parent.pdf",
            file_path=f"projects/{project.id}/{parent_file_id}_parent.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=user.id,
            version=1,
            is_latest=True,
        )
        db_session.add(parent_file)
        await db_session.commit()

        file = MagicMock(spec=UploadFile)
        file.filename = None
        file.content_type = "application/pdf"

        # Act & Assert
        with patch("app.services.storage.get_storage_service", return_value=mock_storage_service):
            service = ProjectFileUploadService(db_session)
            with pytest.raises(ValidationError) as exc_info:
                await service.upload_new_version(parent_file_id, file, user.id)

        assert "ファイル名が必要です" in str(exc_info.value)


class TestAllowedMimeTypes:
    """許可されたMIMEタイプのテスト。"""

    def test_allowed_mime_types_contains_expected_types(self):
        """[test_upload-014] ALLOWED_MIME_TYPESが期待されるMIMEタイプを含むテスト。"""
        # Assert
        assert "image/jpeg" in ALLOWED_MIME_TYPES
        assert "image/png" in ALLOWED_MIME_TYPES
        assert "image/gif" in ALLOWED_MIME_TYPES
        assert "application/pdf" in ALLOWED_MIME_TYPES
        assert "text/plain" in ALLOWED_MIME_TYPES
        assert "text/csv" in ALLOWED_MIME_TYPES
        # Word
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in ALLOWED_MIME_TYPES
        # Excel
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in ALLOWED_MIME_TYPES

    def test_allowed_mime_types_does_not_contain_dangerous_types(self):
        """[test_upload-015] ALLOWED_MIME_TYPESが危険なMIMEタイプを含まないテスト。"""
        # Assert - 危険なMIMEタイプが含まれていないことを確認
        dangerous_types = [
            "application/x-msdownload",  # .exe
            "application/x-msdos-program",  # .exe
            "application/javascript",  # .js
            "application/x-sh",  # .sh
            "application/x-bat",  # .bat
        ]

        for dangerous_type in dangerous_types:
            assert dangerous_type not in ALLOWED_MIME_TYPES
