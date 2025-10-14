"""認証・認可のためのセキュリティユーティリティ."""

from datetime import datetime, timedelta, timezone
from typing import Any

from passlib.context import CryptContext

from app.config import settings

try:
    from jose import JWTError, jwt
except ImportError:
    jwt = None  # type: ignore
    JWTError = Exception  # type: ignore


# パスワードハッシュ化コンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードをハッシュ化されたパスワードと照合.

    Args:
        plain_password: 平文パスワード
        hashed_password: 照合するハッシュ化パスワード

    Returns:
        パスワードが一致する場合True、そうでない場合False
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """パスワードをハッシュ化.

    Args:
        password: 平文パスワード

    Returns:
        ハッシュ化されたパスワード
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """JWTアクセストークンを作成.

    Args:
        data: トークンにエンコードするデータ
        expires_delta: トークンの有効期限

    Returns:
        エンコードされたJWTトークン

    Raises:
        ImportError: python-joseがインストールされていない場合
    """
    if jwt is None:
        raise ImportError("python-jose is required for JWT token creation")

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """JWTアクセストークンをデコード.

    Args:
        token: デコードするJWTトークン

    Returns:
        デコードされたトークンペイロード、無効な場合はNone

    Raises:
        ImportError: python-joseがインストールされていない場合
    """
    if jwt is None:
        raise ImportError("python-jose is required for JWT token decoding")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """ランダムなAPIキーを生成.

    Returns:
        ランダムなAPIキー文字列
    """
    import secrets

    return secrets.token_urlsafe(32)
