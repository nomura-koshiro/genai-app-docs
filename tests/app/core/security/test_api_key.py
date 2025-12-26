"""APIキー生成のテスト。"""

import re

from app.core.security.api_key import generate_api_key


class TestApiKeyGeneration:
    """APIキー生成のテストクラス。"""

    def test_generate_api_key_success(self):
        """[test_api_key-001] APIキーの生成が成功すること。"""
        # Act
        api_key = generate_api_key()

        # Assert
        assert api_key is not None
        assert isinstance(api_key, str)
        assert len(api_key) > 0

    def test_generate_api_key_length(self):
        """[test_api_key-002] 生成されたAPIキーが適切な長さであること。"""
        # Act
        api_key = generate_api_key()

        # Assert
        # 32バイトのURL-safe base64エンコードは約43文字
        assert len(api_key) >= 40
        assert len(api_key) <= 50

    def test_generate_api_key_url_safe(self):
        """[test_api_key-003] 生成されたAPIキーがURL-safe文字のみで構成されていること。"""
        # Act
        api_key = generate_api_key()

        # Assert
        # URL-safe文字: A-Za-z0-9_-
        assert re.match(r"^[A-Za-z0-9_-]+$", api_key)

    def test_generate_api_key_uniqueness(self):
        """[test_api_key-004] 複数回生成したAPIキーがすべて異なること。"""
        # Act
        api_keys = [generate_api_key() for _ in range(100)]

        # Assert
        # すべて異なるAPIキーが生成されること
        assert len(api_keys) == len(set(api_keys))

    def test_generate_api_key_randomness(self):
        """[test_api_key-005] 生成されたAPIキーに十分なランダム性があること。"""
        # Act
        api_key1 = generate_api_key()
        api_key2 = generate_api_key()

        # Assert
        assert api_key1 != api_key2
        # 最初の10文字も異なるべき（高確率）
        assert api_key1[:10] != api_key2[:10]

    def test_generate_api_key_no_special_chars(self):
        """[test_api_key-006] 生成されたAPIキーに特殊文字（URL-unsafe）が含まれないこと。"""
        # Act
        api_keys = [generate_api_key() for _ in range(50)]

        # Assert
        for api_key in api_keys:
            # URL-unsafeな文字が含まれていないこと
            assert "/" not in api_key
            assert "+" not in api_key
            assert "=" not in api_key  # paddingもない
            assert " " not in api_key
            assert "!" not in api_key

    def test_generate_api_key_entropy(self):
        """[test_api_key-007] 生成されたAPIキーに十分なエントロピーがあること。"""
        # Act
        api_key = generate_api_key()

        # Assert
        # 異なる文字の種類をチェック
        unique_chars = len(set(api_key))
        # 32バイトのランダムデータなら、多様な文字が含まれるはず
        assert unique_chars >= 20  # 少なくとも20種類の文字

    def test_generate_api_key_no_predictable_pattern(self):
        """[test_api_key-008] 生成されたAPIキーに予測可能なパターンがないこと。"""
        # Act
        api_keys = [generate_api_key() for _ in range(10)]

        # Assert
        # すべて異なる開始文字（高確率）
        first_chars = [key[0] for key in api_keys]
        # 10個中、少なくとも7個は異なる開始文字のはず
        assert len(set(first_chars)) >= 7
