"""sensitive_data モジュールのテスト。

機密情報のフィールド判定とマスク処理をテストします。

テストID命名規則:
- test_sensitive_data-001: is_sensitive_field 基本テスト
- test_sensitive_data-002: is_sensitive_field パターンマッチテスト
- test_sensitive_data-003: is_sensitive_field 誤検出防止テスト
- test_sensitive_data-010: mask_sensitive_data 基本テスト
- test_sensitive_data-011: mask_sensitive_data ネストテスト
- test_sensitive_data-012: mask_sensitive_data リストテスト
- test_sensitive_data-013: mask_sensitive_data 深度制限テスト
"""

import pytest

from app.utils.sensitive_data import (
    SENSITIVE_KEYS,
    SENSITIVE_PATTERNS,
    is_sensitive_field,
    mask_sensitive_data,
)


class TestIsSensitiveField:
    """is_sensitive_field関数のテスト。"""

    # ==========================================================================
    # 完全一致テスト
    # ==========================================================================

    @pytest.mark.parametrize(
        "field_name",
        [
            "password",
            "password_hash",
            "token",
            "secret",
            "api_key",
            "apikey",
            "credential",
            "authorization",
            "access_token",
            "refresh_token",
            "session_token",
            "bearer",
            "jwt",
            "csrf_token",
            "csrf",
            "xsrf_token",
            "client_secret",
            "client_id",
            "azure_client_secret",
            "connection_string",
            "sas_token",
            "shared_access_signature",
            "account_key",
            "storage_account_key",
            "private_key",
            "secret_key",
            "encryption_key",
            "signing_key",
            "master_key",
            "ssn",
            "credit_card",
            "card_number",
            "cvv",
            "cvc",
            "bank_account",
            "pin",
            "otp",
            "mfa_code",
            "verification_code",
            "auth_code",
            "database_password",
            "db_password",
            "session_id",
            "cookie",
        ],
    )
    def test_sensitive_data_001_exact_match_sensitive_keys(self, field_name: str) -> None:
        """[test_sensitive_data-001] SENSITIVE_KEYSの完全一致で機密と判定。"""
        assert is_sensitive_field(field_name) is True

    @pytest.mark.parametrize(
        "field_name",
        [
            "PASSWORD",
            "Password",
            "TOKEN",
            "Token",
            "API_KEY",
            "Api_Key",
            "CSRF_TOKEN",
            "Csrf_Token",
        ],
    )
    def test_sensitive_data_002_case_insensitive_match(self, field_name: str) -> None:
        """[test_sensitive_data-002] 大文字小文字を区別しない判定。"""
        assert is_sensitive_field(field_name) is True

    # ==========================================================================
    # パターンマッチテスト
    # ==========================================================================

    @pytest.mark.parametrize(
        "field_name",
        [
            # パスワードパターン
            "new_password",
            "old_password",
            "password_confirm",
            "user_password",
            "hashed_password",
            "password_hash",
            # シークレットパターン
            "client_secret",
            "app_secret",
            "secret_value",
            "api_secret",
            # トークンパターン
            "auth_token",
            "reset_token",
            "token_value",
            "user_token",
            # キーパターン
            "api_key",
            "encryption_key",
            "key_value",
            "signing_key",
            # 認証パターン
            "oauth_code",
            "user_auth",
            "auth_header",
            # SASパターン
            "sas_url",
            "blob_sas",
            "container_sas",
            "shared_access_token",
        ],
    )
    def test_sensitive_data_003_pattern_match_sensitive_fields(self, field_name: str) -> None:
        """[test_sensitive_data-003] パターンマッチで機密と判定。"""
        assert is_sensitive_field(field_name) is True

    # ==========================================================================
    # 誤検出防止テスト（False Positive Prevention）
    # ==========================================================================

    @pytest.mark.parametrize(
        "field_name",
        [
            # "auth"パターンの誤検出防止
            "author",
            "author_name",
            "author_id",
            "authored_at",
            "authored_by",
            # "key"パターンの誤検出防止
            "keyboard",
            "monkey",
            "donkey",
            "hockey",
            "turkey",
            # 一般的なフィールド名
            "id",
            "name",
            "email",
            "display_name",
            "created_at",
            "updated_at",
            "is_active",
            "description",
            "title",
            "content",
            "status",
            "type",
            "category",
            "count",
            "value",
            "data",
            "metadata",
            "settings",
            "config",
            "options",
            "items",
            "results",
            "response",
            "request",
            "user_id",
            "project_id",
        ],
    )
    def test_sensitive_data_004_non_sensitive_fields(self, field_name: str) -> None:
        """[test_sensitive_data-004] 非機密フィールドは機密と判定しない。"""
        assert is_sensitive_field(field_name) is False

    def test_sensitive_data_005_empty_string(self) -> None:
        """[test_sensitive_data-005] 空文字列は非機密。"""
        assert is_sensitive_field("") is False

    def test_sensitive_data_006_whitespace_only(self) -> None:
        """[test_sensitive_data-006] 空白のみは非機密。"""
        assert is_sensitive_field("   ") is False


