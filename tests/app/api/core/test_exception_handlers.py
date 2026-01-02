"""RFC 9457準拠の例外ハンドラーのテスト。

このテストは、グローバル例外ハンドラーが正しく登録され、
RFC 9457 Problem Details for HTTP APIs標準に準拠したレスポンスを返すことを確認します。

Reference:
    RFC 9457: https://www.rfc-editor.org/rfc/rfc9457.html
"""

import json

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

    def test_exception_handlers_register_successfully(self):
        """[test_exception_handlers-001] 例外ハンドラーが正しく登録されること。"""
        # Arrange
        app = FastAPI()

        # Act
        register_exception_handlers(app)

        # Assert
        assert len(app.exception_handlers) > 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception_class,message,expected_status,expected_title,details",
        [
            (ValidationError, "Invalid input", 422, "Unprocessable Entity", {"field": "email"}),
            (AuthenticationError, "Unauthorized", 401, "Unauthorized", None),
            (AuthorizationError, "Forbidden", 403, "Forbidden", None),
            (NotFoundError, "Resource not found", 404, "Not Found", None),
        ],
        ids=["validation_422", "authentication_401", "authorization_403", "not_found_404"],
    )
    async def test_exception_returns_rfc9457_response(
        self,
        exception_class: type,
        message: str,
        expected_status: int,
        expected_title: str,
        details: dict | None,
    ):
        """[test_exception_handlers-002] 各例外がRFC 9457準拠のレスポンスになること。"""
        # Arrange
        from app.api.core.exception_handlers import app_exception_handler

        request = Request(
            {
                "type": "http",
                "method": "GET",
                "url": "http://testserver/test",
                "path": "/test",
                "headers": [],
                "query_string": b"",
            }
        )
        exc = exception_class(message, details=details) if details else exception_class(message)

        # Act
        response = await app_exception_handler(request, exc)

        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == expected_status
        assert response.media_type == "application/problem+json"  # RFC 9457準拠

        body = bytes(response.body).decode()
        data = json.loads(body)

        # RFC 9457必須フィールド
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data

        assert data["status"] == expected_status
        assert data["title"] == expected_title
        assert data["detail"] == message

        # カスタムフィールドの検証
        if details:
            for key, value in details.items():
                assert data[key] == value
