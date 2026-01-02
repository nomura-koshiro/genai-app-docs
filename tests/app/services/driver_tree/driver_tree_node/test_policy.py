"""ドライバーツリーノード施策サービスのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.driver_tree.driver_tree_node.policy import DriverTreeNodePolicyService


@pytest.mark.asyncio
async def test_create_policy_success(db_session: AsyncSession):
    """[test_policy-001] 施策作成の成功ケース。"""
    # Arrange
    service = DriverTreeNodePolicyService(db_session)
    project_id = uuid.uuid4()
    node_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_node = MagicMock()
    mock_policy = MagicMock()
    mock_policy.id = uuid.uuid4()
    mock_policy.node_id = node_id
    mock_policy.label = "テスト施策"
    mock_policy.value = 100.0

    with (
        patch.object(
            service,
            "_get_node_with_validation",
            new_callable=AsyncMock,
            return_value=mock_node,
        ),
        patch.object(
            service.policy_repository,
            "create",
            new_callable=AsyncMock,
            return_value=mock_policy,
        ),
        patch.object(
            service,
            "_build_policies_response",
            new_callable=AsyncMock,
            return_value={"node_id": node_id, "policies": []},
        ),
    ):
        # Act
        result = await service.create_policy(project_id, node_id, "テスト施策", 100.0, user_id)

        # Assert
        assert result is not None
        assert result["node_id"] == node_id


@pytest.mark.asyncio
async def test_list_policies_success(db_session: AsyncSession):
    """[test_policy-002] 施策一覧取得の成功ケース。"""
    # Arrange
    service = DriverTreeNodePolicyService(db_session)
    project_id = uuid.uuid4()
    node_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_node = MagicMock()

    with (
        patch.object(
            service,
            "_get_node_with_validation",
            new_callable=AsyncMock,
            return_value=mock_node,
        ),
        patch.object(
            service,
            "_build_policies_response",
            new_callable=AsyncMock,
            return_value={"node_id": node_id, "policies": []},
        ),
    ):
        # Act
        result = await service.list_policies(project_id, node_id, user_id)

        # Assert
        assert result is not None
        assert result["node_id"] == node_id
        assert result["policies"] == []


@pytest.mark.asyncio
async def test_update_policy_success(db_session: AsyncSession):
    """[test_policy-003] 施策更新の成功ケース。"""
    # Arrange
    service = DriverTreeNodePolicyService(db_session)
    project_id = uuid.uuid4()
    node_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_node = MagicMock()
    mock_policy = MagicMock()
    mock_policy.id = policy_id
    mock_policy.node_id = node_id

    with (
        patch.object(
            service,
            "_get_node_with_validation",
            new_callable=AsyncMock,
            return_value=mock_node,
        ),
        patch.object(
            service.policy_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_policy,
        ),
        patch.object(
            service.policy_repository,
            "update",
            new_callable=AsyncMock,
        ),
        patch.object(
            service,
            "_build_policies_response",
            new_callable=AsyncMock,
            return_value={"node_id": node_id, "policies": []},
        ),
    ):
        # Act
        result = await service.update_policy(project_id, node_id, policy_id, "更新施策", 200.0, user_id)

        # Assert
        assert result is not None
        assert result["node_id"] == node_id


@pytest.mark.parametrize(
    "scenario,policy_return,expected_error_msg",
    [
        ("not_found", None, "施策が見つかりません"),
        ("node_mismatch", "mismatch", "このノードに施策が見つかりません"),
    ],
    ids=["not_found", "node_mismatch"],
)
@pytest.mark.asyncio
async def test_update_policy_errors(
    db_session: AsyncSession, scenario: str, policy_return, expected_error_msg: str
):
    """[test_policy-004/005] 施策更新時のエラーケース。"""
    # Arrange
    service = DriverTreeNodePolicyService(db_session)
    project_id = uuid.uuid4()
    node_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_node = MagicMock()

    if policy_return == "mismatch":
        mock_policy = MagicMock()
        mock_policy.id = policy_id
        mock_policy.node_id = uuid.uuid4()  # 異なるノードID
        policy_return_value = mock_policy
    else:
        policy_return_value = None

    with (
        patch.object(
            service,
            "_get_node_with_validation",
            new_callable=AsyncMock,
            return_value=mock_node,
        ),
        patch.object(
            service.policy_repository,
            "get",
            new_callable=AsyncMock,
            return_value=policy_return_value,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_policy(project_id, node_id, policy_id, "更新施策", 200.0, user_id)

        assert expected_error_msg in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_policy_success(db_session: AsyncSession):
    """[test_policy-006] 施策削除の成功ケース。"""
    # Arrange
    service = DriverTreeNodePolicyService(db_session)
    project_id = uuid.uuid4()
    node_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_node = MagicMock()
    mock_policy = MagicMock()
    mock_policy.id = policy_id
    mock_policy.node_id = node_id

    with (
        patch.object(
            service,
            "_get_node_with_validation",
            new_callable=AsyncMock,
            return_value=mock_node,
        ),
        patch.object(
            service.policy_repository,
            "get",
            new_callable=AsyncMock,
            return_value=mock_policy,
        ),
        patch.object(
            service.policy_repository,
            "delete",
            new_callable=AsyncMock,
        ),
        patch.object(
            service,
            "_build_policies_response",
            new_callable=AsyncMock,
            return_value={"node_id": node_id, "policies": []},
        ),
    ):
        # Act
        result = await service.delete_policy(project_id, node_id, policy_id, user_id)

        # Assert
        assert result is not None
        assert result["node_id"] == node_id


@pytest.mark.parametrize(
    "scenario,policy_return,expected_error_msg",
    [
        ("not_found", None, "施策が見つかりません"),
        ("node_mismatch", "mismatch", "このノードに施策が見つかりません"),
    ],
    ids=["not_found", "node_mismatch"],
)
@pytest.mark.asyncio
async def test_delete_policy_errors(
    db_session: AsyncSession, scenario: str, policy_return, expected_error_msg: str
):
    """[test_policy-007/008] 施策削除時のエラーケース。"""
    # Arrange
    service = DriverTreeNodePolicyService(db_session)
    project_id = uuid.uuid4()
    node_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_node = MagicMock()

    if policy_return == "mismatch":
        mock_policy = MagicMock()
        mock_policy.id = policy_id
        mock_policy.node_id = uuid.uuid4()  # 異なるノードID
        policy_return_value = mock_policy
    else:
        policy_return_value = None

    with (
        patch.object(
            service,
            "_get_node_with_validation",
            new_callable=AsyncMock,
            return_value=mock_node,
        ),
        patch.object(
            service.policy_repository,
            "get",
            new_callable=AsyncMock,
            return_value=policy_return_value,
        ),
    ):
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_policy(project_id, node_id, policy_id, user_id)

        assert expected_error_msg in str(exc_info.value)
