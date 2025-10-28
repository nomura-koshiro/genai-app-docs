"""認証・認可のためのセキュリティユーティリティ。

このパッケージは、アプリケーションのセキュリティ機能を提供します：
- パスワードハッシュ化と検証（bcrypt）
- JWT（JSON Web Token）の生成と検証
- パスワード強度検証
- APIキー生成

モジュール:
    password: パスワードハッシュ化と検証
    jwt: JWT認証
    api_key: APIキー生成

使用例:
    >>> from app.core.security import hash_password, verify_password
    >>> from app.core.security import create_access_token, decode_access_token
    >>> from app.core.security import generate_api_key
    >>>
    >>> # パスワードのハッシュ化
    >>> hashed = hash_password("SecurePass123!")
    >>>
    >>> # JWTトークン生成
    >>> token = create_access_token({"sub": "1"})
    >>>
    >>> # APIキー生成
    >>> api_key = generate_api_key()
"""

from app.core.security.api_key import generate_api_key
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.security.password import (
    hash_password,
    validate_password_strength,
    verify_password,
)

__all__ = [
    # パスワード関連
    "hash_password",
    "verify_password",
    "validate_password_strength",
    # JWT関連
    "create_access_token",
    "decode_access_token",
    "create_refresh_token",
    "decode_refresh_token",
    # APIキー
    "generate_api_key",
]
