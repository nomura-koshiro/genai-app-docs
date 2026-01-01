"""課題マスタ管理サービスのテスト。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
from app.models.analysis.analysis_validation_master import AnalysisValidationMaster
from app.schemas.admin.issue import (
    AnalysisIssueCreate,
    AnalysisIssueUpdate,
)
from app.services.admin.issue import AdminIssueService


@pytest.fixture
async def test_validation(db_session: AsyncSession):
    """テスト用検証マスタを作成。"""
    validation = AnalysisValidationMaster(
        name="テスト検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)
    return validation


@pytest.mark.asyncio
async def test_list_issues_success(db_session: AsyncSession, test_validation):
    """[test_issue_service-001] 課題一覧取得の成功ケース。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="テスト課題",
        description="テスト説明",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()

    # Act
    result = await service.list_issues(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total >= 1
    assert len(result.issues) >= 1
    assert result.skip == 0
    assert result.limit == 100


@pytest.mark.asyncio
async def test_list_issues_with_validation_filter(db_session: AsyncSession, test_validation):
    """[test_issue_service-002] validation_idでフィルタした課題一覧取得。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="テスト課題",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()

    # Act
    result = await service.list_issues(skip=0, limit=100, validation_id=test_validation.id)

    # Assert
    assert result is not None
    assert result.total >= 1
    for issue_response in result.issues:
        assert issue_response.validation_id == test_validation.id


@pytest.mark.asyncio
async def test_list_issues_with_pagination(db_session: AsyncSession, test_validation):
    """[test_issue_service-003] 課題一覧取得のページネーション。"""
    # Arrange
    service = AdminIssueService(db_session)

    for i in range(5):
        issue = AnalysisIssueMaster(
            validation_id=test_validation.id,
            name=f"課題{i}",
            issue_order=i + 1,
        )
        db_session.add(issue)
    await db_session.commit()

    # Act
    result = await service.list_issues(skip=2, limit=2)

    # Assert
    assert result is not None
    assert result.skip == 2
    assert result.limit == 2
    assert len(result.issues) <= 2


@pytest.mark.asyncio
async def test_get_issue_success(db_session: AsyncSession, test_validation):
    """[test_issue_service-004] 課題詳細取得の成功ケース。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="テスト課題",
        description="テスト説明",
        agent_prompt="テストプロンプト",
        initial_msg="初期メッセージ",
        dummy_hint="ダミーヒント",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    # Act
    result = await service.get_issue(issue.id)

    # Assert
    assert result is not None
    assert result.id == issue.id
    assert result.name == "テスト課題"
    assert result.description == "テスト説明"
    assert result.agent_prompt == "テストプロンプト"
    assert result.validation_id == test_validation.id


@pytest.mark.asyncio
async def test_get_issue_not_found(db_session: AsyncSession):
    """[test_issue_service-005] 存在しない課題取得時のNotFoundError。"""
    # Arrange
    service = AdminIssueService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_issue(non_existent_id)

    assert "課題マスタが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_issue_success(db_session: AsyncSession, test_validation):
    """[test_issue_service-006] 課題作成の成功ケース。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue_create = AnalysisIssueCreate(
        validation_id=test_validation.id,
        name="新規課題",
        description="新規説明",
        agent_prompt="新規プロンプト",
        initial_msg="新規初期メッセージ",
        dummy_hint="新規ダミーヒント",
        issue_order=1,
    )

    # Act
    result = await service.create_issue(issue_create)

    # Assert
    assert result is not None
    assert result.name == "新規課題"
    assert result.description == "新規説明"
    assert result.validation_id == test_validation.id


@pytest.mark.asyncio
async def test_create_issue_with_minimal_data(db_session: AsyncSession, test_validation):
    """[test_issue_service-007] 最小データでの課題作成。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue_create = AnalysisIssueCreate(
        validation_id=test_validation.id,
        name="最小課題",
        issue_order=1,
    )

    # Act
    result = await service.create_issue(issue_create)

    # Assert
    assert result is not None
    assert result.name == "最小課題"
    assert result.description is None
    assert result.agent_prompt is None


@pytest.mark.asyncio
async def test_update_issue_success(db_session: AsyncSession, test_validation):
    """[test_issue_service-008] 課題更新の成功ケース。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="元の課題",
        description="元の説明",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    issue_update = AnalysisIssueUpdate(
        name="更新後の課題",
        description="更新後の説明",
        agent_prompt="更新後のプロンプト",
        issue_order=2,
    )

    # Act
    result = await service.update_issue(issue.id, issue_update)

    # Assert
    assert result is not None
    assert result.name == "更新後の課題"
    assert result.description == "更新後の説明"
    assert result.agent_prompt == "更新後のプロンプト"
    assert result.issue_order == 2


@pytest.mark.asyncio
async def test_update_issue_partial(db_session: AsyncSession, test_validation):
    """[test_issue_service-009] 課題の部分更新。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="元の課題",
        description="元の説明",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    # 名前のみ更新
    issue_update = AnalysisIssueUpdate(name="名前だけ更新")

    # Act
    result = await service.update_issue(issue.id, issue_update)

    # Assert
    assert result is not None
    assert result.name == "名前だけ更新"


@pytest.mark.asyncio
async def test_update_issue_not_found(db_session: AsyncSession):
    """[test_issue_service-010] 存在しない課題更新時のNotFoundError。"""
    # Arrange
    service = AdminIssueService(db_session)
    non_existent_id = uuid.uuid4()
    issue_update = AnalysisIssueUpdate(name="更新")

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.update_issue(non_existent_id, issue_update)

    assert "課題マスタが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_issue_success(db_session: AsyncSession, test_validation):
    """[test_issue_service-011] 課題削除の成功ケース。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="削除対象課題",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)
    issue_id = issue.id

    # Act
    await service.delete_issue(issue_id)

    # Assert - 削除後に取得するとNotFoundError
    with pytest.raises(NotFoundError):
        await service.get_issue(issue_id)


@pytest.mark.asyncio
async def test_delete_issue_not_found(db_session: AsyncSession):
    """[test_issue_service-012] 存在しない課題削除時のNotFoundError。"""
    # Arrange
    service = AdminIssueService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.delete_issue(non_existent_id)

    assert "課題マスタが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_issue_with_sessions_conflict(db_session: AsyncSession, test_validation):
    """[test_issue_service-013] セッションが紐づいている課題削除時のConflictError。"""
    # Arrange
    service = AdminIssueService(db_session)

    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="セッション付き課題",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    # has_sessionsがTrueを返すようにモック
    with patch.object(
        service.repository,
        "has_sessions",
        new_callable=AsyncMock,
        return_value=True,
    ):
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await service.delete_issue(issue.id)

        assert "セッションが紐づいている" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_issues_empty(db_session: AsyncSession):
    """[test_issue_service-014] 課題が存在しない場合の一覧取得。"""
    # Arrange
    service = AdminIssueService(db_session)

    # Act
    result = await service.list_issues(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total == 0
    assert len(result.issues) == 0


@pytest.mark.asyncio
async def test_create_multiple_issues_for_validation(db_session: AsyncSession, test_validation):
    """[test_issue_service-015] 同一検証に複数課題を作成。"""
    # Arrange
    service = AdminIssueService(db_session)

    issues_data = [
        {"name": "課題1", "description": "説明1", "issue_order": 1},
        {"name": "課題2", "description": "説明2", "issue_order": 2},
        {"name": "課題3", "description": "説明3", "issue_order": 3},
    ]

    # Act
    created_issues = []
    for issue_data in issues_data:
        issue_create = AnalysisIssueCreate(
            validation_id=test_validation.id,
            **issue_data,
        )
        result = await service.create_issue(issue_create)
        created_issues.append(result)

    # Assert
    assert len(created_issues) == 3

    list_result = await service.list_issues(validation_id=test_validation.id)
    assert list_result.total == 3
