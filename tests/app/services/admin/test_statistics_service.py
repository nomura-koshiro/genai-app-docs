"""統計情報サービスのテスト。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, UserAccount
from app.models.audit.user_activity import UserActivity
from app.services.admin.statistics_service import StatisticsService


@pytest.mark.asyncio
async def test_get_overview_success(db_session: AsyncSession):
    """[test_statistics_service-001] 統計概要取得の成功ケース。"""
    # Arrange
    service = StatisticsService(db_session)

    # ユーザーを作成
    user = UserAccount(
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    result = await service.get_overview()

    # Assert
    assert result is not None
    assert result.users is not None
    assert result.projects is not None
    assert result.storage is not None
    assert result.api is not None


@pytest.mark.asyncio
async def test_get_user_summary(db_session: AsyncSession):
    """[test_statistics_service-002] ユーザー統計サマリー取得。"""
    # Arrange
    service = StatisticsService(db_session)

    # 複数のユーザーを作成
    for i in range(3):
        user = UserAccount(
            azure_oid=f"azure-oid-{uuid.uuid4()}",
            email=f"test-{i}-{uuid.uuid4()}@example.com",
            display_name=f"Test User {i}",
        )
        db_session.add(user)
    await db_session.commit()

    # Act
    result = await service._get_user_summary()

    # Assert
    assert result is not None
    assert result.total >= 3


@pytest.mark.asyncio
async def test_get_project_summary(db_session: AsyncSession):
    """[test_statistics_service-003] プロジェクト統計サマリー取得。"""
    # Arrange
    service = StatisticsService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # プロジェクトを作成
    for i in range(2):
        project = Project(
            name=f"Test Project {i}",
            code=f"TEST-{uuid.uuid4().hex[:6]}",
            created_by=creator_id,
            is_active=True,
        )
        db_session.add(project)
    await db_session.commit()

    # Act
    result = await service._get_project_summary()

    # Assert
    assert result is not None
    assert result.total >= 2
    assert result.active >= 2


@pytest.mark.asyncio
async def test_get_api_summary(db_session: AsyncSession):
    """[test_statistics_service-004] API統計サマリー取得。"""
    # Arrange
    service = StatisticsService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # ユーザーアクティビティを作成
    for i in range(5):
        activity = UserActivity(
            user_id=user_id,
            action_type="READ",
            endpoint="/api/v1/test",
            method="GET",
            response_status=200,
            duration_ms=100 + i,
        )
        db_session.add(activity)
    await db_session.commit()

    # Act
    result = await service._get_api_summary()

    # Assert
    assert result is not None
    assert result.requests_today >= 5
    assert result.average_response_ms > 0


@pytest.mark.asyncio
async def test_get_user_statistics_success(db_session: AsyncSession):
    """[test_statistics_service-005] ユーザー統計詳細取得の成功ケース。"""
    # Arrange
    service = StatisticsService(db_session)

    # ユーザーを作成
    for i in range(3):
        user = UserAccount(
            azure_oid=f"azure-oid-{uuid.uuid4()}",
            email=f"test-{i}-{uuid.uuid4()}@example.com",
            display_name=f"Test User {i}",
        )
        db_session.add(user)
    await db_session.commit()

    # Act
    result = await service.get_user_statistics(days=7)

    # Assert
    assert result is not None
    assert result.total >= 3
    assert isinstance(result.active_users, list)
    assert isinstance(result.new_users, list)


@pytest.mark.asyncio
async def test_format_bytes(db_session: AsyncSession):
    """[test_statistics_service-006] バイト数フォーマット。"""
    # Arrange
    service = StatisticsService(db_session)

    # Act & Assert
    assert service._format_bytes(500) == "500.0 B"
    assert service._format_bytes(1024) == "1.0 KB"
    assert service._format_bytes(1024 * 1024) == "1.0 MB"
    assert service._format_bytes(1024 * 1024 * 1024) == "1.0 GB"
