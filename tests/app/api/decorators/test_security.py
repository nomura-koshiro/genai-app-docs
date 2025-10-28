"""セキュリティデコレータのテスト。

このテストは、security.pyのセキュリティ関連デコレータを検証します。
データベース接続を必要としません。
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.decorators import handle_service_errors, validate_permissions
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)

# データベース不要のユニットテストとしてマーク
pytestmark = pytest.mark.skip_db


# セッションスコープのフィクスチャをオーバーライドしてデータベースセットアップをスキップ
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """デコレータテストではデータベースセットアップをスキップ。"""
    yield


class TestHandleServiceErrors:
    """handle_service_errorsデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_validation_error_conversion(self):
        """ValidationErrorが400エラーに変換されることをテスト。"""

        @handle_service_errors
        async def test_func():
            raise ValidationError("バリデーションエラー", details={"field": "email"})

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == 400
        assert "バリデーションエラー" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_authentication_error_conversion(self):
        """AuthenticationErrorが401エラーに変換されることをテスト。"""

        @handle_service_errors
        async def test_func():
            raise AuthenticationError("認証エラー")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authorization_error_conversion(self):
        """AuthorizationErrorが403エラーに変換されることをテスト。"""

        @handle_service_errors
        async def test_func():
            raise AuthorizationError("権限エラー")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_error_conversion(self):
        """NotFoundErrorが404エラーに変換されることをテスト。"""

        @handle_service_errors
        async def test_func():
            raise NotFoundError("リソースが見つかりません")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_generic_exception_conversion(self):
        """一般的な例外が500エラーに変換されることをテスト。"""

        @handle_service_errors
        async def test_func():
            raise ValueError("予期しないエラー")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == 500
        # detailを型安全に扱う
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert detail.get("error") == "Internal server error"

    @pytest.mark.asyncio
    async def test_http_exception_pass_through(self):
        """HTTPExceptionがそのまま再送出されることをテスト。"""

        @handle_service_errors
        async def test_func():
            raise HTTPException(status_code=418, detail="I'm a teapot")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == 418
        assert exc_info.value.detail == "I'm a teapot"

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """正常実行時にエラーハンドリングが介入しないことをテスト。"""

        @handle_service_errors
        async def test_func():
            return {"result": "success"}

        result = await test_func()
        assert result == {"result": "success"}


