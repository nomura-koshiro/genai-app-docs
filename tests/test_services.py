"""サービス層のテスト。"""

import pytest

from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate
from app.services.user import UserService


@pytest.mark.asyncio
async def test_create_user_success(db_session, user_data):
    """ユーザー作成の成功ケース。"""
    # Arrange
    service = UserService(db_session)
    user_create = UserCreate(**user_data)

    # Act
    user = await service.create_user(user_create)
    await db_session.commit()

    # Assert
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.hashed_password != user_data["password"]  # ハッシュ化されている
    assert user.is_active is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session, user_data):
    """重複メールアドレスでのユーザー作成エラー。"""
    # Arrange
    service = UserService(db_session)
    user_create = UserCreate(**user_data)

    # 最初のユーザーを作成
    await service.create_user(user_create)
    await db_session.commit()

    # Act & Assert - 同じメールで再度作成しようとするとエラー
    with pytest.raises(ValidationError) as exc_info:
        await service.create_user(user_create)

    assert "already exists" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_create_user_duplicate_username(db_session, user_data):
    """重複ユーザー名でのユーザー作成エラー。"""
    # Arrange
    service = UserService(db_session)

    # 最初のユーザーを作成
    user_create1 = UserCreate(**user_data)
    await service.create_user(user_create1)
    await db_session.commit()

    # Act & Assert - 同じユーザー名、異なるメールで作成しようとするとエラー
    user_data2 = user_data.copy()
    user_data2["email"] = "different@example.com"
    user_create2 = UserCreate(**user_data2)

    with pytest.raises(ValidationError) as exc_info:
        await service.create_user(user_create2)

    assert "username" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session, user_data):
    """認証成功のテスト。"""
    # Arrange
    service = UserService(db_session)

    # ユーザーを作成
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password=hash_password(user_data["password"]),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    authenticated_user = await service.authenticate(
        user_data["email"], user_data["password"]
    )

    # Assert
    assert authenticated_user.id == user.id
    assert authenticated_user.email == user_data["email"]


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session, user_data):
    """間違ったパスワードでの認証失敗。"""
    # Arrange
    service = UserService(db_session)

    # ユーザーを作成
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password=hash_password(user_data["password"]),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(AuthenticationError):
        await service.authenticate(user_data["email"], "wrong_password")


@pytest.mark.asyncio
async def test_authenticate_user_not_found(db_session):
    """存在しないユーザーでの認証失敗。"""
    # Arrange
    service = UserService(db_session)

    # Act & Assert
    with pytest.raises(AuthenticationError):
        await service.authenticate("nonexistent@example.com", "password123")


@pytest.mark.asyncio
async def test_authenticate_inactive_user(db_session, user_data):
    """非アクティブユーザーでの認証失敗。"""
    # Arrange
    service = UserService(db_session)

    # 非アクティブユーザーを作成
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password=hash_password(user_data["password"]),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(AuthenticationError) as exc_info:
        await service.authenticate(user_data["email"], user_data["password"])

    assert "inactive" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_get_user_success(db_session, user_data):
    """ユーザー取得の成功ケース。"""
    # Arrange
    service = UserService(db_session)

    # ユーザーを作成
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act
    result = await service.get_user(user.id)

    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.email == user_data["email"]


@pytest.mark.asyncio
async def test_get_user_not_found(db_session):
    """存在しないユーザーの取得。"""
    # Arrange
    service = UserService(db_session)

    # Act
    result = await service.get_user(99999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_list_users(db_session):
    """ユーザー一覧取得のテスト。"""
    # Arrange
    service = UserService(db_session)

    # 複数のユーザーを作成
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password="hashed",
        )
        db_session.add(user)
    await db_session.commit()

    # Act
    users = await service.list_users(skip=0, limit=10)

    # Assert
    assert len(users) == 5
