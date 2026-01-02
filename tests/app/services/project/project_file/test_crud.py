"""ProjectFileServiceのテスト。"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from app.core.exceptions import AuthorizationError, NotFoundError, PayloadTooLargeError, ValidationError
from app.models import Project, ProjectMember, ProjectRole, UserAccount
from app.services import ProjectFileService
from app.services.project.project_file import MAX_FILE_SIZE
from app.services.storage.validation import sanitize_filename


class TestProjectFileService:
    """ProjectFileServiceのテストクラス。"""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, db_session):
        """[test_project_file-001] ファイルアップロード成功のテスト。"""
        # Arrange
        user = UserAccount(
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

        file_content = b"Test file content"
        file = MagicMock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"

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

    @pytest.mark.parametrize(
        "role,is_member,expected_error_msg",
        [
            (None, False, "not a member"),
            (ProjectRole.VIEWER, True, "Insufficient permissions"),
        ],
        ids=["non_member", "viewer_no_permission"],
    )
    @pytest.mark.asyncio
    async def test_upload_file_permission_denied(self, db_session, role, is_member, expected_error_msg):
        """[test_project_file-002] アップロード権限不足テスト。"""
        # Arrange
        user = UserAccount(
            azure_oid="permission-test-oid",
            email="permissiontest@company.com",
            display_name="Permission Test User",
        )
        project = Project(
            name="Permission Test Project",
            code="PERM-001",
        )
        db_session.add(user)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(project)

        # メンバーとして追加（is_memberがTrueの場合のみ）
        if is_member:
            member = ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role=role,
            )
            db_session.add(member)
            await db_session.commit()

        service = ProjectFileService(db_session)
        file = MagicMock(spec=UploadFile)
        file.filename = "test.txt"
        file.content_type = "text/plain"

        # Act & Assert
        with pytest.raises(AuthorizationError) as exc_info:
            await service.upload_file(project.id, file, uploaded_by=user.id)

        assert expected_error_msg in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_upload_file_invalid_mime_type(self, db_session):
        """[test_project_file-004] 無効なMIMEタイプのアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
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
        file = MagicMock(spec=UploadFile)
        file.filename = "test.exe"
        file.content_type = "application/x-msdownload"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.upload_file(project.id, file, uploaded_by=user.id)

        assert "許可されていないファイル形式です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_exceeds_size_limit(self, db_session):
        """[test_project_file-005] ファイルサイズ超過のアップロード失敗テスト。"""
        # Arrange
        user = UserAccount(
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
        file = MagicMock(spec=UploadFile)
        file.filename = "large.txt"
        file.content_type = "text/plain"

        # Act & Assert
        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                with pytest.raises(PayloadTooLargeError) as exc_info:
                    await service.upload_file(project.id, file, uploaded_by=user.id)

                assert "ファイルサイズが許可されている最大サイズ" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_file_success(self, db_session):
        """[test_project_file-006] ファイル取得成功のテスト。"""
        # Arrange
        user = UserAccount(
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

        # ファイルをアップロード（MEMBERロールで）
        member.role = ProjectRole.MEMBER
        await db_session.commit()

        file_content = b"Test content"
        file = MagicMock(spec=UploadFile)
        file.filename = "get.txt"
        file.content_type = "text/plain"

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
        """[test_project_file-007] 存在しないファイルの取得テスト。"""
        # Arrange
        user = UserAccount(
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
    async def test_list_project_files(self, db_session):
        """[test_project_file-008] プロジェクトファイル一覧取得のテスト。"""
        # Arrange
        user = UserAccount(
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

        # 複数のファイルをアップロード
        for i in range(3):
            file_content = f"File {i}".encode()
            file = MagicMock(spec=UploadFile)
            file.filename = f"list{i}.txt"
            file.content_type = "text/plain"

            with patch.object(file, "read", return_value=file_content):
                with patch.object(file, "seek", return_value=None):
                    await service.upload_file(project.id, file, uploaded_by=user.id)

        # Act
        files, total = await service.list_project_files(project.id, user.id)

        # Assert
        assert len(files) == 3
        assert total == 3

    @pytest.mark.asyncio
    async def test_delete_file_by_uploader(self, db_session):
        """[test_project_file-009] アップロード者によるファイル削除のテスト。"""
        # Arrange
        user = UserAccount(
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

        # ファイルをアップロード
        file_content = b"Delete test"
        file = MagicMock(spec=UploadFile)
        file.filename = "delete.txt"
        file.content_type = "text/plain"

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(project.id, file, uploaded_by=user.id)

        # Act
        result = await service.delete_file(uploaded_file.id, user.id)

        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "deleter_role,can_delete,expected_result",
        [
            (ProjectRole.PROJECT_MANAGER, True, True),
            (ProjectRole.MEMBER, False, AuthorizationError),
        ],
        ids=["admin_can_delete", "member_cannot_delete"],
    )
    @pytest.mark.asyncio
    async def test_delete_file_by_different_roles(self, db_session, deleter_role, can_delete, expected_result):
        """[test_project_file-010] 異なるロールによるファイル削除のテスト。"""
        # Arrange
        uploader = UserAccount(
            azure_oid="uploader-oid",
            email="uploader@company.com",
            display_name="Uploader",
        )
        deleter = UserAccount(
            azure_oid="deleter-oid",
            email="deleter@company.com",
            display_name="Deleter",
        )
        project = Project(
            name="Delete Test Project",
            code="DELTEST-001",
        )
        db_session.add(uploader)
        db_session.add(deleter)
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(uploader)
        await db_session.refresh(deleter)
        await db_session.refresh(project)

        # uploaderをMEMBERとして追加
        uploader_member = ProjectMember(
            project_id=project.id,
            user_id=uploader.id,
            role=ProjectRole.MEMBER,
        )
        # deleterを指定されたロールとして追加
        deleter_member = ProjectMember(
            project_id=project.id,
            user_id=deleter.id,
            role=deleter_role,
        )
        db_session.add(uploader_member)
        db_session.add(deleter_member)
        await db_session.commit()

        service = ProjectFileService(db_session)

        # uploaderがファイルをアップロード
        file_content = b"Delete test content"
        file = MagicMock(spec=UploadFile)
        file.filename = "delete_test.txt"
        file.content_type = "text/plain"

        with patch.object(file, "read", return_value=file_content):
            with patch.object(file, "seek", return_value=None):
                uploaded_file = await service.upload_file(project.id, file, uploaded_by=uploader.id)

        # Act & Assert
        if can_delete:
            result = await service.delete_file(uploaded_file.id, deleter.id)
            assert result is expected_result
        else:
            with pytest.raises(expected_result) as exc_info:
                await service.delete_file(uploaded_file.id, deleter.id)
            assert "ファイルのアップロード者またはプロジェクト管理者のみが削除できます" in str(exc_info.value)

    def test_sanitize_filename(self):
        """[test_project_file-012] ファイル名サニタイズのテスト。"""
        # Act & Assert
        assert sanitize_filename("test.txt") == "test.txt"
        assert sanitize_filename("file<>name.txt") == "filename.txt"
        assert sanitize_filename('file"name.txt') == "filename.txt"
        # os.path.basename を使用するため、パス区切り文字の後の部分のみ残る
        assert sanitize_filename("file/name.txt") == "name.txt"
        assert sanitize_filename("file\\name.txt") == "name.txt"
        assert sanitize_filename("__file.txt__") == "file.txt"
        assert sanitize_filename("...file.txt...") == "file.txt"
        assert sanitize_filename("") == "unknown"
        assert sanitize_filename("   ") == "unknown"
