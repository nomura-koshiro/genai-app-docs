"""検証マスタ管理サービスのテスト。"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.analysis.analysis_validation_master import AnalysisValidationMaster
from app.schemas.admin.validation import (
    AnalysisValidationCreate,
    AnalysisValidationUpdate,
)
from app.services.admin.validation import AdminValidationService


@pytest.mark.asyncio
async def test_list_validations_success(db_session: AsyncSession):
    """[test_validation_service-001] 検証一覧取得の成功ケース。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="テスト検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()

    # Act
    result = await service.list_validations(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total >= 1
    assert len(result.validations) >= 1
    assert result.skip == 0
    assert result.limit == 100


@pytest.mark.asyncio
async def test_list_validations_with_pagination(db_session: AsyncSession):
    """[test_validation_service-002] 検証一覧取得のページネーション。"""
    # Arrange
    service = AdminValidationService(db_session)

    for i in range(5):
        validation = AnalysisValidationMaster(
            name=f"検証{i}",
            validation_order=i + 1,
        )
        db_session.add(validation)
    await db_session.commit()

    # Act
    result = await service.list_validations(skip=2, limit=2)

    # Assert
    assert result is not None
    assert result.skip == 2
    assert result.limit == 2
    assert len(result.validations) <= 2


@pytest.mark.asyncio
async def test_list_validations_empty(db_session: AsyncSession):
    """[test_validation_service-003] 検証が存在しない場合の一覧取得。"""
    # Arrange
    service = AdminValidationService(db_session)

    # Act
    result = await service.list_validations(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total == 0
    assert len(result.validations) == 0


@pytest.mark.asyncio
async def test_get_validation_success(db_session: AsyncSession):
    """[test_validation_service-004] 検証詳細取得の成功ケース。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="テスト検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)

    # Act
    result = await service.get_validation(validation.id)

    # Assert
    assert result is not None
    assert result.id == validation.id
    assert result.name == "テスト検証"
    assert result.validation_order == 1


@pytest.mark.parametrize(
    "operation,error_msg",
    [
        ("get", "検証マスタが見つかりません"),
        ("update", "検証マスタが見つかりません"),
        ("delete", "検証マスタが見つかりません"),
    ],
    ids=["get_not_found", "update_not_found", "delete_not_found"],
)
@pytest.mark.asyncio
async def test_validation_not_found_errors(db_session: AsyncSession, operation: str, error_msg: str):
    """[test_validation_service-005-011-013] 検証操作でのNotFoundError。"""
    # Arrange
    service = AdminValidationService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        if operation == "get":
            await service.get_validation(non_existent_id)
        elif operation == "update":
            validation_update = AnalysisValidationUpdate(name="更新")
            await service.update_validation(non_existent_id, validation_update)
        elif operation == "delete":
            await service.delete_validation(non_existent_id)

    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_validation_success(db_session: AsyncSession):
    """[test_validation_service-006] 検証作成の成功ケース。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation_create = AnalysisValidationCreate(
        name="新規検証",
        validation_order=1,
    )

    # Act
    result = await service.create_validation(validation_create)

    # Assert
    assert result is not None
    assert result.name == "新規検証"
    assert result.validation_order == 1


@pytest.mark.asyncio
async def test_create_multiple_validations(db_session: AsyncSession):
    """[test_validation_service-007] 複数検証の作成。"""
    # Arrange
    service = AdminValidationService(db_session)

    validations_data = [
        {"name": "市場拡大", "validation_order": 1},
        {"name": "コスト削減", "validation_order": 2},
        {"name": "品質向上", "validation_order": 3},
    ]

    # Act
    created_validations = []
    for data in validations_data:
        validation_create = AnalysisValidationCreate(**data)
        result = await service.create_validation(validation_create)
        created_validations.append(result)

    # Assert
    assert len(created_validations) == 3

    list_result = await service.list_validations()
    assert list_result.total == 3


@pytest.mark.asyncio
async def test_update_validation_success(db_session: AsyncSession):
    """[test_validation_service-008] 検証更新の成功ケース。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="元の検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)

    validation_update = AnalysisValidationUpdate(
        name="更新後の検証",
        validation_order=5,
    )

    # Act
    result = await service.update_validation(validation.id, validation_update)

    # Assert
    assert result is not None
    assert result.name == "更新後の検証"
    assert result.validation_order == 5


@pytest.mark.asyncio
async def test_update_validation_partial_name(db_session: AsyncSession):
    """[test_validation_service-009] 検証の名前のみ部分更新。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="元の検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)

    # 名前のみ更新
    validation_update = AnalysisValidationUpdate(name="名前だけ更新")

    # Act
    result = await service.update_validation(validation.id, validation_update)

    # Assert
    assert result is not None
    assert result.name == "名前だけ更新"


@pytest.mark.asyncio
async def test_update_validation_partial_order(db_session: AsyncSession):
    """[test_validation_service-010] 検証の順序のみ部分更新。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="元の検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)

    # 順序のみ更新
    validation_update = AnalysisValidationUpdate(validation_order=10)

    # Act
    result = await service.update_validation(validation.id, validation_update)

    # Assert
    assert result is not None
    assert result.validation_order == 10


@pytest.mark.asyncio
async def test_delete_validation_success(db_session: AsyncSession):
    """[test_validation_service-012] 検証削除の成功ケース。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="削除対象検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)
    validation_id = validation.id

    # Act
    await service.delete_validation(validation_id)

    # Assert - 削除後に取得するとNotFoundError
    with pytest.raises(NotFoundError):
        await service.get_validation(validation_id)


@pytest.mark.asyncio
async def test_delete_validation_with_issues_conflict(db_session: AsyncSession):
    """[test_validation_service-014] 課題が紐づいている検証削除時のConflictError。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation = AnalysisValidationMaster(
        name="課題付き検証",
        validation_order=1,
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)

    # has_issuesがTrueを返すようにモック
    with patch.object(
        service.repository,
        "has_issues",
        new_callable=AsyncMock,
        return_value=True,
    ):
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await service.delete_validation(validation.id)

        assert "課題が紐づいている" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validation_order_uniqueness(db_session: AsyncSession):
    """[test_validation_service-015] 検証順序の重複が許容されることを確認。"""
    # Arrange
    service = AdminValidationService(db_session)

    # 同じ順序の検証を2つ作成
    validation1 = AnalysisValidationCreate(
        name="検証A",
        validation_order=1,
    )
    validation2 = AnalysisValidationCreate(
        name="検証B",
        validation_order=1,  # 同じ順序
    )

    # Act
    result1 = await service.create_validation(validation1)
    result2 = await service.create_validation(validation2)

    # Assert - 両方作成できることを確認
    assert result1 is not None
    assert result2 is not None
    assert result1.validation_order == result2.validation_order


@pytest.mark.asyncio
async def test_get_validation_with_timestamps(db_session: AsyncSession):
    """[test_validation_service-016] タイムスタンプが正しく取得できることを確認。"""
    # Arrange
    service = AdminValidationService(db_session)

    validation_create = AnalysisValidationCreate(
        name="タイムスタンプテスト",
        validation_order=1,
    )

    # Act
    result = await service.create_validation(validation_create)

    # Assert
    assert result is not None
    assert result.created_at is not None
    assert result.updated_at is not None
    assert isinstance(result.created_at, datetime)
    assert isinstance(result.updated_at, datetime)
