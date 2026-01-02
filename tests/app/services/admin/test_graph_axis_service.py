"""グラフ軸マスタ管理サービスのテスト。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.analysis.analysis_graph_axis_master import AnalysisGraphAxisMaster
from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
from app.models.analysis.analysis_validation_master import AnalysisValidationMaster
from app.schemas.analysis.analysis_template import (
    AnalysisGraphAxisCreate,
    AnalysisGraphAxisUpdate,
)
from app.services.admin.graph_axis import AdminGraphAxisService


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
async def test_list_axes_success(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-001] グラフ軸一覧取得の成功ケース。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis = AnalysisGraphAxisMaster(
        issue_id=test_issue.id,
        name="横軸",
        option="科目",
        multiple=False,
        axis_order=1,
    )
    db_session.add(axis)
    await db_session.commit()

    # Act
    result = await service.list_axes(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total >= 1
    assert len(result.axes) >= 1
    assert result.skip == 0
    assert result.limit == 100


@pytest.mark.asyncio
async def test_list_axes_with_issue_filter(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-002] issue_idでフィルタしたグラフ軸一覧取得。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis = AnalysisGraphAxisMaster(
        issue_id=test_issue.id,
        name="横軸",
        option="科目",
        multiple=False,
        axis_order=1,
    )
    db_session.add(axis)
    await db_session.commit()

    # Act
    result = await service.list_axes(skip=0, limit=100, issue_id=test_issue.id)

    # Assert
    assert result is not None
    assert result.total >= 1
    for axis_response in result.axes:
        assert axis_response.issue_id == test_issue.id


@pytest.mark.asyncio
async def test_list_axes_with_pagination(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-003] グラフ軸一覧取得のページネーション。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    for i in range(5):
        axis = AnalysisGraphAxisMaster(
            issue_id=test_issue.id,
            name=f"軸{i}",
            option="科目" if i % 2 == 0 else "軸",
            multiple=i % 2 == 1,
            axis_order=i + 1,
        )
        db_session.add(axis)
    await db_session.commit()

    # Act
    result = await service.list_axes(skip=2, limit=2)

    # Assert
    assert result is not None
    assert result.skip == 2
    assert result.limit == 2
    assert len(result.axes) <= 2


@pytest.mark.asyncio
async def test_get_axis_success(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-004] グラフ軸詳細取得の成功ケース。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis = AnalysisGraphAxisMaster(
        issue_id=test_issue.id,
        name="横軸",
        option="科目",
        multiple=False,
        axis_order=1,
    )
    db_session.add(axis)
    await db_session.commit()
    await db_session.refresh(axis)

    # Act
    result = await service.get_axis(axis.id)

    # Assert
    assert result is not None
    assert result.id == axis.id
    assert result.name == "横軸"
    assert result.option == "科目"
    assert result.multiple is False
    assert result.issue_id == test_issue.id


@pytest.mark.parametrize(
    "operation,error_msg",
    [
        ("get", "グラフ軸マスタが見つかりません"),
        ("update", "グラフ軸マスタが見つかりません"),
        ("delete", "グラフ軸マスタが見つかりません"),
    ],
    ids=["get_not_found", "update_not_found", "delete_not_found"],
)
@pytest.mark.asyncio
async def test_axis_not_found_errors(db_session: AsyncSession, operation: str, error_msg: str):
    """[test_graph_axis_service-005-009-011] グラフ軸操作でのNotFoundError。"""
    # Arrange
    service = AdminGraphAxisService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        if operation == "get":
            await service.get_axis(non_existent_id)
        elif operation == "update":
            axis_update = AnalysisGraphAxisUpdate(name="更新")
            await service.update_axis(non_existent_id, axis_update)
        elif operation == "delete":
            await service.delete_axis(non_existent_id)

    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_axis_success(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-006] グラフ軸作成の成功ケース。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis_create = AnalysisGraphAxisCreate(
        issue_id=test_issue.id,
        name="色分け",
        option="軸",
        multiple=True,
        axis_order=2,
    )

    # Act
    result = await service.create_axis(axis_create)

    # Assert
    assert result is not None
    assert result.name == "色分け"
    assert result.option == "軸"
    assert result.multiple is True
    assert result.axis_order == 2
    assert result.issue_id == test_issue.id


@pytest.mark.asyncio
async def test_update_axis_success(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-007] グラフ軸更新の成功ケース。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis = AnalysisGraphAxisMaster(
        issue_id=test_issue.id,
        name="元の軸",
        option="科目",
        multiple=False,
        axis_order=1,
    )
    db_session.add(axis)
    await db_session.commit()
    await db_session.refresh(axis)

    axis_update = AnalysisGraphAxisUpdate(
        name="更新後の軸",
        option="軸",
        multiple=True,
        axis_order=3,
    )

    # Act
    result = await service.update_axis(axis.id, axis_update)

    # Assert
    assert result is not None
    assert result.name == "更新後の軸"
    assert result.option == "軸"
    assert result.multiple is True
    assert result.axis_order == 3


@pytest.mark.asyncio
async def test_update_axis_partial(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-008] グラフ軸の部分更新。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis = AnalysisGraphAxisMaster(
        issue_id=test_issue.id,
        name="元の軸",
        option="科目",
        multiple=False,
        axis_order=1,
    )
    db_session.add(axis)
    await db_session.commit()
    await db_session.refresh(axis)

    # 名前のみ更新
    axis_update = AnalysisGraphAxisUpdate(name="名前だけ更新")

    # Act
    result = await service.update_axis(axis.id, axis_update)

    # Assert
    assert result is not None
    assert result.name == "名前だけ更新"


@pytest.mark.asyncio
async def test_delete_axis_success(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-010] グラフ軸削除の成功ケース。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axis = AnalysisGraphAxisMaster(
        issue_id=test_issue.id,
        name="削除対象軸",
        option="科目",
        multiple=False,
        axis_order=1,
    )
    db_session.add(axis)
    await db_session.commit()
    await db_session.refresh(axis)
    axis_id = axis.id

    # Act
    await service.delete_axis(axis_id)

    # Assert - 削除後に取得するとNotFoundError
    with pytest.raises(NotFoundError):
        await service.get_axis(axis_id)


@pytest.mark.asyncio
async def test_create_multiple_axes_for_issue(db_session: AsyncSession, test_issue):
    """[test_graph_axis_service-012] 同一課題に複数グラフ軸を作成。"""
    # Arrange
    service = AdminGraphAxisService(db_session)

    axes_data = [
        {"name": "横軸", "option": "科目", "multiple": False, "axis_order": 1},
        {"name": "色分け", "option": "軸", "multiple": True, "axis_order": 2},
        {"name": "サイズ", "option": "科目", "multiple": False, "axis_order": 3},
    ]

    # Act
    created_axes = []
    for axis_data in axes_data:
        axis_create = AnalysisGraphAxisCreate(
            issue_id=test_issue.id,
            **axis_data,
        )
        result = await service.create_axis(axis_create)
        created_axes.append(result)

    # Assert
    assert len(created_axes) == 3

    list_result = await service.list_axes(issue_id=test_issue.id)
    assert list_result.total == 3
