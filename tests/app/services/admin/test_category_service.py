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
async def test_list_categories_success(db_session: AsyncSession):
    """[test_category_service-001] カテゴリ一覧取得の成功ケース。"""
    # Arrange
    service = AdminCategoryService(db_session)

    # カテゴリを作成
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

    # Act
    result = await service.list_categories(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total >= 1
    assert len(result.categories) >= 1
    assert result.skip == 0
    assert result.limit == 100


@pytest.mark.asyncio
async def test_list_categories_with_pagination(db_session: AsyncSession):
    """[test_category_service-002] カテゴリ一覧取得のページネーション。"""
    # Arrange
    service = AdminCategoryService(db_session)

    # 複数のカテゴリを作成
    for i in range(5):
        category = DriverTreeCategory(
            category_id=i + 1,
            category_name=f"カテゴリ{i}",
            industry_id=i + 1,
            industry_name=f"業界{i}",
            driver_type_id=i + 1,
            driver_type=f"ドライバー型{i}",
        )
        db_session.add(category)
    await db_session.commit()

    # Act
    result = await service.list_categories(skip=2, limit=2)

    # Assert
    assert result is not None
    assert result.skip == 2
    assert result.limit == 2
    assert len(result.categories) <= 2


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
async def test_get_category_not_found(db_session: AsyncSession):
    """[test_category_service-004] 存在しないカテゴリ取得時のNotFoundError。"""
    # Arrange
    service = AdminCategoryService(db_session)
    non_existent_id = 99999

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_category(non_existent_id)

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
async def test_update_category_not_found(db_session: AsyncSession):
    """[test_category_service-007] 存在しないカテゴリ更新時のNotFoundError。"""
    # Arrange
    service = AdminCategoryService(db_session)
    non_existent_id = 99999
    category_update = DriverTreeCategoryUpdate(category_name="更新")

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.update_category(non_existent_id, category_update)

    assert "カテゴリマスタが見つかりません" in str(exc_info.value)


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
async def test_delete_category_not_found(db_session: AsyncSession):
    """[test_category_service-009] 存在しないカテゴリ削除時のNotFoundError。"""
    # Arrange
    service = AdminCategoryService(db_session)
    non_existent_id = 99999

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await service.delete_category(non_existent_id)

    assert "カテゴリマスタが見つかりません" in str(exc_info.value)


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
