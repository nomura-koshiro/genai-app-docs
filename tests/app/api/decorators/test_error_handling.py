"""エラーハンドリングデコレータのテスト。

このテストは、error_handling.pyのエラーハンドリングデコレータを検証します。
データベース接続を必要としません。

Note:
    権限検証（認可）のテストは tests/app/api/core/dependencies/test_authorization.py
    で提供されています。
"""

import pytest
from fastapi import HTTPException

from app.api.decorators import handle_service_errors
from app.core.exceptions import (
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
    async def test_custom_error_conversion(self):
        """[test_error_handling-001] カスタムエラーがログ出力後に再送出されることをテスト。"""
        # Arrange
        @handle_service_errors
        async def test_func():
            raise ValidationError("Validation error", details={"field": "email"})

        # Act
        # デコレータはエラーをそのまま再送出する（グローバルハンドラーで処理）
        with pytest.raises(ValidationError) as exc_info:
            await test_func()

        # Assert
        assert exc_info.value.message == "Validation error"
        assert exc_info.value.details == {"field": "email"}

    @pytest.mark.asyncio
    async def test_http_exception_pass_through(self):
        """[test_error_handling-002] HTTPExceptionがそのまま再送出されることをテスト。"""
        # Arrange
        @handle_service_errors
        async def test_func():
            raise HTTPException(status_code=418, detail="I'm a teapot")

        # Act
        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        # Assert
        assert exc_info.value.status_code == 418
        assert exc_info.value.detail == "I'm a teapot"

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """[test_error_handling-003] 正常実行時にエラーハンドリングが介入しないことをテスト。"""
        # Arrange
        @handle_service_errors
        async def test_func():
            return {"result": "success"}

        # Act
        result = await test_func()

        # Assert
        assert result == {"result": "success"}