class TestValidatePermissions:
    """validate_permissionsデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_owner_access_granted(self):
        """リソースの所有者はアクセスが許可されることをテスト。"""
        # モックユーザー
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.is_superuser = False

        # モックリソース
        mock_resource = MagicMock()
        mock_resource.user_id = 123

        # モックサービス
        mock_service = AsyncMock()
        mock_service.get_file = AsyncMock(return_value=mock_resource)

        @validate_permissions("file", "delete")
        async def test_func(file_id: int, current_user, file_service):
            return "success"

        result = await test_func(
            file_id=1,
            current_user=mock_user,
            file_service=mock_service,
        )

        assert result == "success"
        assert mock_service.get_file.called

    @pytest.mark.asyncio
    async def test_non_owner_access_denied(self):
        """リソースの非所有者はアクセスが拒否されることをテスト。"""
        # モックユーザー
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.is_superuser = False

        # モックリソース（別のユーザーが所有）
        mock_resource = MagicMock()
        mock_resource.user_id = 456
        mock_resource.owner_id = None

        # モックサービス
        mock_service = AsyncMock()
        mock_service.get_file = AsyncMock(return_value=mock_resource)

        @validate_permissions("file", "delete")
        async def test_func(file_id: int, current_user, file_service):
            return "should not reach"

        with pytest.raises(AuthorizationError) as exc_info:
            await test_func(
                file_id=1,
                current_user=mock_user,
                file_service=mock_service,
            )

        assert "アクセス権限がありません" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_superuser_bypass(self):
        """スーパーユーザーは所有者でなくてもアクセスできることをテスト。"""
        # モックスーパーユーザー
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.is_superuser = True

        # モックリソース（別のユーザーが所有）
        mock_resource = MagicMock()
        mock_resource.user_id = 456
        mock_resource.owner_id = None

        # モックサービス
        mock_service = AsyncMock()
        mock_service.get_file = AsyncMock(return_value=mock_resource)

        @validate_permissions("file", "delete")
        async def test_func(file_id: int, current_user, file_service):
            return "superuser access"

        result = await test_func(
            file_id=1,
            current_user=mock_user,
            file_service=mock_service,
        )

        assert result == "superuser access"

    @pytest.mark.asyncio
    async def test_missing_current_user_raises_authentication_error(self):
        """current_userが存在しない場合、AuthenticationErrorが送出されることをテスト。"""

        @validate_permissions("file", "delete")
        async def test_func(file_id: int, file_service):
            return "should not reach"

        mock_service = AsyncMock()

        with pytest.raises(AuthenticationError) as exc_info:
            await test_func(file_id=1, file_service=mock_service)

        assert "認証が必要です" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_resource_not_found(self):
        """リソースが見つからない場合、NotFoundErrorが送出されることをテスト。"""
        # モックユーザー
        mock_user = MagicMock()
        mock_user.id = 123

        # モックサービス（リソースが見つからない）
        mock_service = AsyncMock()
        mock_service.get_file = AsyncMock(side_effect=NotFoundError("ファイルが見つかりません"))

        @validate_permissions("file", "delete")
        async def test_func(file_id: int, current_user, file_service):
            return "should not reach"

        with pytest.raises(NotFoundError, match="ファイルが見つかりません"):
            await test_func(
                file_id=999,
                current_user=mock_user,
                file_service=mock_service,
            )

    @pytest.mark.asyncio
    async def test_custom_resource_id_getter(self):
        """カスタムリソースID取得関数が正しく動作することをテスト。"""
        # モックユーザー
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.is_superuser = False

        # モックリソース（user_idなし、owner_idあり）
        mock_resource = MagicMock()
        mock_resource.user_id = None
        mock_resource.owner_id = 123

        # モックサービス
        mock_service = AsyncMock()
        mock_service.get_session = AsyncMock(return_value=mock_resource)

        def custom_getter(kwargs: dict[str, Any]) -> str | int:
            result = kwargs.get("session_identifier")
            if result is None:
                raise ValueError("session_identifier not found")
            return str(result)

        @validate_permissions("session", "update", get_resource_id=custom_getter)
        async def test_func(session_identifier: str, current_user, session_service):
            return "success"

        result = await test_func(
            session_identifier="custom-id-123",
            current_user=mock_user,
            session_service=mock_service,
        )

        assert result == "success"
        mock_service.get_session.assert_called_once_with("custom-id-123")

    @pytest.mark.asyncio
    async def test_owner_id_fallback(self):
        """user_id属性がない場合、owner_idが使用されることをテスト。"""
        # モックユーザー
        mock_user = MagicMock()
        mock_user.id = 789
        mock_user.is_superuser = False

        # モックリソース（user_idなし、owner_idあり）
        mock_resource = MagicMock()
        mock_resource.user_id = None
        mock_resource.owner_id = 789

        # モックサービス
        mock_service = AsyncMock()
        mock_service.get_session = AsyncMock(return_value=mock_resource)

        @validate_permissions("session", "read")
        async def test_func(session_id: int, current_user, session_service):
            return "success"

        result = await test_func(
            session_id=1,
            current_user=mock_user,
            session_service=mock_service,
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_audit_log_on_access(self):
        """アクセス時に監査ログが記録されることをテスト。"""
        # モックユーザー
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.email = "test@example.com"
        mock_user.is_superuser = False

        # モックリソース
        mock_resource = MagicMock()
        mock_resource.user_id = 123

        # モックサービス
        mock_service = AsyncMock()
        mock_service.get_file = AsyncMock(return_value=mock_resource)

        @validate_permissions("file", "delete")
        async def test_func(file_id: int, current_user, file_service):
            return "success"

        with patch("app.api.decorators.security.logger") as mock_logger:
            await test_func(
                file_id=1,
                current_user=mock_user,
                file_service=mock_service,
            )

            # 監査ログが記録されている
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "permission_validated"
            assert call_args[1]["user_id"] == 123
            assert call_args[1]["resource_type"] == "file"
            assert call_args[1]["action"] == "delete"
