"""ユーザーサービスの拡張テスト（アカウントロック、IP記録等）。"""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import hash_password
from app.models import SampleUser
from app.services.sample_user import SampleUserService


@pytest.mark.asyncio
async def test_account_lock_after_max_failed_attempts(db_session):
    """最大ログイン失敗回数後にアカウントがロックされることを確認。"""
    # Arrange
    service = SampleUserService(db_session)
    correct_password = "SecurePass123!"

    user = SampleUser(
        email="locktest@example.com",
        username="locktest",
        hashed_password=hash_password(correct_password),
        is_active=True,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()

    # Act - MAX_LOGIN_ATTEMPTS回失敗させる
    for i in range(settings.MAX_LOGIN_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            await service.authenticate("locktest@example.com", "wrong_password")

    # Refresh to get updated state
    await db_session.refresh(user)

    # Assert - アカウントがロックされている
    assert user.failed_login_attempts == settings.MAX_LOGIN_ATTEMPTS
    assert user.locked_until is not None
    assert user.locked_until > datetime.now(UTC)

    # さらなる認証試行もエラーになる
    with pytest.raises(AuthenticationError) as exc_info:
        await service.authenticate("locktest@example.com", correct_password)

    # ロックメッセージを確認
    assert "ロック" in exc_info.value.message or "lock" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_failed_login_attempts_reset_on_success(db_session):
    """認証成功時に失敗回数がリセットされることを確認。"""
    # Arrange
    service = SampleUserService(db_session)
    correct_password = "SecurePass123!"

    user = SampleUser(
        email="reset@example.com",
        username="resettest",
        hashed_password=hash_password(correct_password),
        is_active=True,
        failed_login_attempts=3,  # 既に3回失敗している
    )
    db_session.add(user)
    await db_session.commit()

    # Act - 正しいパスワードで認証
    authenticated = await service.authenticate("reset@example.com", correct_password)

    # Assert
    assert authenticated.failed_login_attempts == 0
    assert authenticated.locked_until is None


@pytest.mark.asyncio
async def test_last_login_tracking(db_session):
    """最終ログイン日時とIPアドレスが記録されることを確認。"""
    # Arrange
    service = SampleUserService(db_session)
    password = "SecurePass123!"
    client_ip = "192.168.1.100"

    user = SampleUser(
        email="login@example.com",
        username="logintest",
        hashed_password=hash_password(password),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    before_login = datetime.now(UTC)

    # Act
    authenticated = await service.authenticate("login@example.com", password, client_ip=client_ip)

    # Assert
    assert authenticated.last_login_at is not None
    assert authenticated.last_login_at >= before_login
    assert authenticated.last_login_ip == client_ip


@pytest.mark.asyncio
async def test_authenticate_locked_account_before_unlock_time(db_session):
    """ロック時間前の認証がエラーになることを確認。"""
    # Arrange
    service = SampleUserService(db_session)
    password = "SecurePass123!"

    # 1時間後までロックされているユーザー
    locked_until = datetime.now(UTC) + timedelta(hours=1)

    user = SampleUser(
        email="locked@example.com",
        username="lockeduser",
        hashed_password=hash_password(password),
        is_active=True,
        failed_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
        locked_until=locked_until,
    )
    db_session.add(user)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(AuthenticationError) as exc_info:
        await service.authenticate("locked@example.com", password)

    assert "ロック" in exc_info.value.message or "lock" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_password_increments_failed_attempts(db_session):
    """パスワード失敗時に失敗回数がインクリメントされることを確認。"""
    # Arrange
    service = SampleUserService(db_session)
    correct_password = "SecurePass123!"

    user = SampleUser(
        email="increment@example.com",
        username="incrementtest",
        hashed_password=hash_password(correct_password),
        is_active=True,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()

    # Act - 2回失敗させる
    for i in range(2):
        with pytest.raises(AuthenticationError):
            await service.authenticate("increment@example.com", "wrong_password")

    # Refresh
    await db_session.refresh(user)

    # Assert
    assert user.failed_login_attempts == 2


@pytest.mark.asyncio
async def test_get_user_by_email_success(db_session):
    """メールアドレスでのユーザー取得が成功することを確認。"""
    # Arrange
    service = SampleUserService(db_session)

    user = SampleUser(
        email="byemail@example.com",
        username="byemailtest",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    result = await service.get_user_by_email("byemail@example.com")

    # Assert
    assert result is not None
    assert result.email == "byemail@example.com"


@pytest.mark.asyncio
async def test_list_users_with_pagination(db_session):
    """ページネーションが正しく機能することを確認。"""
    # Arrange
    service = SampleUserService(db_session)

    # 10人のユーザーを作成
    for i in range(10):
        user = SampleUser(
            email=f"page{i}@example.com",
            username=f"page{i}",
            hashed_password="hashed",
        )
        db_session.add(user)
    await db_session.commit()

    # Act - 最初の5件を取得
    page1 = await service.list_users(skip=0, limit=5)

    # 次の5件を取得
    page2 = await service.list_users(skip=5, limit=5)

    # Assert
    assert len(page1) == 5
    assert len(page2) == 5

    # 異なるユーザーが返されることを確認
    page1_emails = {u.email for u in page1}
    page2_emails = {u.email for u in page2}
    assert len(page1_emails & page2_emails) == 0  # 重複なし
