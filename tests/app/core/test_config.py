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
        """[test_config-001] 本番環境で開発モード認証が有効な場合にエラーを発生させる。

        セキュリティリスク防止のため、ENVIRONMENT=production かつ
        AUTH_MODE=development の組み合わせは禁止される。
        """
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "development",
                "SECRET_KEY": "a" * 32,  # 本番環境では必須
                "ALLOWED_ORIGINS": '["https://example.com"]',  # 本番環境では必須
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

    def test_development_with_dev_auth_success(self):
        """[test_config-003] 開発環境では開発モード認証を許可する。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "development",
                "AUTH_MODE": "development",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.ENVIRONMENT == "development"
            assert settings.AUTH_MODE == "development"

    def test_staging_with_dev_auth_success(self):
        """[test_config-004] ステージング環境では開発モード認証を許可する。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "staging",
                "AUTH_MODE": "development",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.ENVIRONMENT == "staging"
            assert settings.AUTH_MODE == "development"


class TestSecretKeyValidation:
    """SECRET_KEY の本番環境バリデーションテスト。"""

    def test_production_without_secret_key_raises_error(self):
        """[test_config-005] 本番環境でSECRET_KEYが未設定の場合にエラーを発生させる。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "production",
                "ALLOWED_ORIGINS": '["https://example.com"]',
                "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-test-key",
                "AZURE_TENANT_ID": "test-tenant-id",
                "AZURE_CLIENT_ID": "test-client-id",
                # SECRET_KEYは環境変数に設定せず、デフォルト値を使わせる
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError,
                match="本番環境ではSECRET_KEYを設定する必要があります",
            ):
                Settings(_env_file=None)

    def test_production_with_default_secret_key_raises_error(self):
        """[test_config-006] 本番環境でデフォルトSECRET_KEYを使用した場合にエラーを発生させる。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "production",
                "SECRET_KEY": "dev-secret-key-change-in-production-must-be-32-chars-minimum",
                "ALLOWED_ORIGINS": '["https://example.com"]',
                "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-test-key",
                "AZURE_TENANT_ID": "test-tenant-id",
                "AZURE_CLIENT_ID": "test-client-id",
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError,
                match="本番環境ではSECRET_KEYを設定する必要があります",
            ):
                Settings()


class TestAllowedOriginsValidation:
    """ALLOWED_ORIGINS の本番環境バリデーションテスト。"""

    def test_production_without_allowed_origins_raises_error(self):
        """[test_config-007] 本番環境でALLOWED_ORIGINSが未設定の場合にエラーを発生させる。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "production",
                "SECRET_KEY": "a" * 32,
                "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-test-key",
                "AZURE_TENANT_ID": "test-tenant-id",
                "AZURE_CLIENT_ID": "test-client-id",
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError,
                match="本番環境ではALLOWED_ORIGINSを明示的に設定する必要があります",
            ):
                # _env_file=Noneを指定して.envファイルの読み込みを無効化
                Settings(_env_file=None)

    def test_production_with_wildcard_cors_raises_error(self):
        """[test_config-008] 本番環境でワイルドカードCORSを使用した場合にエラーを発生させる。"""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "AUTH_MODE": "production",
                "SECRET_KEY": "a" * 32,
                "ALLOWED_ORIGINS": '["*"]',
                "DATABASE_URL": "postgresql+asyncpg://prod-db:5432/app_db",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-test-key",
                "AZURE_TENANT_ID": "test-tenant-id",
                "AZURE_CLIENT_ID": "test-client-id",
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError,
                match="本番環境ではワイルドカードCORS",
            ):
                Settings()


class TestAzureAdValidation:
    """Azure AD設定の本番モードバリデーションテスト。"""

    def test_production_auth_without_tenant_id_raises_error(self):
        """[test_config-009] 本番モード認証でAZURE_TENANT_IDが未設定の場合にエラーを発生させる。"""
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
                "AZURE_CLIENT_ID": "test-client-id",
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError,
                match="AUTH_MODE=productionの場合、AZURE_TENANT_IDが必要です",
            ):
                Settings()

    def test_production_auth_without_client_id_raises_error(self):
        """[test_config-010] 本番モード認証でAZURE_CLIENT_IDが未設定の場合にエラーを発生させる。"""
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
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError,
                match="AUTH_MODE=productionの場合、AZURE_CLIENT_IDが必要です",
            ):
                Settings()
