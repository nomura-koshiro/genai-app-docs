"""操作履歴サービスのテスト。"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserAccount
from app.models.audit.user_activity import UserActivity
from app.schemas.admin.activity_log import ActivityLogFilter
from app.services.admin.activity_tracking_service import ActivityTrackingService


@pytest.mark.asyncio
async def test_record_activity_success(db_session: AsyncSession):
    """[test_activity_tracking_service-001] 操作履歴記録の成功ケース。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    await service.record_activity(
        user_id=user_id,
        action_type="CREATE",
        resource_type="Project",
        resource_id=uuid.uuid4(),
        endpoint="/api/v1/project",
        method="POST",
        request_body={"name": "Test Project"},
        response_status=201,
        error_message=None,
        error_code=None,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        duration_ms=100,
    )

    # Assert
    result = await db_session.execute(
        db_session.query(UserActivity).where(UserActivity.user_id == user_id)
    )
    activity = result.scalar_one_or_none()
    assert activity is not None
    assert activity.action_type == "CREATE"
    assert activity.resource_type == "Project"
    assert activity.response_status == 201


@pytest.mark.asyncio
async def test_list_activities_success(db_session: AsyncSession):
    """[test_activity_tracking_service-002] 操作履歴一覧取得の成功ケース。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # 複数の操作履歴を作成
    for i in range(3):
        activity = UserActivity(
            user_id=user_id,
            action_type="READ",
            endpoint=f"/api/v1/test/{i}",
            method="GET",
            response_status=200,
            duration_ms=50,
        )
        db_session.add(activity)
    await db_session.commit()

    # Act
    filter_params = ActivityLogFilter(page=1, limit=10)
    result = await service.list_activities(filter_params)

    # Assert
    assert result.total >= 3
    assert len(result.items) >= 3


@pytest.mark.asyncio
async def test_list_activities_with_filter(db_session: AsyncSession):
    """[test_activity_tracking_service-003] フィルタ付き操作履歴一覧取得。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # 成功とエラーの操作履歴を作成
    success_activity = UserActivity(
        user_id=user_id,
        action_type="READ",
        endpoint="/api/v1/test",
        method="GET",
        response_status=200,
        duration_ms=50,
    )
    error_activity = UserActivity(
        user_id=user_id,
        action_type="READ",
        endpoint="/api/v1/test",
        method="GET",
        response_status=500,
        error_message="Internal Error",
        duration_ms=50,
    )
    db_session.add(success_activity)
    db_session.add(error_activity)
    await db_session.commit()

    # Act
    filter_params = ActivityLogFilter(user_id=user_id, has_error=True, page=1, limit=10)
    result = await service.list_activities(filter_params)

    # Assert
    assert result.total >= 1
    assert all(item.error_message is not None for item in result.items if item.user_id == user_id)


@pytest.mark.asyncio
async def test_get_activity_detail_success(db_session: AsyncSession):
    """[test_activity_tracking_service-004] 操作履歴詳細取得の成功ケース。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 操作履歴を作成
    activity = UserActivity(
        user_id=user_id,
        action_type="UPDATE",
        endpoint="/api/v1/test",
        method="PUT",
        request_body={"key": "value"},
        response_status=200,
        duration_ms=100,
    )
    db_session.add(activity)
    await db_session.commit()

    # Act
    result = await service.get_activity_detail(activity.id)

    # Assert
    assert result is not None
    assert result.id == activity.id
    assert result.action_type == "UPDATE"
    assert result.request_body == {"key": "value"}


@pytest.mark.asyncio
async def test_get_activity_detail_not_found(db_session: AsyncSession):
    """[test_activity_tracking_service-005] 存在しない操作履歴の取得。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    nonexistent_id = uuid.uuid4()

    # Act
    result = await service.get_activity_detail(nonexistent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_export_to_csv_success(db_session: AsyncSession):
    """[test_activity_tracking_service-006] CSV エクスポートの成功ケース。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 操作履歴を作成
    activity = UserActivity(
        user_id=user_id,
        action_type="CREATE",
        endpoint="/api/v1/test",
        method="POST",
        response_status=201,
        duration_ms=100,
    )
    db_session.add(activity)
    await db_session.commit()

    # Act
    filter_params = ActivityLogFilter(user_id=user_id, page=1, limit=10)
    csv_data = await service.export_to_csv(filter_params)

    # Assert
    assert csv_data is not None
    assert "ID" in csv_data  # ヘッダーを確認
    assert "日時" in csv_data
    assert str(user_id) in csv_data


@pytest.mark.asyncio
async def test_get_statistics_success(db_session: AsyncSession):
    """[test_activity_tracking_service-007] 統計情報取得の成功ケース。"""
    # Arrange
    service = ActivityTrackingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 操作履歴を作成
    for i in range(5):
        activity = UserActivity(
            user_id=user_id,
            action_type="READ",
            endpoint="/api/v1/test",
            method="GET",
            response_status=200,
            duration_ms=50 + i,
        )
        db_session.add(activity)
    await db_session.commit()

    # Act
    stats = await service.get_statistics()

    # Assert
    assert stats is not None
    assert isinstance(stats, dict)
