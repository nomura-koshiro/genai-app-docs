"""パスワードハッシュ化と検証のテスト。"""

import pytest

from app.core.security.password import (
    hash_password,
    validate_password_strength,
    verify_password,
)


class TestPasswordHashing:
    """パスワードハッシュ化のテストクラス。"""

    @pytest.mark.parametrize(
        "password",
        [
            "SecurePass123!",
            "パスワード123!Abc",
            "A" * 100,  # 72バイトを超える長いパスワード
        ],
        ids=["normal", "multibyte", "long_password"],
    )
    def test_hash_password_success(self, password: str):
        """[test_password-001] 各種パスワードのハッシュ化が成功すること。"""
        # Act
        hashed = hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed.startswith("$2b$")  # bcrypt 2bバリアント
        assert len(hashed) >= 60  # bcryptハッシュの標準長

    def test_hash_password_different_salts(self):
        """[test_password-002] 同じパスワードでも毎回異なるハッシュが生成されること（salt）。"""
        # Arrange
        password = "SecurePass123!"

        # Act
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Assert
        assert hash1 != hash2  # saltが異なるため


class TestPasswordVerification:
    """パスワード検証のテストクラス。"""

    @pytest.mark.parametrize(
        "password",
        [
            "SecurePass123!",
            "パスワード123!Abc",
        ],
        ids=["normal", "multibyte"],
    )
    def test_verify_password_success(self, password: str):
        """[test_password-005] 正しいパスワードの検証が成功すること。"""
        # Arrange
        hashed = hash_password(password)

        # Act
        result = verify_password(password, hashed)

        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "correct_password,wrong_password",
        [
            ("SecurePass123!", "WrongPassword456!"),
            ("SecurePass123!", "securepass123!"),  # 大文字小文字違い
        ],
        ids=["different_password", "case_sensitive"],
    )
    def test_verify_password_failure(self, correct_password: str, wrong_password: str):
        """[test_password-006] 誤ったパスワードの検証が失敗すること。"""
        # Arrange
        hashed = hash_password(correct_password)

        # Act
        result = verify_password(wrong_password, hashed)

        # Assert
        assert result is False


class TestPasswordStrengthValidation:
    """パスワード強度検証のテストクラス。"""

    @pytest.mark.parametrize(
        "password",
        [
            "SecurePass123!",
            "SecurePass123",  # 特殊文字なし（推奨だが必須ではない）
            "Password1",  # 最低要件
        ],
        ids=["strong", "no_special_char", "minimum_requirements"],
    )
    def test_validate_strong_password(self, password: str):
        """[test_password-009] 強いパスワードの検証が成功すること。"""
        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is True
        assert error == ""

    @pytest.mark.parametrize(
        "password,expected_error",
        [
            ("Pass1!", "8文字以上"),  # 短すぎる
            ("password123!", "大文字"),  # 大文字なし
            ("PASSWORD123!", "小文字"),  # 小文字なし
            ("SecurePass!", "数字"),  # 数字なし
        ],
        ids=["too_short", "no_uppercase", "no_lowercase", "no_digit"],
    )
    def test_validate_weak_password(self, password: str, expected_error: str):
        """[test_password-010] 弱いパスワードが拒否されること。"""
        # Act
        is_valid, error = validate_password_strength(password)

        # Assert
        assert is_valid is False
        assert expected_error in error
