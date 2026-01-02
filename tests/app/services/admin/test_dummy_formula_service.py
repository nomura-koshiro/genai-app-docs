"""ダミー数式マスタ管理サービスのテスト。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.analysis.analysis_dummy_formula_master import AnalysisDummyFormulaMaster
from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
from app.models.analysis.analysis_validation_master import AnalysisValidationMaster
from app.schemas.analysis.analysis_template import (
    AnalysisDummyFormulaCreate,
    AnalysisDummyFormulaUpdate,
)
from app.services.admin.dummy_formula import AdminDummyFormulaService


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
async def test_list_formulas_success(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-001] ダミー数式一覧取得の成功ケース。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula = AnalysisDummyFormulaMaster(
        issue_id=test_issue.id,
        name="平均売上",
        value="5000円",
        formula_order=1,
    )
    db_session.add(formula)
    await db_session.commit()

    # Act
    result = await service.list_formulas(skip=0, limit=100)

    # Assert
    assert result is not None
    assert result.total >= 1
    assert len(result.formulas) >= 1
    assert result.skip == 0
    assert result.limit == 100


@pytest.mark.asyncio
async def test_list_formulas_with_issue_filter(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-002] issue_idでフィルタしたダミー数式一覧取得。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula = AnalysisDummyFormulaMaster(
        issue_id=test_issue.id,
        name="平均売上",
        value="5000円",
        formula_order=1,
    )
    db_session.add(formula)
    await db_session.commit()

    # Act
    result = await service.list_formulas(skip=0, limit=100, issue_id=test_issue.id)

    # Assert
    assert result is not None
    assert result.total >= 1
    for formula_response in result.formulas:
        assert formula_response.issue_id == test_issue.id


@pytest.mark.asyncio
async def test_list_formulas_with_pagination(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-003] ダミー数式一覧取得のページネーション。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    for i in range(5):
        formula = AnalysisDummyFormulaMaster(
            issue_id=test_issue.id,
            name=f"数式{i}",
            value=f"{i * 1000}円",
            formula_order=i + 1,
        )
        db_session.add(formula)
    await db_session.commit()

    # Act
    result = await service.list_formulas(skip=2, limit=2)

    # Assert
    assert result is not None
    assert result.skip == 2
    assert result.limit == 2
    assert len(result.formulas) <= 2


@pytest.mark.asyncio
async def test_get_formula_success(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-004] ダミー数式詳細取得の成功ケース。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula = AnalysisDummyFormulaMaster(
        issue_id=test_issue.id,
        name="平均売上",
        value="5000円",
        formula_order=1,
    )
    db_session.add(formula)
    await db_session.commit()
    await db_session.refresh(formula)

    # Act
    result = await service.get_formula(formula.id)

    # Assert
    assert result is not None
    assert result.id == formula.id
    assert result.name == "平均売上"
    assert result.value == "5000円"
    assert result.issue_id == test_issue.id


@pytest.mark.parametrize(
    "operation,error_msg",
    [
        ("get", "ダミー数式マスタが見つかりません"),
        ("update", "ダミー数式マスタが見つかりません"),
        ("delete", "ダミー数式マスタが見つかりません"),
    ],
    ids=["get_not_found", "update_not_found", "delete_not_found"],
)
@pytest.mark.asyncio
async def test_formula_not_found_errors(db_session: AsyncSession, operation: str, error_msg: str):
    """[test_dummy_formula_service-005-009-011] ダミー数式操作でのNotFoundError。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        if operation == "get":
            await service.get_formula(non_existent_id)
        elif operation == "update":
            formula_update = AnalysisDummyFormulaUpdate(name="更新")
            await service.update_formula(non_existent_id, formula_update)
        elif operation == "delete":
            await service.delete_formula(non_existent_id)

    assert error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_formula_success(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-006] ダミー数式作成の成功ケース。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula_create = AnalysisDummyFormulaCreate(
        issue_id=test_issue.id,
        name="新規数式",
        value="10000円",
        formula_order=1,
    )

    # Act
    result = await service.create_formula(formula_create)

    # Assert
    assert result is not None
    assert result.name == "新規数式"
    assert result.value == "10000円"
    assert result.issue_id == test_issue.id
    assert result.formula_order == 1


@pytest.mark.asyncio
async def test_update_formula_success(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-007] ダミー数式更新の成功ケース。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula = AnalysisDummyFormulaMaster(
        issue_id=test_issue.id,
        name="元の数式",
        value="5000円",
        formula_order=1,
    )
    db_session.add(formula)
    await db_session.commit()
    await db_session.refresh(formula)

    formula_update = AnalysisDummyFormulaUpdate(
        name="更新後数式",
        value="8000円",
        formula_order=2,
    )

    # Act
    result = await service.update_formula(formula.id, formula_update)

    # Assert
    assert result is not None
    assert result.name == "更新後数式"
    assert result.value == "8000円"
    assert result.formula_order == 2


@pytest.mark.asyncio
async def test_update_formula_partial(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-008] ダミー数式の部分更新。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula = AnalysisDummyFormulaMaster(
        issue_id=test_issue.id,
        name="元の数式",
        value="5000円",
        formula_order=1,
    )
    db_session.add(formula)
    await db_session.commit()
    await db_session.refresh(formula)

    # 名前のみ更新
    formula_update = AnalysisDummyFormulaUpdate(name="名前だけ更新")

    # Act
    result = await service.update_formula(formula.id, formula_update)

    # Assert
    assert result is not None
    assert result.name == "名前だけ更新"


@pytest.mark.asyncio
async def test_delete_formula_success(db_session: AsyncSession, test_issue):
    """[test_dummy_formula_service-010] ダミー数式削除の成功ケース。"""
    # Arrange
    service = AdminDummyFormulaService(db_session)

    formula = AnalysisDummyFormulaMaster(
        issue_id=test_issue.id,
        name="削除対象数式",
        value="1000円",
        formula_order=1,
    )
    db_session.add(formula)
    await db_session.commit()
    await db_session.refresh(formula)
    formula_id = formula.id

    # Act
    await service.delete_formula(formula_id)

    # Assert - 削除後に取得するとNotFoundError
    with pytest.raises(NotFoundError):
        await service.get_formula(formula_id)
