"""Azure AD認証用UserServiceのテスト。"""

import uuid
from datetime import datetime

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models import User
from app.services import UserService


@pytest.mark.asyncio
async def test_get_or_create_by_azure_oid_new_user(db_session):
    """新規ユーザー作成テスト（Azure OID初回ログイン）。"""
    # Arrange
    service = UserService(db_session)

    # Act
    user = await service.get_or_create_by_azure_oid(
        azure_oid="new-azure-oid-12345",
        email="newuser@company.com",
        display_name="New User",
        roles=["User"],
    )

    # Assert
    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.azure_oid == "new-azure-oid-12345"
    assert user.email == "newuser@company.com"
    assert user.display_name == "New User"
    assert user.roles == ["User"]
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_or_create_by_azure_oid_existing_user(db_session):
    """既存ユーザー取得テスト（Azure OID 2回目以降のログイン）。"""
    # Arrange
    existing_user = User(
        azure_oid="existing-oid-12345",
        email="existing@company.com",
        display_name="Existing User",
        roles=["User"],
    )
    db_session.add(existing_user)
    await db_session.commit()
    await db_session.refresh(existing_user)

    service = UserService(db_session)

    # Act
    user = await service.get_or_create_by_azure_oid(
        azure_oid="existing-oid-12345",
        email="existing@company.com",
        display_name="Existing User",
    )

    # Assert
    assert user.id == existing_user.id
    assert user.azure_oid == "existing-oid-12345"
    assert user.email == "existing@company.com"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,old_value,new_value",
    [
        ("email", "old@company.com", "new@company.com"),
        ("display_name", "Old Name", "New Name"),
    ],
)
async def test_get_or_create_by_azure_oid_updates_fields(db_session, field, old_value, new_value):
    """Azure OIDによるフィールド更新テスト（パラメータ化）。"""
    # Arrange
    initial_values = {
        "azure_oid": "update-oid",
        "email": "user@company.com" if field != "email" else old_value,
        "display_name": "User" if field != "display_name" else old_value,
        "roles": ["User"],
    }
    existing_user = User(**initial_values)
    db_session.add(existing_user)
    await db_session.commit()

    service = UserService(db_session)

    # Act
    update_values = {
        "azure_oid": "update-oid",
        "email": new_value if field == "email" else initial_values["email"],
        "display_name": new_value if field == "display_name" else initial_values["display_name"],
    }
    user = await service.get_or_create_by_azure_oid(**update_values)

    # Assert
    assert user.id == existing_user.id
    assert getattr(user, field) == new_value


@pytest.mark.asyncio
async def test_get_or_create_by_azure_oid_duplicate_email(db_session):
    """メールアドレス重複エラーテスト。"""
    # Arrange
    user1 = User(
        azure_oid="user1-oid",
        email="duplicate@company.com",
        display_name="User 1",
    )
    db_session.add(user1)
    await db_session.commit()

    service = UserService(db_session)

    # Act & Assert - 別のOIDで同じメールは作成できない
    with pytest.raises(ValidationError):
        await service.get_or_create_by_azure_oid(
            azure_oid="user2-oid",  # 別のOID
            email="duplicate@company.com",  # 同じメール
            display_name="User 2",
        )


