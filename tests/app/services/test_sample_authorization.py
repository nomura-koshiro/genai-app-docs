"""認可サービスのテスト。"""

import pytest

from app.core.exceptions import AuthorizationError
from app.models.sample_user import SampleUser
from app.services.sample_authorization import SampleAuthorizationService


class TestSampleAuthorizationService:
    """SampleAuthorizationServiceのテストクラス。"""

    def test_check_admin_access_with_superuser(self):
        """スーパーユーザーのアクセスが許可されること。"""
        # Arrange
        superuser = SampleUser(
            id=1,
            email="admin@example.com",
            username="admin",
            hashed_password="hashed",
            is_superuser=True,
            is_active=True,
        )

        # Act & Assert - 例外が発生しないこと
        try:
            SampleAuthorizationService.check_admin_access(superuser)
        except AuthorizationError:
            pytest.fail("スーパーユーザーのアクセスが拒否されました")

    def test_check_admin_access_with_regular_user(self):
        """一般ユーザーのアクセスが拒否されること。"""
        # Arrange
        regular_user = SampleUser(
            id=2,
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            is_superuser=False,
            is_active=True,
        )

        # Act & Assert
        with pytest.raises(AuthorizationError) as exc_info:
            SampleAuthorizationService.check_admin_access(regular_user)

        # エラーメッセージの検証
        assert "管理者権限が必要です" in str(exc_info.value)

    def test_check_admin_access_with_inactive_superuser(self):
        """非アクティブなスーパーユーザーでもチェックはパスすること。"""
        # Arrange - このメソッドはis_activeをチェックしない（認証層で処理済み想定）
        inactive_superuser = SampleUser(
            id=3,
            email="inactive_admin@example.com",
            username="inactive_admin",
            hashed_password="hashed",
            is_superuser=True,
            is_active=False,
        )

        # Act & Assert - is_superuser=Trueなので例外は発生しない
        try:
            SampleAuthorizationService.check_admin_access(inactive_superuser)
        except AuthorizationError:
            pytest.fail("スーパーユーザー（非アクティブ）のアクセスが拒否されました")

    def test_check_admin_access_static_method(self):
        """静的メソッドとして呼び出せること。"""
        # Arrange
        superuser = SampleUser(
            id=4,
            email="static@example.com",
            username="static_admin",
            hashed_password="hashed",
            is_superuser=True,
            is_active=True,
        )

        # Act & Assert - クラスから直接呼び出し
        try:
            SampleAuthorizationService.check_admin_access(superuser)
        except AuthorizationError:
            pytest.fail("静的メソッド呼び出しでエラーが発生しました")

    def test_check_admin_access_instance_method(self):
        """インスタンスメソッドとしても呼び出せること。"""
        # Arrange
        superuser = SampleUser(
            id=5,
            email="instance@example.com",
            username="instance_admin",
            hashed_password="hashed",
            is_superuser=True,
            is_active=True,
        )
        auth_service = SampleAuthorizationService()

        # Act & Assert - インスタンスから呼び出し
        try:
            auth_service.check_admin_access(superuser)
        except AuthorizationError:
            pytest.fail("インスタンスメソッド呼び出しでエラーが発生しました")

    def test_check_admin_access_error_contains_user_id(self):
        """認可エラーにuser_idが含まれていること。"""
        # Arrange
        regular_user = SampleUser(
            id=99,
            email="details@example.com",
            username="details_user",
            hashed_password="hashed",
            is_superuser=False,
            is_active=True,
        )

        # Act & Assert
        with pytest.raises(AuthorizationError) as exc_info:
            SampleAuthorizationService.check_admin_access(regular_user)

        # detailsにuser_idが含まれていることを確認
        error = exc_info.value
        assert hasattr(error, "details")
        assert error.details.get("user_id") == 99
