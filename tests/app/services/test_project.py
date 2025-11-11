"""プロジェクトサービスのテスト。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project import ProjectService


@pytest.mark.asyncio
async def test_create_project_success(db_session: AsyncSession):
    """プロジェクト作成の成功ケース。"""
    # Arrange
    service = ProjectService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"creator-{uuid.uuid4()}@example.com",
        display_name="Creator User",
    )
    db_session.add(user)
    await db_session.commit()

    project_data = ProjectCreate(
        name="Test Project",
        code="TEST-001",
        description="Test description",
    )

    # Act
    project = await service.create_project(project_data, creator_id)
    await db_session.commit()

    # Assert
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.code == "TEST-001"
    assert project.created_by == creator_id

@pytest.mark.asyncio
async def test_create_project_duplicate_code(db_session: AsyncSession):
    """重複コードでのプロジェクト作成エラー。"""
    # Arrange
    service = ProjectService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"creator-{uuid.uuid4()}@example.com",
        display_name="Creator User",
    )
    db_session.add(user)
    await db_session.commit()

    # 最初のプロジェクトを作成
    first_project = ProjectCreate(
        name="First Project",
        code="DUP-001",
        description="First project",
    )
    await service.create_project(first_project, creator_id)
    await db_session.commit()

    # Act & Assert - 同じコードで再度作成しようとするとエラー
    duplicate_project = ProjectCreate(
        name="Duplicate Project",
        code="DUP-001",
        description="Duplicate project",
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.create_project(duplicate_project, creator_id)

    assert "既に使用されています" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_get_project_success(db_session: AsyncSession):
    """プロジェクト取得の成功ケース。"""
    # Arrange
    service = ProjectService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"creator-{uuid.uuid4()}@example.com",
        display_name="Creator User",
    )
    db_session.add(user)
    await db_session.commit()

    project_data = ProjectCreate(
        name="Get Test",
        code=f"GET-{uuid.uuid4().hex[:6]}",
        description="Get test",
    )
    created_project = await service.create_project(project_data, creator_id)
    await db_session.commit()

    # Act
    result = await service.get_project(created_project.id)

    # Assert
    assert result is not None
    assert result.id == created_project.id
    assert result.name == "Get Test"

@pytest.mark.asyncio
async def test_get_project_not_found(db_session: AsyncSession):
    """存在しないプロジェクトの取得。"""
    # Arrange
    service = ProjectService(db_session)
    nonexistent_id = uuid.uuid4()

    # Act
    result = await service.get_project(nonexistent_id)

    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_project_by_code_success(db_session: AsyncSession):
    """コードによるプロジェクト取得の成功ケース。"""
    # Arrange
    service = ProjectService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"creator-{uuid.uuid4()}@example.com",
        display_name="Creator User",
    )
    db_session.add(user)
    await db_session.commit()

    project_data = ProjectCreate(
        name="Code Test",
        code=f"CODE-{uuid.uuid4().hex[:6]}",
        description="Code test",
    )
    created_project = await service.create_project(project_data, creator_id)
    await db_session.commit()

    # Act
    result = await service.get_project_by_code(created_project.code)

    # Assert
    assert result is not None
    assert result.code == created_project.code

@pytest.mark.asyncio
async def test_get_project_by_code_not_found(db_session: AsyncSession):
    """存在しないコードでのプロジェクト取得。"""
    # Arrange
    service = ProjectService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_project_by_code("NONEXISTENT")

@pytest.mark.asyncio
async def test_list_user_projects(db_session: AsyncSession):
    """ユーザーのプロジェクト一覧取得。"""
    # Arrange
    service = ProjectService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"user-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # プロジェクトを作成
    project1_data = ProjectCreate(
        name="User Project 1",
        code=f"UP1-{uuid.uuid4().hex[:6]}",
        description="User project 1",
    )
    project2_data = ProjectCreate(
        name="User Project 2",
        code=f"UP2-{uuid.uuid4().hex[:6]}",
        description="User project 2",
    )

    await service.create_project(project1_data, user_id)
    await service.create_project(project2_data, user_id)
    await db_session.commit()

    # Act
    result = await service.list_user_projects(user_id)

    # Assert
    assert len(result) == 2

@pytest.mark.asyncio
async def test_update_project_success(db_session: AsyncSession):
    """プロジェクト更新の成功ケース（OWNERロール）。"""
    # Arrange
    service = ProjectService(db_session)
    owner_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=owner_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"owner-{uuid.uuid4()}@example.com",
        display_name="Owner User",
    )
    db_session.add(user)
    await db_session.commit()

    project_data = ProjectCreate(
        name="Original Name",
        code=f"UPD-{uuid.uuid4().hex[:6]}",
        description="Original description",
    )
    project = await service.create_project(project_data, owner_id)
    await db_session.commit()

    # Act
    update_data = ProjectUpdate(
        name="Updated Name",
        description="Updated description",
    )
    updated = await service.update_project(project.id, update_data, owner_id)
    await db_session.commit()

    # Assert
    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"

@pytest.mark.asyncio
async def test_update_project_permission_denied(db_session: AsyncSession):
    """権限のないユーザーによる更新エラー。"""
    # Arrange
    service = ProjectService(db_session)
    owner_id = uuid.uuid4()
    viewer_id = uuid.uuid4()

    # ユーザーを作成
    owner = User(
        id=owner_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"owner-{uuid.uuid4()}@example.com",
        display_name="Owner User",
    )
    viewer = User(
        id=viewer_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"viewer-{uuid.uuid4()}@example.com",
        display_name="Viewer User",
    )
    db_session.add(owner)
    db_session.add(viewer)
    await db_session.commit()

    # プロジェクトを作成
    project_data = ProjectCreate(
        name="Test Project",
        code=f"PERM-{uuid.uuid4().hex[:6]}",
        description="Test description",
    )
    project = await service.create_project(project_data, owner_id)

    # VIEWERとして追加
    viewer_member = ProjectMember(
        project_id=project.id,
        user_id=viewer_id,
        role=ProjectRole.VIEWER,
        added_by=owner_id,
    )
    db_session.add(viewer_member)
    await db_session.commit()

    # Act & Assert - VIEWERは更新できない
    update_data = ProjectUpdate(name="Updated by Viewer")

    with pytest.raises(AuthorizationError):
        await service.update_project(project.id, update_data, viewer_id)

@pytest.mark.asyncio
async def test_delete_project_success(db_session: AsyncSession):
    """プロジェクト削除の成功ケース（OWNERロール）。"""
    # Arrange
    service = ProjectService(db_session)
    owner_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=owner_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"owner-{uuid.uuid4()}@example.com",
        display_name="Owner User",
    )
    db_session.add(user)
    await db_session.commit()

    project_data = ProjectCreate(
        name="To Delete",
        code=f"DEL-{uuid.uuid4().hex[:6]}",
        description="To be deleted",
    )
    project = await service.create_project(project_data, owner_id)
    await db_session.commit()
    project_id = project.id

    # Act
    await service.delete_project(project_id, owner_id)
    await db_session.commit()

    # Assert - 削除されたことを確認
    deleted = await service.get_project(project_id)
    assert deleted is None

@pytest.mark.asyncio
async def test_delete_project_permission_denied(db_session: AsyncSession):
    """権限のないユーザーによる削除エラー。"""
    # Arrange
    service = ProjectService(db_session)
    owner_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    # ユーザーを作成
    owner = User(
        id=owner_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"owner-{uuid.uuid4()}@example.com",
        display_name="Owner User",
    )
    admin = User(
        id=admin_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(owner)
    db_session.add(admin)
    await db_session.commit()

    # プロジェクトを作成
    project_data = ProjectCreate(
        name="Test Project",
        code=f"DELPERM-{uuid.uuid4().hex[:6]}",
        description="Test description",
    )
    project = await service.create_project(project_data, owner_id)

    # ADMINとして追加
    admin_member = ProjectMember(
        project_id=project.id,
        user_id=admin_id,
        role=ProjectRole.PROJECT_MANAGER,
        added_by=owner_id,
    )
    db_session.add(admin_member)
    await db_session.commit()

    # Act & Assert - ADMINは削除できない（OWNERのみ）
    with pytest.raises(AuthorizationError):
        await service.delete_project(project.id, admin_id)

@pytest.mark.asyncio
async def test_check_user_access(db_session: AsyncSession):
    """ユーザーアクセスチェック。"""
    # Arrange
    service = ProjectService(db_session)
    owner_id = uuid.uuid4()
    member_id = uuid.uuid4()
    non_member_id = uuid.uuid4()

    # ユーザーを作成
    owner = User(
        id=owner_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"owner-{uuid.uuid4()}@example.com",
        display_name="Owner User",
    )
    member = User(
        id=member_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"member-{uuid.uuid4()}@example.com",
        display_name="Member User",
    )
    db_session.add(owner)
    db_session.add(member)
    await db_session.commit()

    # プロジェクトを作成
    project_data = ProjectCreate(
        name="Access Test",
        code=f"ACCESS-{uuid.uuid4().hex[:6]}",
        description="Access test",
    )
    project = await service.create_project(project_data, owner_id)

    # MEMBERとして追加
    member_obj = ProjectMember(
        project_id=project.id,
        user_id=member_id,
        role=ProjectRole.MEMBER,
        added_by=owner_id,
    )
    db_session.add(member_obj)
    await db_session.commit()

    # Act & Assert
    # OWNERはアクセス可能
    assert await service.check_user_access(project.id, owner_id) is True

    # MEMBERはアクセス可能
    assert await service.check_user_access(project.id, member_id) is True

    # 非メンバーはアクセス不可
    assert await service.check_user_access(project.id, non_member_id) is False

@pytest.mark.asyncio
async def test_delete_project_without_files(db_session: AsyncSession):
    """ファイルのないプロジェクトの削除が成功すること。"""
    # Arrange
    service = ProjectService(db_session)
    owner_id = uuid.uuid4()

    # ユーザーを作成
    user = User(
        id=owner_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"owner-{uuid.uuid4()}@example.com",
        display_name="Owner User",
    )
    db_session.add(user)
    await db_session.commit()

    # プロジェクトを作成（ファイルなし）
    project_data = ProjectCreate(
        name="Project without Files",
        code=f"DELNOFILE-{uuid.uuid4().hex[:6]}",
        description="Test project without files",
    )
    project = await service.create_project(project_data, owner_id)
    await db_session.commit()
    project_id = project.id

    # Act: プロジェクト削除
    await service.delete_project(project_id, owner_id)
    await db_session.commit()

    # Assert: プロジェクトが削除されたことを確認
    deleted_project = await service.get_project(project_id)
    assert deleted_project is None
