"""ダミーチャートマスタ管理サービスのテスト。"""

import json
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.analysis.analysis_dummy_chart_master import AnalysisDummyChartMaster
from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
from app.models.analysis.analysis_validation_master import AnalysisValidationMaster
from app.schemas.analysis.analysis_template import (
    AnalysisDummyChartCreate,
    AnalysisDummyChartUpdate,
)
from app.services.admin.dummy_chart import AdminDummyChartService


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


@pytest.fixture
async def test_issue(db_session: AsyncSession, test_validation):
    """テスト用課題マスタを作成。"""
    issue = AnalysisIssueMaster(
        validation_id=test_validation.id,
        name="テスト課題",
        issue_order=1,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)
    return issue


@pytest.mark.asyncio
async def test_list_charts_success(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-001] ダミーチャート一覧取得の成功ケース。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    chart_data = {"data": [], "layout": {}}
    chart = AnalysisDummyChartMaster(
        issue_id=test_issue.id,
        chart=json.dumps(chart_data).encode("utf-8"),
        chart_order=1,
    )
    db_session.add(chart)
    await db_session.commit()

    # Act
    result = await service.list_charts(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total >= 1
    assert len(result.charts) >= 1
    assert result.skip == 0
    assert result.limit == 100


@pytest.mark.asyncio
async def test_list_charts_with_issue_filter(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-002] issue_idでフィルタしたダミーチャート一覧取得。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    chart_data = {"data": [], "layout": {}}
    chart = AnalysisDummyChartMaster(
        issue_id=test_issue.id,
        chart=json.dumps(chart_data).encode("utf-8"),
        chart_order=1,
    )
    db_session.add(chart)
    await db_session.commit()

    # Act
    result = await service.list_charts(skip=0, limit=100, issue_id=test_issue.id)

    # Assert
    assert result is not None
    assert result.total >= 1
    for chart_response in result.charts:
        assert chart_response.issue_id == test_issue.id


@pytest.mark.asyncio
async def test_list_charts_with_pagination(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-003] ダミーチャート一覧取得のページネーション。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    for i in range(5):
        chart_data = {"data": [], "layout": {"title": f"Chart {i}"}}
        chart = AnalysisDummyChartMaster(
            issue_id=test_issue.id,
            chart=json.dumps(chart_data).encode("utf-8"),
            chart_order=i + 1,
        )
        db_session.add(chart)
    await db_session.commit()

    # Act
    result = await service.list_charts(skip=2, limit=2)

    # Assert
    assert result is not None
    assert result.skip == 2
    assert result.limit == 2
    assert len(result.charts) <= 2


@pytest.mark.asyncio
async def test_get_chart_success(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-004] ダミーチャート詳細取得の成功ケース。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    chart_data = {"data": [{"x": [1, 2, 3], "y": [4, 5, 6]}], "layout": {"title": "Test"}}
    chart = AnalysisDummyChartMaster(
        issue_id=test_issue.id,
        chart=json.dumps(chart_data).encode("utf-8"),
        chart_order=1,
    )
    db_session.add(chart)
    await db_session.commit()
    await db_session.refresh(chart)

    # Act
    result = await service.get_chart(chart.id)

    # Assert
    assert result is not None
    assert result.id == chart.id
    assert result.issue_id == test_issue.id
    assert result.chart_order == 1


@pytest.mark.asyncio
async def test_get_chart_not_found(db_session: AsyncSession):
    """[test_dummy_chart_service-005] 存在しないダミーチャート取得時のNotFoundError。"""
    # Arrange
    service = AdminDummyChartService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_chart(non_existent_id)

    assert "ダミーチャートマスタが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_chart_success(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-006] ダミーチャート作成の成功ケース。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    chart_data = {"data": [{"x": [1, 2, 3], "y": [4, 5, 6]}], "layout": {"title": "New Chart"}}
    chart_create = AnalysisDummyChartCreate(
        issue_id=test_issue.id,
        chart=chart_data,
        chart_order=1,
    )

    # Act
    result = await service.create_chart(chart_create)

    # Assert
    assert result is not None
    assert result.issue_id == test_issue.id
    assert result.chart_order == 1


@pytest.mark.asyncio
async def test_update_chart_success(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-007] ダミーチャート更新の成功ケース。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    chart_data = {"data": [], "layout": {"title": "Original"}}
    chart = AnalysisDummyChartMaster(
        issue_id=test_issue.id,
        chart=json.dumps(chart_data).encode("utf-8"),
        chart_order=1,
    )
    db_session.add(chart)
    await db_session.commit()
    await db_session.refresh(chart)

    updated_chart_data = {"data": [{"x": [1], "y": [2]}], "layout": {"title": "Updated"}}
    chart_update = AnalysisDummyChartUpdate(
        chart=updated_chart_data,
        chart_order=2,
    )

    # Act
    result = await service.update_chart(chart.id, chart_update)

    # Assert
    assert result is not None
    assert result.chart_order == 2


@pytest.mark.asyncio
async def test_update_chart_not_found(db_session: AsyncSession):
    """[test_dummy_chart_service-008] 存在しないダミーチャート更新時のNotFoundError。"""
    # Arrange
    service = AdminDummyChartService(db_session)
    non_existent_id = uuid.uuid4()
    chart_update = AnalysisDummyChartUpdate(chart_order=2)

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.update_chart(non_existent_id, chart_update)

    assert "ダミーチャートマスタが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_chart_success(db_session: AsyncSession, test_issue):
    """[test_dummy_chart_service-009] ダミーチャート削除の成功ケース。"""
    # Arrange
    service = AdminDummyChartService(db_session)

    chart_data = {"data": [], "layout": {}}
    chart = AnalysisDummyChartMaster(
        issue_id=test_issue.id,
        chart=json.dumps(chart_data).encode("utf-8"),
        chart_order=1,
    )
    db_session.add(chart)
    await db_session.commit()
    await db_session.refresh(chart)
    chart_id = chart.id

    # Act
    await service.delete_chart(chart_id)

    # Assert - 削除後に取得するとNotFoundError
    with pytest.raises(NotFoundError):
        await service.get_chart(chart_id)


@pytest.mark.asyncio
async def test_delete_chart_not_found(db_session: AsyncSession):
    """[test_dummy_chart_service-010] 存在しないダミーチャート削除時のNotFoundError。"""
    # Arrange
    service = AdminDummyChartService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.delete_chart(non_existent_id)

    assert "ダミーチャートマスタが見つかりません" in str(exc_info.value)
