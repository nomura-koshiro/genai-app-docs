"""分析サービスのテスト。

ビジネスロジックと検証のテストに焦点を当てます。
"""

import base64
import uuid

import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.analysis.session import (
    AnalysisFileUploadRequest,
    AnalysisSessionCreate,
)
from app.services.analysis import AnalysisService


@pytest.mark.asyncio
async def test_create_session_success(db_session: AsyncSession, test_user, test_project):
    """セッション作成の成功ケース。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id

    project_id = test_project.id
    session_data = AnalysisSessionCreate(
        project_id=project_id,
        policy="市場拡大",
        issue="新規参入",
        session_name="テストセッション",
    )

    # Act
    session = await service.create_session(session_data, user_id)
    await db_session.commit()

    # Assert
    assert session.id is not None
    assert session.created_by == user_id
    assert session.validation_config is not None
    assert session.chat_history == []
    # スナップショット履歴は初期スナップショット（空のステップリスト）が1つ存在する
    assert session.snapshot_history is not None
    assert len(session.snapshot_history) == 1
    # 初期スナップショットは空のステップリスト
    assert isinstance(session.snapshot_history[0], list)
    assert session.snapshot_history[0] == []


@pytest.mark.asyncio
async def test_get_session_with_relations_success(db_session: AsyncSession, test_user, test_project):
    """リレーション付きセッション取得の成功ケース。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id

    # セッションを作成
    project_id = test_project.id
    session_data = AnalysisSessionCreate(
        project_id=project_id,
        policy="テスト施策",
        issue="テスト課題",
        session_name=None,
    )
    created_session = await service.create_session(session_data, user_id)
    await db_session.commit()

    # Act
    result = await service.get_session(created_session.id)

    # Assert
    assert result is not None
    assert result.id == created_session.id


@pytest.mark.asyncio
async def test_get_session_not_found(db_session: AsyncSession, test_user, test_project):
    """存在しないセッションの取得エラー。"""
    # Arrange
    service = AnalysisService(db_session)
    nonexistent_id = uuid.uuid4()

    # Act
    result = await service.get_session(nonexistent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_list_user_sessions(db_session: AsyncSession, test_user, test_project):
    """ユーザーのセッション一覧取得。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id

    # 2つのセッションを作成
    project_id = test_project.id
    session_data1 = AnalysisSessionCreate(
        project_id=project_id,
        policy="テスト施策1",
        issue="テスト課題1",
        session_name=None,
    )
    session_data2 = AnalysisSessionCreate(
        project_id=project_id,
        policy="テスト施策2",
        issue="テスト課題2",
        session_name=None,
    )

    await service.create_session(session_data1, user_id)
    await service.create_session(session_data2, user_id)
    await db_session.commit()

    # Act
    result = await service.list_project_sessions(project_id)

    # Assert
    assert len(result) == 2


@pytest.mark.asyncio
async def test_upload_data_file_success(db_session: AsyncSession, test_user, test_project):
    """データファイルアップロードの成功ケース。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id

    # セッションを作成
    project_id = test_project.id
    session_data = AnalysisSessionCreate(
        project_id=project_id,
        policy="テスト施策",
        issue="テスト課題",
        session_name=None,
    )
    session = await service.create_session(session_data, user_id)
    await db_session.commit()

    # CSVデータを作成
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
        }
    )
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode()).decode()

    file_request = AnalysisFileUploadRequest(
        session_id=session.id,
        file_name="test.csv",
        table_name="test_data",
        table_axis=["name"],
        data=encoded_content,
    )

    # Act
    result = await service.upload_data_file(session.id, file_request, user_id)
    await db_session.commit()

    # Assert
    assert result.id is not None
    assert result.file_name == "test.csv"
    assert result.table_name == "test_data"
    assert result.message == "ファイルが正常にアップロードされました"


@pytest.mark.asyncio
async def test_upload_data_file_invalid_csv(db_session: AsyncSession, test_user, test_project):
    """無効なCSVファイルのアップロードエラー。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id

    # セッションを作成
    project_id = test_project.id
    session_data = AnalysisSessionCreate(
        project_id=project_id,
        policy="テスト施策",
        issue="テスト課題",
        session_name=None,
    )
    session = await service.create_session(session_data, user_id)
    await db_session.commit()

    # 無効なCSVコンテンツ
    invalid_content = "This is not a valid CSV"
    encoded_content = base64.b64encode(invalid_content.encode()).decode()

    file_request = AnalysisFileUploadRequest(
        session_id=session.id,
        file_name="invalid.csv",
        table_name="invalid_data",
        table_axis=[],
        data=encoded_content,
    )

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.upload_data_file(session.id, file_request, user_id)

    # ValidationErrorが発生することを確認（メッセージの内容は問わない）


@pytest.mark.asyncio
async def test_upload_data_file_session_not_found(db_session: AsyncSession, test_user, test_project):
    """存在しないセッションへのファイルアップロードエラー。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id
    nonexistent_session_id = uuid.uuid4()

    # CSVデータを作成
    df = pd.DataFrame({"id": [1, 2, 3]})
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode()).decode()

    file_request = AnalysisFileUploadRequest(
        session_id=nonexistent_session_id,
        file_name="test.csv",
        table_name="test_data",
        table_axis=[],
        data=encoded_content,
    )

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.upload_data_file(nonexistent_session_id, file_request, user_id)


@pytest.mark.asyncio
async def test_list_user_sessions_with_pagination(db_session: AsyncSession, test_user, test_project):
    """ページネーション付きセッション一覧取得。"""
    # Arrange
    service = AnalysisService(db_session)
    user_id = test_user.id

    # 5つのセッションを作成
    project_id = test_project.id
    for i in range(5):
        session_data = AnalysisSessionCreate(
            project_id=project_id,
            policy=f"施策{i}",
            issue=f"課題{i}",
            session_name=None,
        )
        await service.create_session(session_data, user_id)

    await db_session.commit()

    # Act - 最初の2件を取得
    result = await service.list_project_sessions(project_id, skip=0, limit=2)

    # Assert
    assert len(result) == 2
