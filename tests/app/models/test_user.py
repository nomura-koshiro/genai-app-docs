"""Azure AD認証用Userモデルのテスト。

このテストファイルは MODEL_TEST_POLICY.md に従い、
データ整合性に関わる制約テストのみを実施します。

基本的なCRUD操作はリポジトリ層・サービス層のテストでカバーされます。
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User


@pytest.mark.asyncio
async def test_user_unique_azure_oid(db_session):
    """Azure OIDの一意性制約のテスト。

    同じAzure OIDを持つユーザーを複数登録できないことを確認します。
    これはAzure AD認証の整合性に関わる重要な制約です。
    """
    # Arrange
    user1 = User(
        azure_oid="unique-oid-12345",
        email="user1@company.com",
        display_name="User 1",
    )
    db_session.add(user1)
    await db_session.commit()

    # Act & Assert - 同じAzure OIDで作成しようとするとエラー
    user2 = User(
        azure_oid="unique-oid-12345",  # 同じOID
        email="user2@company.com",
        display_name="User 2",
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_user_unique_email(db_session):
    """メールアドレスの一意性制約のテスト。

    同じメールアドレスを持つユーザーを複数登録できないことを確認します。
    これはユーザー識別の整合性に関わる重要な制約です。
    """
    # Arrange
    user1 = User(
        azure_oid="oid-12345",
        email="duplicate@company.com",
        display_name="User 1",
    )
    db_session.add(user1)
    await db_session.commit()

    # Act & Assert - 同じメールで作成しようとするとエラー
    user2 = User(
        azure_oid="oid-67890",
        email="duplicate@company.com",  # 同じメール
        display_name="User 2",
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
