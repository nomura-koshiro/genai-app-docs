"""パスワードハッシュ化と検証のテスト。"""

from app.core.security.password import (
    hash_password,
    validate_password_strength,
    verify_password,
)


class TestPasswordHashing:
    """パスワードハッシュ化のテストクラス。"""

    def test_hash_password_success(self):
        """パスワードのハッシュ化が成功すること。"""
        # Arrange
        password = "SecurePass123!"

        # Act
        hashed = hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed.startswith("$2b$")  # bcrypt 2bバリアント
        assert len(hashed) >= 60  # bcryptハッシュの標準長

    def test_hash_password_different_salts(self):
        """同じパスワードでも毎回異なるハッシュが生成されること（salt）。"""
        # Arrange
        password = "SecurePass123!"

        # Act
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Assert
        assert hash1 != hash2  # saltが異なるため

    def test_hash_password_with_multibyte_characters(self):
        """マルチバイト文字（日本語）を含むパスワードのハッシュ化。"""
        # Arrange
        password = "パスワード123!Abc"

        # Act
        hashed = hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed.startswith("$2b$")

    def test_hash_password_long_password(self):
        """72バイトを超える長いパスワードのハッシュ化。"""
        # Arrange
        password = "A" * 100  # 100文字の長いパスワード

        # Act
        hashed = hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed.startswith("$2b$")


class TestPasswordVerification:
    """パスワード検証のテストクラス。"""

    def test_verify_password_success(self):
        """正しいパスワードの検証が成功すること。"""
        # Arrange
        password = "SecurePass123!"
        hashed = hash_password(password)

        # Act
        result = verify_password(password, hashed)

        # Assert
        assert result is True

    def test_verify_password_failure(self):
        """誤ったパスワードの検証が失敗すること。"""
        # Arrange
        correct_password = "SecurePass123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(correct_password)

        # Act
        result = verify_password(wrong_password, hashed)

        # Assert
        assert result is False

    def test_verify_password_case_sensitive(self):
        """パスワード検証が大文字小文字を区別すること。"""
        # Arrange
        password = "SecurePass123!"
        hashed = hash_password(password)

        # Act
        result = verify_password("securepass123!", hashed)

        # Assert
        assert result is False

    def test_verify_password_with_multibyte(self):
        """マルチバイト文字を含むパスワードの検証。"""
        # Arrange
        password = "パスワード123!Abc"
        hashed = hash_password(password)

        # Act
        result = verify_password(password, hashed)

        # Assert
        assert result is True


class TestPasswordStrengthValidation:
    """パスワード強度検証のテストクラス。"""

    def test_validate_strong_password(self):
        """強いパスワードの検証が成功すること。"""
        # Arrange
        password = "SecurePass123!"

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is True
        assert error == ""

    def test_validate_password_too_short(self):
        """8文字未満のパスワードが拒否されること。"""
        # Arrange
        password = "Pass1!"

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is False
        assert "8文字以上" in error

    def test_validate_password_no_uppercase(self):
        """大文字がないパスワードが拒否されること。"""
        # Arrange
        password = "password123!"

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is False
        assert "大文字" in error

    def test_validate_password_no_lowercase(self):
        """小文字がないパスワードが拒否されること。"""
        # Arrange
        password = "PASSWORD123!"

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is False
        assert "小文字" in error

    def test_validate_password_no_digit(self):
        """数字がないパスワードが拒否されること。"""
        # Arrange
        password = "SecurePass!"

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is False
        assert "数字" in error

    def test_validate_password_no_special_char(self):
        """特殊文字がなくても検証が成功すること（推奨だが必須ではない）。"""
        # Arrange
        password = "SecurePass123"

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is True  # 特殊文字は推奨だが必須ではない
        assert error == ""

    def test_validate_password_minimum_requirements(self):
        """最低要件を満たすパスワードの検証。"""
        # Arrange
        password = "Password1"  # 8文字、大文字、小文字、数字

        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is True
        assert error == ""
