"""ProjectFileRepositoryのテスト。

このテストファイルは REPOSITORY_TEST_POLICY.md に従い、
複雑なクエリやカスタムメソッドのみをテストします。

基本的なCRUD操作はサービス層のテストでカバーされます。
"""

import pytest

from app.models import Project, ProjectFile, UserAccount
from app.repositories import ProjectFileRepository


@pytest.mark.asyncio
async def test_get_file_with_uploader(db_session):
    """ファイル取得（uploader情報含む）のテスト。

    複雑なクエリ: selectinloadによるリレーションシップの取得。
    N+1問題を防ぐため、uploaderを同時に取得する重要な実装。
    """
    # Arrange
    user = User(
        azure_oid="get-file-oid",
        email="getfile@company.com",
        display_name="Get File User",
    )
    project = Project(
        name="Get File Project",
        code="GETFILE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    file = ProjectFile(
        project_id=project.id,
        filename="get.txt",
        original_filename="get-test.txt",
        file_path="uploads/get.txt",
        file_size=512,
        uploaded_by=user.id,
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)

    repository = ProjectFileRepository(db_session)

    # Act
    retrieved_file = await repository.get(file.id)

    # Assert
    assert retrieved_file is not None
    assert retrieved_file.id == file.id
    assert retrieved_file.uploader is not None  # selectinloadで取得されている
    assert retrieved_file.uploader.id == user.id
    assert retrieved_file.uploader.display_name == "Get File User"


@pytest.mark.asyncio
async def test_list_by_project(db_session):
    """プロジェクトファイル一覧取得のテスト。

    複雑なクエリ: プロジェクト別一覧 + uploaded_at降順ソート + selectinload。
    ファイル一覧画面で使用され、アップロード日時順に並べる。
    """
    # Arrange
    user = User(
        azure_oid="list-file-oid",
        email="listfile@company.com",
        display_name="List File User",
    )
    project = Project(
        name="List File Project",
        code="LISTFILE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # 複数のファイルを作成
    for i in range(3):
        file = ProjectFile(
            project_id=project.id,
            filename=f"file{i}.txt",
            original_filename=f"file-{i}.txt",
            file_path=f"uploads/file{i}.txt",
            file_size=100 * (i + 1),
            uploaded_by=user.id,
        )
        db_session.add(file)
    await db_session.commit()

    repository = ProjectFileRepository(db_session)

    # Act
    files = await repository.list_by_project(project.id)

    # Assert
    assert len(files) == 3
    # 降順でソートされている（最新が先頭）
    assert files[0].filename == "file2.txt"
    # uploader情報が含まれている
    assert all(f.uploader is not None for f in files)


@pytest.mark.asyncio
async def test_count_by_project(db_session):
    """プロジェクトのファイル数カウントのテスト。

    カスタムクエリ: プロジェクト別ファイル数のCOUNT集計。
    プロジェクトダッシュボードでのファイル統計表示に使用される。
    """
    # Arrange
    user = User(
        azure_oid="count-file-oid",
        email="countfile@company.com",
        display_name="Count File User",
    )
    project = Project(
        name="Count File Project",
        code="COUNTFILE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # 3つのファイルを作成
    for i in range(3):
        file = ProjectFile(
            project_id=project.id,
            filename=f"count{i}.txt",
            original_filename=f"count-{i}.txt",
            file_path=f"uploads/count{i}.txt",
            file_size=100,
            uploaded_by=user.id,
        )
        db_session.add(file)
    await db_session.commit()

    repository = ProjectFileRepository(db_session)

    # Act
    count = await repository.count_by_project(project.id)

    # Assert
    assert count == 3


@pytest.mark.asyncio
async def test_get_total_size_by_project(db_session):
    """プロジェクトの合計ファイルサイズ取得のテスト。

    カスタムクエリ: プロジェクト別ファイルサイズのSUM集計。
    ストレージ使用量の監視やクォータ管理で使用される重要な機能。
    """
    # Arrange
    user = User(
        azure_oid="size-file-oid",
        email="sizefile@company.com",
        display_name="Size File User",
    )
    project = Project(
        name="Size File Project",
        code="SIZEFILE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # サイズの異なるファイルを作成
    sizes = [1024, 2048, 4096]
    for i, size in enumerate(sizes):
        file = ProjectFile(
            project_id=project.id,
            filename=f"size{i}.txt",
            original_filename=f"size-{i}.txt",
            file_path=f"uploads/size{i}.txt",
            file_size=size,
            uploaded_by=user.id,
        )
        db_session.add(file)
    await db_session.commit()

    repository = ProjectFileRepository(db_session)

    # Act
    total_size = await repository.get_total_size_by_project(project.id)

    # Assert
    assert total_size == sum(sizes)
