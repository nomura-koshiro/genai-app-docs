"""ProjectFileモデルのテスト。

このテストファイルは MODEL_TEST_POLICY.md に従い、
データ整合性に関わる制約テストのみを実施します。

基本的なCRUD操作はリポジトリ層・サービス層のテストでカバーされます。
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Project, ProjectFile, UserAccount


@pytest.mark.asyncio
async def test_project_file_cascade_delete_project(db_session):
    """プロジェクト削除時にファイルもカスケード削除されることを確認。

    プロジェクトが削除される際、そのプロジェクトに属するすべてのファイルも
    自動的に削除されることでデータ整合性を保証します。
    """
    # Arrange
    user = UserAccount(
        azure_oid="cascade-file-oid",
        email="filecascade@company.com",
        display_name="File Cascade User",
    )
    project = Project(
        name="File Cascade Project",
        code="FILECASCADE-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # ファイルを追加
    file = ProjectFile(
        project_id=project.id,
        filename="cascade.txt",
        original_filename="cascade-test.txt",
        file_path="uploads/cascade.txt",
        file_size=512,
        mime_type="text/plain",
        uploaded_by=user.id,
    )
    db_session.add(file)
    await db_session.commit()
    file_id = file.id

    # Act - プロジェクトを削除
    await db_session.delete(project)
    await db_session.commit()

    # Assert - ファイルも削除されているはず（CASCADE）
    result = await db_session.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    deleted_file = result.scalar_one_or_none()
    assert deleted_file is None


@pytest.mark.asyncio
async def test_project_file_restrict_delete_user(db_session):
    """ユーザー削除時にRESTRICT制約が機能することを確認。

    アップロード者がいるファイルが存在する場合、そのユーザーの削除を禁止します。
    これにより、ファイルの履歴情報の整合性を保証します。
    """
    # Arrange
    user = UserAccount(
        azure_oid="restrict-file-oid",
        email="filerestrict@company.com",
        display_name="File Restrict User",
    )
    project = Project(
        name="File Restrict Project",
        code="FILERESTRICT-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # ファイルを追加
    file = ProjectFile(
        project_id=project.id,
        filename="restrict.txt",
        original_filename="restrict-test.txt",
        file_path="uploads/restrict.txt",
        file_size=256,
        mime_type="text/plain",
        uploaded_by=user.id,
    )
    db_session.add(file)
    await db_session.commit()

    # Act & Assert - ユーザーを削除しようとするとエラー（RESTRICT）
    with pytest.raises(IntegrityError):
        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_file_required_fields(db_session):
    """必須フィールド（NOT NULL制約）が機能することを確認。

    主要な属性（filename）が欠けている場合、データベースの制約により
    エラーが発生し、不完全なレコード作成を防止します。
    """
    # Arrange
    user = UserAccount(
        azure_oid="required-file-oid",
        email="filerequired@company.com",
        display_name="File Required User",
    )
    project = Project(
        name="File Required Project",
        code="FILEREQUIRED-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # Act & Assert - 必須フィールドが欠けている場合エラー
    # SQLAlchemyではNone許容のため、IntegrityError（DB制約違反）が発生
    with pytest.raises(IntegrityError):  # NOT NULL constraint
        file = ProjectFile(
            project_id=project.id,
            # filename は必須だが欠けている（Noneで設定される）
            original_filename="test.txt",
            file_path="uploads/test.txt",
            file_size=100,
            uploaded_by=user.id,
        )
        db_session.add(file)
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_file_uploaded_at_auto_set(db_session):
    """uploaded_atが自動的に設定されることを確認。

    ファイル作成時にuploaded_atを明示的に指定しなくても、
    モデルのデフォルト値により自動的に現在時刻が設定されます。
    """
    # Arrange
    user = UserAccount(
        azure_oid="autoset-file-oid",
        email="fileautoset@company.com",
        display_name="File Auto Set User",
    )
    project = Project(
        name="File Auto Set Project",
        code="FILEAUTOSET-001",
    )
    db_session.add(user)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(project)

    # Act - uploaded_atを指定せずにファイルを作成
    file = ProjectFile(
        project_id=project.id,
        filename="auto.txt",
        original_filename="auto-set.txt",
        file_path="uploads/auto.txt",
        file_size=128,
        uploaded_by=user.id,
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)

    # Assert - uploaded_atが自動的に設定されている
    assert file.uploaded_at is not None
    assert isinstance(file.uploaded_at, datetime)
    assert file.uploaded_at <= datetime.now(UTC)
