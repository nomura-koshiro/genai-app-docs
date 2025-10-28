"""JWT認証のテスト。"""

from datetime import timedelta

from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


class TestAccessToken:
    """JWTアクセストークンのテストクラス。"""

    def test_create_access_token_success(self):
        """アクセストークンの生成が成功すること。"""
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
        """カスタム有効期限でトークンを生成できること。"""
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
        """追加のクレームを含むトークンを生成できること。"""
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
        """有効なトークンのデコードが成功すること。"""
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

    def test_decode_access_token_invalid_signature(self):
        """署名が不正なトークンのデコードが失敗すること。"""
        # Arrange
        # 正しいトークンを生成して、最後の文字を変更（署名を破壊）
        token = create_access_token({"sub": "1"})
        invalid_token = token[:-1] + ("A" if token[-1] != "A" else "B")

        # Act
        payload = decode_access_token(invalid_token)

        # Assert
        assert payload is None

    def test_decode_access_token_expired(self):
        """有効期限切れトークンのデコードが失敗すること。"""
        # Arrange
        data = {"sub": "1"}
        # 有効期限を過去に設定（-1秒）
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Act
        payload = decode_access_token(token)

        # Assert
        assert payload is None

    def test_decode_access_token_malformed(self):
        """不正な形式のトークンのデコードが失敗すること。"""
        # Arrange
        invalid_token = "not.a.valid.jwt.token"

        # Act
        payload = decode_access_token(invalid_token)

        # Assert
        assert payload is None

    def test_decode_access_token_missing_sub(self):
        """subフィールドがないトークンのデコードが失敗すること。"""
        # Arrange
        # subフィールドなしでトークン生成は可能だが、デコード時に検証される
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
        """リフレッシュトークンの生成が成功すること。"""
        # Arrange
        data = {"sub": "1"}

        # Act
        token = create_refresh_token(data)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token_success(self):
        """有効なリフレッシュトークンのデコードが成功すること。"""
        # Arrange
        data = {"sub": "1"}
        token = create_refresh_token(data)

        # Act
        payload = decode_refresh_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_decode_refresh_token_wrong_type(self):
        """アクセストークンをリフレッシュトークンとしてデコードすると失敗すること。"""
        # Arrange
        token = create_access_token({"sub": "1"})

        # Act
        payload = decode_refresh_token(token)

        # Assert
        assert payload is None  # typeが"access"なので失敗

    def test_decode_refresh_token_invalid(self):
        """不正なリフレッシュトークンのデコードが失敗すること。"""
        # Arrange
        invalid_token = "invalid.refresh.token"

        # Act
        payload = decode_refresh_token(invalid_token)

        # Assert
        assert payload is None

    def test_refresh_token_longer_expiration(self):
        """リフレッシュトークンの有効期限がアクセストークンより長いこと。"""
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
