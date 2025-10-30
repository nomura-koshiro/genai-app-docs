"""RFC 9457準拠の例外ハンドラーのテスト。

このテストは、グローバル例外ハンドラーが正しく登録され、
RFC 9457 Problem Details for HTTP APIs標準に準拠したレスポンスを返すことを確認します。

Reference:
    RFC 9457: https://www.rfc-editor.org/rfc/rfc9457.html
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
    """RFC 9457準拠の例外ハンドラーのテストクラス。"""

    def test_register_exception_handlers(self):
        """例外ハンドラーが正しく登録されること。"""
        app = FastAPI()
        register_exception_handlers(app)

        # 例外ハンドラーが登録されている
        assert len(app.exception_handlers) > 0

    @pytest.mark.asyncio
    async def test_validation_error_handler(self):
        """ValidationErrorがRFC 9457準拠の422レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        # モックリクエスト
        request = Request({
            "type": "http",
            "method": "GET",
            "url": "http://testserver/test",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        })

        # ValidationErrorを発生
        exc = ValidationError("Invalid input", details={"field": "email"})

        # ハンドラーを実行
        response = await app_exception_handler(request, exc)

        # レスポンスの検証
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422  # ValidationErrorは422 Unprocessable Entity
        assert response.media_type == "application/problem+json"  # RFC 9457準拠のContent-Type

        # レスポンスボディの検証（RFC 9457準拠）
        body = response.body.decode()
        import json
        data = json.loads(body)
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data
        assert data["status"] == 422
        assert data["title"] == "Unprocessable Entity"
        assert data["detail"] == "Invalid input"
        assert data["field"] == "email"  # カスタムフィールド

    @pytest.mark.asyncio
    async def test_authentication_error_handler(self):
        """AuthenticationErrorがRFC 9457準拠の401レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        request = Request({
            "type": "http",
            "method": "GET",
            "url": "http://testserver/test",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        })
        exc = AuthenticationError("Unauthorized")

        response = await app_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        assert response.media_type == "application/problem+json"

        body = response.body.decode()
        import json
        data = json.loads(body)
        assert data["status"] == 401
        assert data["title"] == "Unauthorized"
        assert data["detail"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_authorization_error_handler(self):
        """AuthorizationErrorがRFC 9457準拠の403レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        request = Request({
            "type": "http",
            "method": "GET",
            "url": "http://testserver/test",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        })
        exc = AuthorizationError("Forbidden")

        response = await app_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        assert response.media_type == "application/problem+json"

        body = response.body.decode()
        import json
        data = json.loads(body)
        assert data["status"] == 403
        assert data["title"] == "Forbidden"
        assert data["detail"] == "Forbidden"

    @pytest.mark.asyncio
    async def test_not_found_error_handler(self):
        """NotFoundErrorがRFC 9457準拠の404レスポンスになること。"""
        from app.api.core.exception_handlers import app_exception_handler

        request = Request({
            "type": "http",
            "method": "GET",
            "url": "http://testserver/test",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        })
        exc = NotFoundError("Resource not found")

        response = await app_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        assert response.media_type == "application/problem+json"

        body = response.body.decode()
        import json
        data = json.loads(body)
        assert data["status"] == 404
        assert data["title"] == "Not Found"
        assert data["detail"] == "Resource not found"
