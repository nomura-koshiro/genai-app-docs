"""APIキー生成のテスト。"""

import re

import pytest

from app.core.security.api_key import generate_api_key


class TestApiKeyGeneration:
    """APIキー生成のテストクラス。"""

    def test_generate_api_key_basic_properties(self):
        """[test_api_key-001] APIキーの基本プロパティが正しいこと。"""
        # Act
        api_key = generate_api_key()

        # Assert - 基本プロパティ
        assert api_key is not None
        assert isinstance(api_key, str)
        assert len(api_key) > 0

        # Assert - 長さ（32バイトのURL-safe base64は約43文字）
        assert 40 <= len(api_key) <= 50

        # Assert - URL-safe文字のみ
        assert re.match(r"^[A-Za-z0-9_-]+$", api_key)

    def test_generate_api_key_uniqueness(self):
        """[test_api_key-004] 複数回生成したAPIキーがすべて異なること。"""
        # Act
        api_keys = [generate_api_key() for _ in range(100)]

        # Assert
        assert len(api_keys) == len(set(api_keys))

    @pytest.mark.parametrize(
        "unsafe_char",
        ["/", "+", "=", " ", "!"],
        ids=["slash", "plus", "equals", "space", "exclamation"],
    )
    def test_generate_api_key_no_unsafe_chars(self, unsafe_char: str):
        """[test_api_key-006] URL-unsafe文字が含まれないこと。"""
        # Act
        api_keys = [generate_api_key() for _ in range(50)]

        # Assert
        for api_key in api_keys:
            assert unsafe_char not in api_key

    def test_generate_api_key_entropy(self):
        """[test_api_key-007] 生成されたAPIキーに十分なエントロピーがあること。"""
        # Act
        api_key = generate_api_key()

        # Assert - 異なる文字の種類をチェック
        unique_chars = len(set(api_key))
        # 32バイトのランダムデータなら、多様な文字が含まれるはず
        assert unique_chars >= 20

    def test_generate_api_key_no_predictable_pattern(self):
        """[test_api_key-008] 予測可能なパターンがないこと。"""
        # Act
        api_keys = [generate_api_key() for _ in range(10)]

        # Assert - すべて異なる開始文字（高確率）
        first_chars = [key[0] for key in api_keys]
        # 10個中、少なくとも7個は異なる開始文字のはず
        assert len(set(first_chars)) >= 7
