"""AnalysisTemplateServiceのテスト。"""

import uuid

import pytest

from app.core.exceptions import NotFoundError
from app.models import AnalysisIssueMaster, AnalysisValidationMaster
from app.services import AnalysisTemplateService


@pytest.mark.asyncio
async def test_list_templates_success(db_session):
    """[test_analysis_template-001] テンプレート一覧取得成功のテスト。"""
    # Arrange
    validation = AnalysisValidationMaster(
        name="テスト施策",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.flush()

    issue1 = AnalysisIssueMaster(
        validation_id=validation.id,
        name="課題1",
        issue_order=1,
    )
    issue2 = AnalysisIssueMaster(
        validation_id=validation.id,
        name="課題2",
        issue_order=2,
    )
    db_session.add(issue1)
    db_session.add(issue2)
    await db_session.commit()

    service = AnalysisTemplateService(db_session)

    # Act
    result = await service.list_templates()

    # Assert
    assert len(result) >= 2
    template_names = [t.name for t in result]
    assert "課題1" in template_names
    assert "課題2" in template_names


@pytest.mark.asyncio
async def test_list_templates_empty(db_session):
    """[test_analysis_template-002] テンプレート一覧が空の場合のテスト。"""
    # Arrange
    service = AnalysisTemplateService(db_session)

    # Act
    result = await service.list_templates()

    # Assert
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_template_success(db_session):
    """[test_analysis_template-003] テンプレート詳細取得成功のテスト。"""
    # Arrange
    validation = AnalysisValidationMaster(
        name="詳細テスト施策",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.flush()

    issue = AnalysisIssueMaster(
        validation_id=validation.id,
        name="詳細テスト課題",
        issue_order=1,
        description="テスト説明",
        agent_prompt="テストプロンプト",
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    service = AnalysisTemplateService(db_session)

    # Act
    result = await service.get_template(issue.id)

    # Assert
    assert result.id == issue.id
    assert result.name == "詳細テスト課題"
    assert result.validation == "詳細テスト施策"
    assert result.description == "テスト説明"


@pytest.mark.asyncio
async def test_get_template_not_found(db_session):
    """[test_analysis_template-004] 存在しないテンプレートの取得エラーテスト。"""
    # Arrange
    service = AnalysisTemplateService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_template(non_existent_id)


@pytest.mark.asyncio
async def test_list_templates_with_project_id(db_session):
    """[test_analysis_template-005] プロジェクトID指定でのテンプレート一覧取得テスト。"""
    # Arrange
    validation = AnalysisValidationMaster(
        name="プロジェクトテスト施策",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.flush()

    issue = AnalysisIssueMaster(
        validation_id=validation.id,
        name="プロジェクトテスト課題",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()

    service = AnalysisTemplateService(db_session)
    project_id = uuid.uuid4()

    # Act
    result = await service.list_templates(project_id=project_id)

    # Assert
    # 現状はproject_idは無視される（TODO: project別テンプレート対応）
    assert isinstance(result, list)
