"""ドライバーツリーノードサービスのテスト。

このテストファイルは、DriverTreeNodeServiceの各メソッドをテストします。

対応メソッド:
    - create_node: ノード作成
    - get_node: ノード詳細取得
    - update_node: ノード更新
    - delete_node: ノード削除
    - download_node_preview: ノードプレビューダウンロード
    - create_policy: 施策作成
    - list_policies: 施策一覧取得
    - update_policy: 施策更新
    - delete_policy: 施策削除
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.services.driver_tree import DriverTreeNodeService

# ================================================================================
# ノード CRUD
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "label,node_type",
    [
        ("新規ノード", "入力"),
        ("計算ノード", "計算"),
        ("100", "定数"),
    ],
    ids=["input", "calculation", "constant"],
)
async def test_create_node_types(db_session: AsyncSession, test_data_seeder, label, node_type):
    """[test_driver_tree_node-001~003] 各種ノードタイプの作成。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.create_node(
        project_id=project.id,
        tree_id=tree.id,
        label=label,
        node_type=node_type,
        position_x=300,
        position_y=200,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert "tree" in result
    assert "created_node_id" in result
    assert result["created_node_id"] is not None


@pytest.mark.asyncio
async def test_create_node_invalid_type(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-004] 不正なノードタイプでValidationError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    tree = data["tree"]

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.create_node(
            project_id=project.id,
            tree_id=tree.id,
            label="不正ノード",
            node_type="不正なタイプ",
            position_x=300,
            position_y=200,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_get_node_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-006] ノード詳細取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.get_node(
        project_id=project.id,
        node_id=root_node.id,
        user_id=owner.id,
    )

    # Assert
    assert result["node_id"] == root_node.id
    assert result["label"] == root_node.label
    assert result["node_type"] == root_node.node_type


@pytest.mark.asyncio
async def test_get_node_with_relationship(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-007] リレーションシップを持つノードの詳細取得。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.get_node(
        project_id=project.id,
        node_id=root_node.id,
        user_id=owner.id,
    )

    # Assert
    assert result["relationship"] is not None
    assert result["relationship"]["operator"] == "+"
    assert len(result["relationship"]["child_id_list"]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "update_field,update_kwargs",
    [
        ("label", {"label": "更新されたラベル"}),
        ("position", {"position_x": 500, "position_y": 300}),
        ("node_type", {"node_type": "定数"}),
    ],
    ids=["label", "position", "node_type"],
)
async def test_update_node_fields(
    db_session: AsyncSession, test_data_seeder, update_field, update_kwargs
):
    """[test_driver_tree_node-009~011] ノードの各フィールド更新。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]

    service = DriverTreeNodeService(db_session)

    # Prepare update parameters with defaults
    update_params = {
        "project_id": project.id,
        "node_id": child_node.id,
        "label": None,
        "node_type": None,
        "position_x": None,
        "position_y": None,
        "operator": None,
        "children_id_list": None,
        "user_id": owner.id,
    }
    update_params.update(update_kwargs)

    # Act
    result = await service.update_node(**update_params)
    await db_session.commit()

    # Assert
    assert "tree" in result


@pytest.mark.asyncio
async def test_update_node_invalid_type(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-012] 不正なノードタイプへの更新でValidationError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.update_node(
            project_id=project.id,
            node_id=child_node.id,
            label=None,
            node_type="不正なタイプ",
            position_x=None,
            position_y=None,
            operator=None,
            children_id_list=None,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_delete_node_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-014] ノード削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][1]  # 2番目の子ノードを削除
    node_id = child_node.id

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.delete_node(
        project_id=project.id,
        node_id=node_id,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert "tree" in result

    # 削除されたことを確認
    with pytest.raises(NotFoundError):
        await service.get_node(
            project_id=project.id,
            node_id=node_id,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_delete_root_node_error(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-015] ルートノードの削除でValidationError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    root_node = data["root_node"]

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.delete_node(
            project_id=project.id,
            node_id=root_node.id,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_download_node_preview_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-017] ノードプレビューダウンロードの成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]

    service = DriverTreeNodeService(db_session)

    # Act
    response = await service.download_node_preview(
        project_id=project.id,
        node_id=child_node.id,
        user_id=owner.id,
    )

    # Assert
    assert response.media_type == "text/csv"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation,method_name,extra_args",
    [
        ("create_node", "create_node", {"tree_id": "fake_uuid", "label": "新規ノード", "node_type": "入力", "position_x": 300, "position_y": 200}),
        ("get_node", "get_node", {"node_id": "fake_uuid"}),
        ("update_node", "update_node", {"node_id": "fake_uuid", "label": "更新ラベル", "node_type": None, "position_x": None, "position_y": None, "operator": None, "children_id_list": None}),
        ("delete_node", "delete_node", {"node_id": "fake_uuid"}),
        ("download_preview", "download_node_preview", {"node_id": "fake_uuid"}),
    ],
    ids=["create_node", "get_node", "update_node", "delete_node", "download_preview"],
)
async def test_node_operations_not_found(
    db_session: AsyncSession, test_data_seeder, operation, method_name, extra_args
):
    """[test_driver_tree_node-005,008,013,016,018] ノード操作でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeNodeService(db_session)

    # Replace fake_uuid placeholders with actual UUIDs
    for key, value in extra_args.items():
        if value == "fake_uuid":
            extra_args[key] = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError):
        method = getattr(service, method_name)
        await method(
            project_id=project.id,
            user_id=owner.id,
            **extra_args
        )