class TestMaskSensitiveData:
    """mask_sensitive_data関数のテスト。"""

    # ==========================================================================
    # 基本テスト
    # ==========================================================================

    def test_sensitive_data_010_mask_simple_dict(self) -> None:
        """[test_sensitive_data-010] シンプルな辞書の機密フィールドをマスク。"""
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "name": "John",
        }
        result = mask_sensitive_data(data)

        assert result["email"] == "user@example.com"
        assert result["password"] == "***MASKED***"
        assert result["name"] == "John"

    def test_sensitive_data_011_mask_multiple_sensitive_fields(self) -> None:
        """[test_sensitive_data-011] 複数の機密フィールドをマスク。"""
        data = {
            "user": "admin",
            "password": "secret",
            "api_key": "sk-12345",
            "token": "jwt-token",
            "csrf_token": "csrf-value",
        }
        result = mask_sensitive_data(data)

        assert result["user"] == "admin"
        assert result["password"] == "***MASKED***"
        assert result["api_key"] == "***MASKED***"
        assert result["token"] == "***MASKED***"
        assert result["csrf_token"] == "***MASKED***"

    # ==========================================================================
    # ネストテスト
    # ==========================================================================

    def test_sensitive_data_012_mask_nested_dict(self) -> None:
        """[test_sensitive_data-012] ネストされた辞書の機密フィールドをマスク。"""
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "password": "secret",
                    "api_key": "key-123",
                },
            },
        }
        result = mask_sensitive_data(data)

        assert result["user"]["name"] == "John"
        assert result["user"]["credentials"]["password"] == "***MASKED***"
        assert result["user"]["credentials"]["api_key"] == "***MASKED***"

    def test_sensitive_data_013_mask_deeply_nested_dict(self) -> None:
        """[test_sensitive_data-013] 深くネストされた辞書も再帰的にマスク。"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "password": "deep-secret",
                            "name": "deep-name",
                        }
                    }
                }
            }
        }
        result = mask_sensitive_data(data)

        assert result["level1"]["level2"]["level3"]["level4"]["password"] == "***MASKED***"
        assert result["level1"]["level2"]["level3"]["level4"]["name"] == "deep-name"

    # ==========================================================================
    # リストテスト
    # ==========================================================================

    def test_sensitive_data_014_mask_list_of_dicts(self) -> None:
        """[test_sensitive_data-014] 辞書のリストの機密フィールドをマスク。"""
        data = {
            "users": [
                {"name": "User1", "password": "pass1"},
                {"name": "User2", "password": "pass2"},
            ]
        }
        result = mask_sensitive_data(data)

        assert result["users"][0]["name"] == "User1"
        assert result["users"][0]["password"] == "***MASKED***"
        assert result["users"][1]["name"] == "User2"
        assert result["users"][1]["password"] == "***MASKED***"

    def test_sensitive_data_015_mask_nested_list(self) -> None:
        """[test_sensitive_data-015] ネストされたリストの処理。"""
        data = {
            "groups": [
                {
                    "members": [
                        {"name": "Member1", "token": "token1"},
                        {"name": "Member2", "token": "token2"},
                    ]
                }
            ]
        }
        result = mask_sensitive_data(data)

        assert result["groups"][0]["members"][0]["token"] == "***MASKED***"
        assert result["groups"][0]["members"][1]["token"] == "***MASKED***"

    # ==========================================================================
    # 深度制限テスト
    # ==========================================================================

    def test_sensitive_data_016_depth_limit(self) -> None:
        """[test_sensitive_data-016] 深度制限（10レベル）を超えると打ち切り。"""
        # 11レベルのネスト構造を作成
        data: dict = {"password": "should-be-masked"}
        for i in range(12):
            data = {f"level{i}": data}

        result = mask_sensitive_data(data)

        # 最深部は ***NESTED*** になる
        current = result
        for i in range(11, -1, -1):
            if i == 0:
                # 11レベル目（depth=10を超過）は打ち切り
                assert current[f"level{i}"] == "***NESTED***"
            else:
                current = current[f"level{i}"]

    # ==========================================================================
    # 非辞書データテスト
    # ==========================================================================

    def test_sensitive_data_017_non_dict_data(self) -> None:
        """[test_sensitive_data-017] 非辞書データはそのまま返す。"""
        assert mask_sensitive_data("string") == "string"
        assert mask_sensitive_data(123) == 123
        assert mask_sensitive_data(12.34) == 12.34
        assert mask_sensitive_data(True) is True
        assert mask_sensitive_data(None) is None

    def test_sensitive_data_018_simple_list(self) -> None:
        """[test_sensitive_data-018] シンプルなリストはそのまま返す。"""
        data = ["a", "b", "c"]
        result = mask_sensitive_data(data)
        assert result == ["a", "b", "c"]

    def test_sensitive_data_019_empty_dict(self) -> None:
        """[test_sensitive_data-019] 空辞書は空辞書を返す。"""
        assert mask_sensitive_data({}) == {}

    def test_sensitive_data_020_empty_list(self) -> None:
        """[test_sensitive_data-020] 空リストは空リストを返す。"""
        assert mask_sensitive_data([]) == []

    # ==========================================================================
    # パターンマッチによるマスクテスト
    # ==========================================================================

    def test_sensitive_data_021_pattern_matched_fields_masked(self) -> None:
        """[test_sensitive_data-021] パターンマッチした機密フィールドもマスク。"""
        data = {
            "new_password": "new-secret",
            "client_secret": "client-secret-value",
            "auth_token": "auth-token-value",
            "sas_url": "https://example.com/sas",
        }
        result = mask_sensitive_data(data)

        assert result["new_password"] == "***MASKED***"
        assert result["client_secret"] == "***MASKED***"
        assert result["auth_token"] == "***MASKED***"
        assert result["sas_url"] == "***MASKED***"

    # ==========================================================================
    # 実際のユースケーステスト
    # ==========================================================================

    def test_sensitive_data_022_realistic_user_registration(self) -> None:
        """[test_sensitive_data-022] 実際のユーザー登録リクエストのマスク。"""
        data = {
            "email": "user@example.com",
            "password": "MySecretPassword123!",
            "password_confirm": "MySecretPassword123!",
            "display_name": "John Doe",
            "profile": {
                "bio": "Hello, I am John",
                "settings": {
                    "theme": "dark",
                    "api_key": "user-api-key",
                },
            },
        }
        result = mask_sensitive_data(data)

        assert result["email"] == "user@example.com"
        assert result["password"] == "***MASKED***"
        assert result["password_confirm"] == "***MASKED***"
        assert result["display_name"] == "John Doe"
        assert result["profile"]["bio"] == "Hello, I am John"
        assert result["profile"]["settings"]["theme"] == "dark"
        assert result["profile"]["settings"]["api_key"] == "***MASKED***"

    def test_sensitive_data_023_realistic_api_config(self) -> None:
        """[test_sensitive_data-023] 実際のAPI設定のマスク。"""
        data = {
            "endpoint": "https://api.example.com",
            "api_key": "sk-1234567890",
            "client_id": "client-123",
            "client_secret": "secret-456",
            "connection_string": "Server=myserver;Database=mydb;Password=secret",
            "timeout": 30,
        }
        result = mask_sensitive_data(data)

        assert result["endpoint"] == "https://api.example.com"
        assert result["api_key"] == "***MASKED***"
        assert result["client_id"] == "***MASKED***"
        assert result["client_secret"] == "***MASKED***"
        assert result["connection_string"] == "***MASKED***"
        assert result["timeout"] == 30


class TestSensitiveKeysAndPatterns:
    """SENSITIVE_KEYSとSENSITIVE_PATTERNSの定義テスト。"""

    def test_sensitive_data_030_sensitive_keys_not_empty(self) -> None:
        """[test_sensitive_data-030] SENSITIVE_KEYSが空でないこと。"""
        assert len(SENSITIVE_KEYS) > 0

    def test_sensitive_data_031_sensitive_patterns_not_empty(self) -> None:
        """[test_sensitive_data-031] SENSITIVE_PATTERNSが空でないこと。"""
        assert len(SENSITIVE_PATTERNS) > 0

    def test_sensitive_data_032_all_keys_lowercase(self) -> None:
        """[test_sensitive_data-032] SENSITIVE_KEYSはすべて小文字。"""
        for key in SENSITIVE_KEYS:
            assert key == key.lower(), f"Key '{key}' should be lowercase"

    def test_sensitive_data_033_patterns_are_compiled(self) -> None:
        """[test_sensitive_data-033] SENSITIVE_PATTERNSはコンパイル済み正規表現。"""
        import re

        for pattern in SENSITIVE_PATTERNS:
            assert isinstance(pattern, re.Pattern), f"Pattern {pattern} should be compiled"
