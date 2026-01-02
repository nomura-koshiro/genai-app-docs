"""JWT認証のテスト。"""

from datetime import timedelta

import pytest

from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


class TestAccessToken:
    """JWTアクセストークンのテストクラス。"""

    def test_create_access_token_success(self):
        """[test_jwt-001] アクセストークンの生成が成功すること。"""
        # Arrange
        data = {"sub": "1"}

        # Act
        token = create_access_token(data)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT形式: header.payload.signature
        assert token.count(".") == 2

    def test_create_access_token_with_custom_expiration(self):
        """[test_jwt-002] カスタム有効期限でトークンを生成できること。"""
        # Arrange
        data = {"sub": "1"}
        expires_delta = timedelta(hours=1)

        # Act
        token = create_access_token(data, expires_delta=expires_delta)

        # Assert
        assert token is not None
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"

    def test_create_access_token_with_additional_claims(self):
        """[test_jwt-003] 追加のクレームを含むトークンを生成できること。"""
        # Arrange
        data = {"sub": "1", "role": "admin", "username": "testuser"}

        # Act
        token = create_access_token(data)

        # Assert
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["role"] == "admin"
        assert payload["username"] == "testuser"

    def test_decode_access_token_success(self):
        """[test_jwt-004] 有効なトークンのデコードが成功すること。"""
        # Arrange
        data = {"sub": "123"}
        token = create_access_token(data)

        # Act
        payload = decode_access_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == "123"
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"

    @pytest.mark.parametrize(
        "token_generator,description",
        [
            (
                lambda: (
                    lambda t=create_access_token({"sub": "1"}): f"{t.split('.')[0]}.{t.split('.')[1]}.invalid_sig"
                )(),
                "invalid_signature",
            ),
            (
                lambda: create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1)),
                "expired",
            ),
            (
                lambda: "not.a.valid.jwt.token",
                "malformed",
            ),
        ],
        ids=["invalid_signature", "expired", "malformed"],
    )
    def test_decode_access_token_failure(self, token_generator, description: str):
        """[test_jwt-005] 無効なトークンのデコードが失敗すること。"""
        # Arrange
        invalid_token = token_generator()

        # Act
        payload = decode_access_token(invalid_token)

        # Assert
        assert payload is None

    def test_decode_access_token_missing_sub(self):
        """[test_jwt-008] subフィールドがないトークンのデコードが失敗すること。"""
        # Arrange
        from datetime import UTC, datetime

        from jose import jwt

        from app.core.config import settings

        payload = {
            "exp": datetime.now(UTC) + timedelta(minutes=30),
            "iat": datetime.now(UTC),
            "type": "access",
            # "sub" フィールドなし
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # Act
        result = decode_access_token(token)

        # Assert
        assert result is None


class TestRefreshToken:
    """JWTリフレッシュトークンのテストクラス。"""

    def test_create_refresh_token_success(self):
        """[test_jwt-009] リフレッシュトークンの生成が成功すること。"""
        # Arrange
        data = {"sub": "1"}

        # Act
        token = create_refresh_token(data)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token_success(self):
        """[test_jwt-010] 有効なリフレッシュトークンのデコードが成功すること。"""
        # Arrange
        data = {"sub": "1"}
        token = create_refresh_token(data)

        # Act
        payload = decode_refresh_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    @pytest.mark.parametrize(
        "token_type,description",
        [
            ("wrong_type", "wrong_type"),
            ("invalid", "invalid"),
        ],
        ids=["wrong_type", "invalid"],
    )
    def test_decode_refresh_token_errors(self, token_type: str, description: str):
        """[test_jwt-011/012] リフレッシュトークンのデコード失敗ケース。"""
        # Arrange
        if token_type == "wrong_type":
            token = create_access_token({"sub": "1"})
        else:  # invalid
            token = "invalid.refresh.token"

        # Act
        payload = decode_refresh_token(token)

        # Assert
        assert payload is None

    def test_refresh_token_longer_expiration(self):
        """[test_jwt-013] リフレッシュトークンの有効期限がアクセストークンより長いこと。"""
        # Arrange
        data = {"sub": "1"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        # Act
        access_payload = decode_access_token(access_token)
        refresh_payload = decode_refresh_token(refresh_token)

        # Assert
        assert access_payload is not None
        assert refresh_payload is not None
        # リフレッシュトークンの有効期限がアクセストークンより長い
        assert refresh_payload["exp"] > access_payload["exp"]