# ================================================================================
# 施策 CRUD
# ================================================================================


@pytest.mark.asyncio
async def test_create_policy_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-019] 施策作成の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][1]

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.create_policy(
        project_id=project.id,
        node_id=child_node.id,
        name="新規施策",
        value=20.0,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert result["node_id"] == child_node.id
    assert "policies" in result
    assert len(result["policies"]) >= 1


@pytest.mark.asyncio
async def test_create_policy_node_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-020] 存在しないノードへの施策作成でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.create_policy(
            project_id=project.id,
            node_id=uuid.uuid4(),
            name="新規施策",
            value=20.0,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_list_policies_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-021] 施策一覧取得の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.list_policies(
        project_id=project.id,
        node_id=child_node.id,
        user_id=owner.id,
    )

    # Assert
    assert result["node_id"] == child_node.id
    assert "policies" in result
    assert len(result["policies"]) >= 1  # シードデータに施策が含まれている


@pytest.mark.asyncio
async def test_list_policies_empty(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-022] 施策がないノードの一覧取得。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][1]  # 施策が設定されていないノード

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.list_policies(
        project_id=project.id,
        node_id=child_node.id,
        user_id=owner.id,
    )

    # Assert
    assert result["node_id"] == child_node.id
    assert result["policies"] == []


@pytest.mark.asyncio
async def test_list_policies_node_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-023] 存在しないノードの施策一覧取得でNotFoundError。"""
    # Arrange
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.list_policies(
            project_id=project.id,
            node_id=uuid.uuid4(),
            user_id=owner.id,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "update_field,update_kwargs,expected_check",
    [
        ("name", {"name": "更新された施策", "value": None}, lambda p: p["name"] == "更新された施策"),
        ("value", {"name": None, "value": 99.9}, lambda p: p["value"] == 99.9),
    ],
    ids=["name", "value"],
)
async def test_update_policy_fields(
    db_session: AsyncSession, test_data_seeder, update_field, update_kwargs, expected_check
):
    """[test_driver_tree_node-024~025] 施策の各フィールド更新。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]
    policy = data["policy"]

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.update_policy(
        project_id=project.id,
        node_id=child_node.id,
        policy_id=policy.id,
        user_id=owner.id,
        **update_kwargs
    )
    await db_session.commit()

    # Assert
    assert result["node_id"] == child_node.id
    assert any(expected_check(p) for p in result["policies"])


@pytest.mark.asyncio
async def test_update_policy_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-026] 存在しない施策の更新でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_policy(
            project_id=project.id,
            node_id=child_node.id,
            policy_id=uuid.uuid4(),
            name="更新名",
            value=None,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_update_policy_wrong_node(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-027] 別ノードの施策更新でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    policy = data["policy"]
    wrong_node = data["child_nodes"][1]  # 施策が属していないノード

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_policy(
            project_id=project.id,
            node_id=wrong_node.id,
            policy_id=policy.id,
            name="更新名",
            value=None,
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_delete_policy_success(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-028] 施策削除の成功ケース。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]
    policy = data["policy"]
    policy_id = policy.id

    service = DriverTreeNodeService(db_session)

    # Act
    result = await service.delete_policy(
        project_id=project.id,
        node_id=child_node.id,
        policy_id=policy_id,
        user_id=owner.id,
    )
    await db_session.commit()

    # Assert
    assert result["node_id"] == child_node.id
    assert not any(p["policy_id"] == policy_id for p in result["policies"])


@pytest.mark.asyncio
async def test_delete_policy_not_found(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-029] 存在しない施策の削除でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    child_node = data["child_nodes"][0]

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.delete_policy(
            project_id=project.id,
            node_id=child_node.id,
            policy_id=uuid.uuid4(),
            user_id=owner.id,
        )


@pytest.mark.asyncio
async def test_delete_policy_wrong_node(db_session: AsyncSession, test_data_seeder):
    """[test_driver_tree_node-030] 別ノードの施策削除でNotFoundError。"""
    # Arrange
    data = await test_data_seeder.seed_driver_tree_dataset()
    project = data["project"]
    owner = data["owner"]
    policy = data["policy"]
    wrong_node = data["child_nodes"][1]  # 施策が属していないノード

    service = DriverTreeNodeService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.delete_policy(
            project_id=project.id,
            node_id=wrong_node.id,
            policy_id=policy.id,
            user_id=owner.id,
        )
