"""リポジトリ層のテスト。"""

import pytest

from app.models import SampleUser
from app.repositories.sample_user import SampleUserRepository


@pytest.mark.asyncio
async def test_repository_get(db_session, user_data):
    """リポジトリのget操作のテスト。"""
    # Arrange
    user = SampleUser(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repository = SampleUserRepository(db_session)

    # Act
    result = await repository.get(user.id)

    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.email == user_data["email"]


@pytest.mark.asyncio
async def test_repository_get_not_found(db_session):
    """存在しないIDのget操作のテスト。"""
    # Arrange
    repository = SampleUserRepository(db_session)

    # Act
    result = await repository.get(99999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_repository_create(db_session, user_data):
    """リポジトリのcreate操作のテスト。"""
    # Arrange
    repository = SampleUserRepository(db_session)

    # Act
    user = await repository.create(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed_password",
    )
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]


@pytest.mark.asyncio
async def test_repository_get_multi(db_session):
    """リポジトリのget_multi操作のテスト。"""
    # Arrange
    repository = SampleUserRepository(db_session)

    # 複数のユーザーを作成
    for i in range(5):
        user = SampleUser(
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password="hashed",
        )
        db_session.add(user)
    await db_session.commit()

    # Act
    users = await repository.get_multi(skip=0, limit=10)

    # Assert
    assert len(users) == 5


@pytest.mark.asyncio
async def test_repository_get_multi_pagination(db_session):
    """リポジトリのページネーションのテスト。"""
    # Arrange
    repository = SampleUserRepository(db_session)

    # 10人のユーザーを作成
    for i in range(10):
        user = SampleUser(
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password="hashed",
        )
        db_session.add(user)
    await db_session.commit()

    # Act
    first_page = await repository.get_multi(skip=0, limit=5)
    second_page = await repository.get_multi(skip=5, limit=5)

    # Assert
    assert len(first_page) == 5
    assert len(second_page) == 5
    assert first_page[0].id != second_page[0].id


@pytest.mark.asyncio
async def test_repository_update(db_session, user_data):
    """リポジトリのupdate操作のテスト。"""
    # Arrange
    user = SampleUser(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repository = SampleUserRepository(db_session)

    # Act
    updated_user = await repository.update(user, is_active=False)
    await db_session.commit()
    await db_session.refresh(updated_user)

    # Assert
    assert updated_user.is_active is False
    assert updated_user.id == user.id


@pytest.mark.asyncio
async def test_repository_delete(db_session, user_data):
    """リポジトリのdelete操作のテスト。"""
    # Arrange
    user = SampleUser(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repository = SampleUserRepository(db_session)
    user_id = user.id

    # Act
    result = await repository.delete(user.id)
    await db_session.commit()

    # Assert
    assert result is True
    deleted_user = await repository.get(user_id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_repository_get_by_email(db_session, user_data):
    """SampleUserRepositoryのget_by_emailのテスト。"""
    # Arrange
    user = SampleUser(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

    repository = SampleUserRepository(db_session)

    # Act
    result = await repository.get_by_email(user_data["email"])

    # Assert
    assert result is not None
    assert result.email == user_data["email"]


@pytest.mark.asyncio
async def test_repository_get_by_username(db_session, user_data):
    """SampleUserRepositoryのget_by_usernameのテスト。"""
    # Arrange
    user = SampleUser(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

    repository = SampleUserRepository(db_session)

    # Act
    result = await repository.get_by_username(user_data["username"])

    # Assert
    assert result is not None
    assert result.username == user_data["username"]
