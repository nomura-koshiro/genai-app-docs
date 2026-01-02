"""アプリケーション設定のテスト。

このモジュールは、app.core.config.Settingsクラスのバリデーションをテストします。

テスト方針（TEST_REDUCTION_POLICY.md に準拠）:
    1. Happy Path: 正常な設定のテスト
    2. セキュリティバリデーション: 本番環境でのセキュリティチェック
    3. エラーケース: 代表的な設定エラーのみテスト

テストカテゴリ:
    - 開発モード認証の本番環境混入防止
    - SECRET_KEY の本番環境検証
    - ALLOWED_ORIGINS の本番環境検証
    - Azure AD設定の検証
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestDevAuthProductionValidation:
    """開発モード認証の本番環境混入防止テスト。"""

    def test_production_with_dev_auth_raises_error(self):
        """[test_config-001] 本番環境で開発モード認証が有効な場合にエラーを発生させる。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "development",
                "SECRET_KEY": "a" * 32,
                "ALLOWED_ORIGINS": '["https://example.com"]',
                "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-test-key",
            },
            clear=True,
        ):
            with pytest.raises(
                ValidationError,
                match="Development authentication cannot be enabled in production environment",
            ):
                Settings()

    def test_production_with_production_auth_success(self):
        """[test_config-002] 本番環境で本番モード認証を使用する場合は正常に動作する。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "production",
                "SECRET_KEY": "a" * 32,
                "ALLOWED_ORIGINS": '["https://example.com"]',
                "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-test-key",
                "AZURE_TENANT_ID": "test-tenant-id",
                "AZURE_CLIENT_ID": "test-client-id",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.ENVIRONMENT == "production"
            assert settings.AUTH_MODE == "production"

    @pytest.mark.parametrize(
        "environment",
        ["development", "staging"],
        ids=["development", "staging"],
    )
    def test_non_production_with_dev_auth_success(self, environment: str):
        """[test_config-003] 非本番環境では開発モード認証を許可する。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": environment,
                "AUTH_MODE": "development",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.ENVIRONMENT == environment
            assert settings.AUTH_MODE == "development"


class TestSecretKeyValidation:
    """SECRET_KEY の本番環境バリデーションテスト。"""

    @pytest.mark.parametrize(
        "secret_key,use_env_file",
        [
            (None, None),  # 未設定
            ("dev-secret-key-change-in-production-must-be-32-chars-minimum", False),  # デフォルト値
        ],
        ids=["not_set", "default_value"],
    )
    def test_production_with_invalid_secret_key_raises_error(
        self, secret_key: str | None, use_env_file: bool | None
    ):
        """[test_config-005] 本番環境で無効なSECRET_KEYの場合にエラーを発生させる。"""
        env_vars = {
            "ENVIRONMENT": "production",
            "AUTH_MODE": "production",
            "ALLOWED_ORIGINS": '["https://example.com"]',
            "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-test-key",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AZURE_CLIENT_ID": "test-client-id",
        }
        if secret_key:
            env_vars["SECRET_KEY"] = secret_key

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(
                ValueError,
                match="本番環境ではSECRET_KEYを設定する必要があります",
            ):
                if use_env_file is None:
                    Settings(_env_file=None)
                else:
                    Settings()


class TestAllowedOriginsValidation:
    """ALLOWED_ORIGINS の本番環境バリデーションテスト。"""

    @pytest.mark.parametrize(
        "allowed_origins,error_match,use_env_file",
        [
            (None, "本番環境ではALLOWED_ORIGINSを明示的に設定する必要があります", None),
            ('["*"]', "本番環境ではワイルドカードCORS", False),
        ],
        ids=["not_set", "wildcard"],
    )
    def test_production_with_invalid_allowed_origins_raises_error(
        self, allowed_origins: str | None, error_match: str, use_env_file: bool | None
    ):
        """[test_config-007] 本番環境で無効なALLOWED_ORIGINSの場合にエラーを発生させる。"""
        env_vars = {
            "ENVIRONMENT": "production",
            "AUTH_MODE": "production",
            "SECRET_KEY": "a" * 32,
            "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-test-key",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AZURE_CLIENT_ID": "test-client-id",
        }
        if allowed_origins:
            env_vars["ALLOWED_ORIGINS"] = allowed_origins

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match=error_match):
                if use_env_file is None:
                    Settings(_env_file=None)
                else:
                    Settings()


class TestAzureAdValidation:
    """Azure AD設定の本番モードバリデーションテスト。"""

    @pytest.mark.parametrize(
        "missing_field,error_match",
        [
            ("AZURE_TENANT_ID", "AUTH_MODE=productionの場合、AZURE_TENANT_IDが必要です"),
            ("AZURE_CLIENT_ID", "AUTH_MODE=productionの場合、AZURE_CLIENT_IDが必要です"),
        ],
        ids=["missing_tenant_id", "missing_client_id"],
    )
    def test_production_auth_without_azure_config_raises_error(
        self, missing_field: str, error_match: str
    ):
        """[test_config-009] 本番モード認証でAzure AD設定が不足の場合にエラーを発生させる。"""
        env_vars = {
            "ENVIRONMENT": "production",
            "AUTH_MODE": "production",
            "SECRET_KEY": "a" * 32,
            "ALLOWED_ORIGINS": '["https://example.com"]',
            "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-test-key",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AZURE_CLIENT_ID": "test-client-id",
        }
        # 指定フィールドを削除
        del env_vars[missing_field]

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match=error_match):
                Settings()
