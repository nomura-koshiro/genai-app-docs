"""機密情報パターンの一元管理。

監査ログ、操作履歴などで機密情報をマスクする際の共通パターンを定義します。
"""

import re
from typing import Any

# 機密情報として除外するフィールド（完全一致）
SENSITIVE_KEYS: set[str] = {
    # SQLAlchemy内部
    "_sa_instance_state",
    # 認証関連
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
    # CSRF
    "csrf_token",
    "csrf",
    "xsrf_token",
    "xsrf",
    # Azure/クラウド関連
    "client_secret",
    "client_id",  # OAuth client ID（漏洩リスクがある場合）
    "azure_client_secret",
    "connection_string",
    "sas_token",
    "shared_access_signature",
    "account_key",
    "storage_account_key",
    # 暗号化関連
    "private_key",
    "secret_key",
    "encryption_key",
    "signing_key",
    "master_key",
    # 個人情報
    "ssn",
    "social_security_number",
    "credit_card",
    "card_number",
    "cvv",
    "cvc",
    "bank_account",
    "routing_number",
    # 認証コード
    "pin",
    "otp",
    "mfa_code",
    "verification_code",
    "auth_code",
    # データベース
    "database_password",
    "db_password",
    # セッション
    "session_id",
    "cookie",
}

# 機密情報として除外するフィールドパターン（正規表現）
# 注意: 過剰検知を防ぐため、具体的なパターンを使用
# - "author"が"auth"にマッチしないよう、単語境界を意識
# - "keyboard"が"key"にマッチしないよう、アンダースコア区切りで限定
SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    # パスワード関連: password, new_password, password_hash
    re.compile(r"^password$|_password$|^password_|_password_", re.IGNORECASE),
    # シークレット関連: secret, client_secret, secret_key
    re.compile(r"^secret$|_secret$|^secret_|_secret_", re.IGNORECASE),
    # トークン関連: token, access_token, token_id
    re.compile(r"^token$|_token$|^token_|_token_", re.IGNORECASE),
    # キー関連: key, api_key, encryption_key（keyboardやmonkeyにマッチしない）
    re.compile(r"^key$|_key$|^key_|_key_", re.IGNORECASE),
    # 認証情報関連: credential, credentials
    re.compile(r"credential", re.IGNORECASE),
    # Bearer関連
    re.compile(r"bearer", re.IGNORECASE),
    # 認証関連: auth, oauth, auth_code（authorにマッチしない）
    re.compile(r"^auth$|_auth$|^auth_|_auth_|oauth", re.IGNORECASE),
    # Azure SAS関連: sas_token, sas_url, shared_access_signature
    re.compile(r"^sas$|_sas$|^sas_|_sas_|shared_access", re.IGNORECASE),
]


def is_sensitive_field(field_name: str) -> bool:
    """フィールド名が機密情報かどうかを判定します。

    完全一致とパターンマッチングの両方でチェックします。

    Args:
        field_name: チェック対象のフィールド名

    Returns:
        bool: 機密情報の場合True
    """
    field_lower = field_name.lower()

    # 完全一致チェック
    if field_lower in SENSITIVE_KEYS:
        return True

    # パターンマッチング（search()を使用して文字列全体を検索）
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(field_lower):
            return True

    return False


def mask_sensitive_data(data: Any, depth: int = 0) -> Any:
    """機密情報をマスクします。

    完全一致とパターンマッチングの両方を使用して機密情報を検出します。

    Args:
        data: マスク対象データ
        depth: ネスト深度（無限ループ防止）

    Returns:
        Any: マスク済みデータ
    """
    if depth > 10:  # 深すぎるネストは打ち切り
        return "***NESTED***"

    if isinstance(data, dict):
        return {
            key: (
                "***MASKED***"
                if is_sensitive_field(key)
                else mask_sensitive_data(value, depth + 1)
            )
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, depth + 1) for item in data]
    else:
        return data
