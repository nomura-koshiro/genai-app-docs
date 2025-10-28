"""例外ハンドラーのテスト。

このテストは、グローバル例外ハンドラーが正しく登録され、
適切なレスポンスを返すことを確認します。
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.core import register_exception_handlers
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)


class TestExceptionHandlers:
    """例外ハンドラーのテストクラス。"""

    def test_register_exception_handlers(self):
        """例外ハンドラーが正しく登録されること。"""
        app = FastAPI()
        register_exception_handlers(app)

        # 例外ハンドラーが登録されている
        assert len(app.exception_handlers) > 0

    @pytest.mark.asyncio
    async def test_validation_error_handler(self):
        """ValidationErrorが400レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        # モックリクエスト
        request = Request({"type": "http", "method": "GET", "url": "/test"})

        # ValidationErrorを発生
        exc = ValidationError("Invalid input", details={"field": "email"})

        # ハンドラーを実行
        response = await app_exception_handler(request, exc)

        # レスポンスの検証
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422  # ValidationErrorは422 Unprocessable Entity

    @pytest.mark.asyncio
    async def test_authentication_error_handler(self):
        """AuthenticationErrorが401レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        request = Request({"type": "http", "method": "GET", "url": "/test"})
        exc = AuthenticationError("Unauthorized")

        response = await app_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authorization_error_handler(self):
        """AuthorizationErrorが403レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        request = Request({"type": "http", "method": "GET", "url": "/test"})
        exc = AuthorizationError("Forbidden")

        response = await app_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_error_handler(self):
        """NotFoundErrorが404レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        request = Request({"type": "http", "method": "GET", "url": "/test"})
        exc = NotFoundError("Resource not found")

        response = await app_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
