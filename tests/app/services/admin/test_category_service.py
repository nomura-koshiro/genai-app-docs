"""カテゴリマスタ管理サービスのテスト。"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.driver_tree.driver_tree_category import DriverTreeCategory
from app.schemas.admin.category import (
    DriverTreeCategoryCreate,
    DriverTreeCategoryUpdate,
)
from app.services.admin.category import AdminCategoryService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "num_categories,skip,limit,expected_min_total,expected_skip,expected_limit,expected_max_results",
    [
        # test_list_categories_success: 1 category, no pagination
        (1, 0, 100, 1, 0, 100, 100),
        # test_list_categories_with_pagination: 5 categories, skip=2, limit=2
        (5, 2, 2, 5, 2, 2, 2),
    ],
    ids=["success", "with_pagination"],
)
async def test_list_categories(
    db_session: AsyncSession,
    num_categories: int,
    skip: int,
    limit: int,
    expected_min_total: int,
    expected_skip: int,
    expected_limit: int,
    expected_max_results: int,
):
    """[test_category_service-001,002] カテゴリ一覧取得の成功ケースとページネーション。"""
    # Arrange
    service = AdminCategoryService(db_session)

    # カテゴリを作成
    for i in range(num_categories):
        category = DriverTreeCategory(
            category_id=i + 1,
            category_name=f"カテゴリ{i}" if num_categories > 1 else "製造業",
            industry_id=i + 1,
            industry_name=f"業界{i}" if num_categories > 1 else "自動車",
            driver_type_id=i + 1,
            driver_type=f"ドライバー型{i}" if num_categories > 1 else "収益ドライバー",
        )
        db_session.add(category)
    await db_session.commit()

    # Act
    result = await service.list_categories(skip=skip, limit=limit)

    # Assert
    assert result is not None
    assert result.total >= expected_min_total
    assert result.skip == expected_skip
    assert result.limit == expected_limit
    assert len(result.categories) <= expected_max_results


@pytest.mark.asyncio
async def test_get_category_success(db_session: AsyncSession):
    """[test_category_service-003] カテゴリ詳細取得の成功ケース。"""
    # Arrange
    service = AdminCategoryService(db_session)

    category = DriverTreeCategory(
        category_id=1,
        category_name="製造業",
        industry_id=1,
        industry_name="自動車",
        driver_type_id=1,
        driver_type="収益ドライバー",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    # Act
    result = await service.get_category(category.id)

    # Assert
    assert result is not None
    assert result.id == category.id
    assert result.category_name == "製造業"
    assert result.industry_name == "自動車"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    ["get", "update", "delete"],
    ids=["get", "update", "delete"],
)
async def test_category_not_found(db_session: AsyncSession, operation: str):
    """[test_category_service-004,007,009] 存在しないカテゴリ操作時のNotFoundError。"""
    # Arrange
    service = AdminCategoryService(db_session)
    non_existent_id = 99999

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        if operation == "get":
            await service.get_category(non_existent_id)
        elif operation == "update":
            category_update = DriverTreeCategoryUpdate(category_name="更新")
            await service.update_category(non_existent_id, category_update)
        else:  # delete
            await service.delete_category(non_existent_id)

    assert "カテゴリマスタが見つかりません" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_category_success(db_session: AsyncSession):
    """[test_category_service-005] カテゴリ作成の成功ケース。"""
    # Arrange
    service = AdminCategoryService(db_session)
    category_create = DriverTreeCategoryCreate(
        category_id=1,
        category_name="製造業",
        industry_id=1,
        industry_name="自動車",
        driver_type_id=1,
        driver_type="収益ドライバー",
    )

    # Act
    result = await service.create_category(category_create)

    # Assert
    assert result is not None
    assert result.category_name == "製造業"
    assert result.industry_name == "自動車"
    assert result.driver_type == "収益ドライバー"


@pytest.mark.asyncio
async def test_update_category_success(db_session: AsyncSession):
    """[test_category_service-006] カテゴリ更新の成功ケース。"""
    # Arrange
    service = AdminCategoryService(db_session)

    category = DriverTreeCategory(
        category_id=1,
        category_name="製造業",
        industry_id=1,
        industry_name="自動車",
        driver_type_id=1,
        driver_type="収益ドライバー",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    category_update = DriverTreeCategoryUpdate(
        category_name="更新後カテゴリ",
        industry_name="更新後業界",
    )

    # Act
    result = await service.update_category(category.id, category_update)

    # Assert
    assert result is not None
    assert result.category_name == "更新後カテゴリ"
    assert result.industry_name == "更新後業界"


@pytest.mark.asyncio
async def test_delete_category_success(db_session: AsyncSession):
    """[test_category_service-008] カテゴリ削除の成功ケース。"""
    # Arrange
    service = AdminCategoryService(db_session)

    category = DriverTreeCategory(
        category_id=1,
        category_name="製造業",
        industry_id=1,
        industry_name="自動車",
        driver_type_id=1,
        driver_type="収益ドライバー",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    category_id = category.id

    # Act
    await service.delete_category(category_id)

    # Assert - 削除後に取得するとNotFoundError
    with pytest.raises(NotFoundError):
        await service.get_category(category_id)


@pytest.mark.asyncio
async def test_delete_category_with_formulas_conflict(db_session: AsyncSession):
    """[test_category_service-010] 数式が紐づいているカテゴリ削除時のConflictError。"""
    # Arrange
    service = AdminCategoryService(db_session)

    category = DriverTreeCategory(
        category_id=1,
        category_name="製造業",
        industry_id=1,
        industry_name="自動車",
        driver_type_id=1,
        driver_type="収益ドライバー",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    # has_formulasがTrueを返すようにモック
    with patch.object(
        service.repository,
        "has_formulas",
        new_callable=AsyncMock,
        return_value=True,
    ):
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await service.delete_category(category.id)

        assert "数式が紐づいている" in str(exc_info.value)