@pytest.mark.asyncio
async def test_update_last_login(db_session):
    """最終ログイン情報更新テスト。"""
    # Arrange
    user = User(
        azure_oid="login-oid",
        email="login@company.com",
        display_name="Login User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.last_login is None

    service = UserService(db_session)

    # Act
    updated_user = await service.update_last_login(
        user_id=user.id,
        client_ip="192.168.1.1",
    )

    # Assert
    assert updated_user.last_login is not None
    assert isinstance(updated_user.last_login, datetime)


@pytest.mark.asyncio
async def test_update_last_login_user_not_found(db_session):
    """存在しないユーザーの最終ログイン更新エラーテスト。"""
    # Arrange
    service = UserService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_last_login(user_id=non_existent_id)


@pytest.mark.asyncio
async def test_get_user(db_session):
    """ユーザー取得テスト。"""
    # Arrange
    user = User(
        azure_oid="get-oid",
        email="get@company.com",
        display_name="Get User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = UserService(db_session)

    # Act
    result = await service.get_user(user.id)

    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.email == "get@company.com"


@pytest.mark.asyncio
async def test_get_user_not_found(db_session):
    """存在しないユーザー取得テスト。"""
    # Arrange
    service = UserService(db_session)
    non_existent_id = uuid.uuid4()

    # Act
    result = await service.get_user(non_existent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email(db_session):
    """メールアドレスでユーザー取得テスト。"""
    # Arrange
    user = User(
        azure_oid="email-oid",
        email="email@company.com",
        display_name="Email User",
    )
    db_session.add(user)
    await db_session.commit()

    service = UserService(db_session)

    # Act
    result = await service.get_user_by_email("email@company.com")

    # Assert
    assert result is not None
    assert result.email == "email@company.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session):
    """存在しないメールでユーザー取得エラーテスト。"""
    # Arrange
    service = UserService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_user_by_email("nonexistent@company.com")


@pytest.mark.asyncio
async def test_get_user_by_azure_oid(db_session):
    """Azure OIDでユーザー取得テスト。"""
    # Arrange
    user = User(
        azure_oid="oid-test-12345",
        email="oid@company.com",
        display_name="OID User",
    )
    db_session.add(user)
    await db_session.commit()

    service = UserService(db_session)

    # Act
    result = await service.get_user_by_azure_oid("oid-test-12345")

    # Assert
    assert result is not None
    assert result.azure_oid == "oid-test-12345"


@pytest.mark.asyncio
async def test_get_user_by_azure_oid_not_found(db_session):
    """存在しないAzure OIDでユーザー取得エラーテスト。"""
    # Arrange
    service = UserService(db_session)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_user_by_azure_oid("nonexistent-oid")


@pytest.mark.asyncio
async def test_list_active_users(db_session):
    """アクティブユーザー一覧取得テスト。"""
    # Arrange
    # アクティブユーザー3人
    for i in range(3):
        user = User(
            azure_oid=f"active-{i}",
            email=f"active{i}@company.com",
            display_name=f"Active {i}",
            is_active=True,
        )
        db_session.add(user)

    # 非アクティブユーザー2人
    for i in range(2):
        user = User(
            azure_oid=f"inactive-{i}",
            email=f"inactive{i}@company.com",
            display_name=f"Inactive {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    service = UserService(db_session)

    # Act
    active_users = await service.list_active_users(skip=0, limit=10)

    # Assert
    assert len(active_users) == 3
    assert all(user.is_active for user in active_users)


@pytest.mark.asyncio
async def test_list_users(db_session):
    """全ユーザー一覧取得テスト。"""
    # Arrange
    # アクティブユーザー3人 + 非アクティブ2人
    for i in range(3):
        user = User(
            azure_oid=f"user-{i}",
            email=f"user{i}@company.com",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)

    for i in range(2):
        user = User(
            azure_oid=f"inactive-{i}",
            email=f"inactive{i}@company.com",
            display_name=f"Inactive {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    service = UserService(db_session)

    # Act
    all_users = await service.list_users(skip=0, limit=10)

    # Assert
    assert len(all_users) == 5  # 全員取得される


@pytest.mark.asyncio
async def test_count_users_active_only(db_session):
    """アクティブユーザー数カウントテスト。"""
    # Arrange
    # アクティブユーザー3人 + 非アクティブ2人
    for i in range(3):
        user = User(
            azure_oid=f"count-active-user-{i}",
            email=f"countactiveuser{i}@company.com",
            display_name=f"Count Active User {i}",
            is_active=True,
        )
        db_session.add(user)

    for i in range(2):
        user = User(
            azure_oid=f"count-inactive-user-{i}",
            email=f"countinactiveuser{i}@company.com",
            display_name=f"Count Inactive User {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    service = UserService(db_session)

    # Act
    active_count = await service.count_users(is_active=True)

    # Assert
    assert active_count == 3  # アクティブユーザーのみ


@pytest.mark.asyncio
async def test_count_users_inactive_only(db_session):
    """非アクティブユーザー数カウントテスト。"""
    # Arrange
    # アクティブユーザー3人 + 非アクティブ2人
    for i in range(3):
        user = User(
            azure_oid=f"count2-active-user-{i}",
            email=f"count2activeuser{i}@company.com",
            display_name=f"Count2 Active User {i}",
            is_active=True,
        )
        db_session.add(user)

    for i in range(2):
        user = User(
            azure_oid=f"count2-inactive-user-{i}",
            email=f"count2inactiveuser{i}@company.com",
            display_name=f"Count2 Inactive User {i}",
            is_active=False,
        )
        db_session.add(user)

    await db_session.commit()

    service = UserService(db_session)

    # Act
    inactive_count = await service.count_users(is_active=False)

    # Assert
    assert inactive_count == 2  # 非アクティブユーザーのみ


@pytest.mark.asyncio
async def test_update_user_roles_by_admin(db_session):
    """ユーザーのロール更新テスト（管理者）。"""
    # Arrange
    user = User(
        azure_oid="update-roles-oid",
        email="roles@company.com",
        display_name="User",
        roles=["User"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = UserService(db_session)

    # Act - 管理者がロールを更新
    updated_user = await service.update_user(
        user_id=user.id,
        update_data={"roles": ["SystemAdmin", "User"]},
        current_user_roles=["SystemAdmin"],
    )

    # Assert
    assert updated_user.id == user.id
    assert updated_user.roles == ["SystemAdmin", "User"]


@pytest.mark.asyncio
async def test_update_user_roles_by_non_admin_fails(db_session):
    """一般ユーザーによるロール更新の失敗テスト。"""
    # Arrange
    user = User(
        azure_oid="fail-update-oid",
        email="fail@company.com",
        display_name="User",
        roles=["User"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = UserService(db_session)

    # Act & Assert - 一般ユーザーがロールを更新しようとすると失敗
    with pytest.raises(ValidationError) as exc_info:
        await service.update_user(
            user_id=user.id,
            update_data={"roles": ["SystemAdmin", "User"]},
            current_user_roles=["User"],  # SystemAdminではない
        )

    assert "管理者権限が必要です" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_user_is_active_by_admin(db_session):
    """ユーザーのis_active更新テスト（管理者）。"""
    # Arrange
    user = User(
        azure_oid="update-active-oid",
        email="active@company.com",
        display_name="User",
        roles=["User"],
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = UserService(db_session)

    # Act - 管理者がis_activeを更新
    updated_user = await service.update_user(
        user_id=user.id,
        update_data={"is_active": False},
        current_user_roles=["SystemAdmin"],
    )

    # Assert
    assert updated_user.id == user.id
    assert updated_user.is_active is False


@pytest.mark.asyncio
async def test_update_user_is_active_by_non_admin_fails(db_session):
    """一般ユーザーによるis_active更新の失敗テスト。"""
    # Arrange
    user = User(
        azure_oid="fail-active-oid",
        email="fail-active@company.com",
        display_name="User",
        roles=["User"],
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = UserService(db_session)

    # Act & Assert - 一般ユーザーがis_activeを更新しようとすると失敗
    with pytest.raises(ValidationError) as exc_info:
        await service.update_user(
            user_id=user.id,
            update_data={"is_active": False},
            current_user_roles=["User"],  # SystemAdminではない
        )

    assert "管理者権限が必要です" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_user_not_found(db_session):
    """存在しないユーザーの更新エラーテスト。"""
    # Arrange
    service = UserService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_user(
            user_id=non_existent_id,
            update_data={"display_name": "New Name"},
            current_user_roles=["User"],
        )
