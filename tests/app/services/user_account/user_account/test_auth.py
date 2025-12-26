"""Azure AD認証関連のUserAccountServiceテスト。"""

import uuid
from datetime import datetime

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models import UserAccount
from app.services import UserAccountService


@pytest.mark.asyncio
async def test_get_or_create_by_azure_oid_new_user(db_session):
    """[test_user_account-001] 新規ユーザー作成テスト（Azure OID初回ログイン）。"""
    # Arrange
    service = UserAccountService(db_session)

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
    """[test_user_account-002] 既存ユーザー取得テスト（Azure OID 2回目以降のログイン）。"""
    # Arrange
    existing_user = UserAccount(
        azure_oid="existing-oid-12345",
        email="existing@company.com",
        display_name="Existing User",
        roles=["User"],
    )
    db_session.add(existing_user)
    await db_session.commit()
    await db_session.refresh(existing_user)

    service = UserAccountService(db_session)

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
    """[test_user_account-003] Azure OIDによるフィールド更新テスト（パラメータ化）。"""
    # Arrange
    initial_values = {
        "azure_oid": "update-oid",
        "email": "user@company.com" if field != "email" else old_value,
        "display_name": "User" if field != "display_name" else old_value,
        "roles": ["User"],
    }
    existing_user = UserAccount(**initial_values)
    db_session.add(existing_user)
    await db_session.commit()

    service = UserAccountService(db_session)

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
    """[test_user_account-004] メールアドレス重複エラーテスト。"""
    # Arrange
    user1 = UserAccount(
        azure_oid="user1-oid",
        email="duplicate@company.com",
        display_name="User 1",
    )
    db_session.add(user1)
    await db_session.commit()

    service = UserAccountService(db_session)

    # Act & Assert - 別のOIDで同じメールは作成できない
    with pytest.raises(ValidationError):
        await service.get_or_create_by_azure_oid(
            azure_oid="user2-oid",  # 別のOID
            email="duplicate@company.com",  # 同じメール
            display_name="User 2",
        )


@pytest.mark.asyncio
async def test_update_last_login(db_session):
    """[test_user_account-005] 最終ログイン情報更新テスト。"""
    # Arrange
    user = UserAccount(
        azure_oid="login-oid",
        email="login@company.com",
        display_name="Login User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.last_login is None

    service = UserAccountService(db_session)

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
    """[test_user_account-006] 存在しないユーザーの最終ログイン更新エラーテスト。"""
    # Arrange
    service = UserAccountService(db_session)
    non_existent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_last_login(user_id=non_existent_id)
