"""JWT（JSON Web Token）認証。

このモジュールは、JWTトークンの生成、検証機能を提供します。

主な機能:
    - create_access_token(): JWTアクセストークン生成
    - decode_access_token(): JWTトークンの検証とデコード
    - create_refresh_token(): リフレッシュトークン生成
    - decode_refresh_token(): リフレッシュトークンの検証とデコード

セキュリティ設定:
    - JWT: HS256アルゴリズム（設定可能）
    - トークン有効期限: 設定ファイルで指定（デフォルト: 30分）

使用例:
    >>> from app.core.security.jwt import create_access_token
    >>>
    >>> # JWTトークン生成
    >>> token = create_access_token({"sub": "1"})
    >>> print(token[:20])
    eyJ0eXAiOiJKV1QiLCJh...
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

try:
    from jose import ExpiredSignatureError, JWTError, jwt
except ImportError:
    jwt = None  # type: ignore
    JWTError = Exception  # type: ignore
    ExpiredSignatureError = Exception  # type: ignore

logger = get_logger(__name__)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """JWTアクセストークンを生成します。

    この関数は、ユーザー認証後にアクセストークンを生成するために使用されます。
    生成されたトークンは、API リクエストのAuthorizationヘッダーに含めて送信します。

    トークンに含まれるフィールド:
        - sub: Subject（通常はuser_id）- dataパラメータで指定
        - exp: 有効期限（UTC）- 自動設定
        - iat: 発行時刻（UTC）- 自動設定
        - type: トークンタイプ（"access"）- 自動設定
        - その他: dataパラメータで指定した追加フィールド

    アルゴリズム:
        - HS256（HMAC-SHA256）- デフォルト
        - SECRET_KEYで署名

    Args:
        data (dict[str, Any]): トークンペイロードに含めるデータ
            - 必須: {"sub": "user_id"}
            - オプション: 追加のクレーム
            例: {"sub": "1", "role": "admin"}
        expires_delta (timedelta | None): トークンの有効期限
            - None: デフォルト有効期限を使用（settings.ACCESS_TOKEN_EXPIRE_MINUTES）
            - timedelta: カスタム有効期限
            例: timedelta(hours=1)

    Returns:
        str: エンコードされたJWTトークン文字列
            - 形式: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            - Authorizationヘッダーで使用: "Bearer {token}"

    Raises:
        ImportError: python-joseライブラリがインストールされていない場合

    Example:
        >>> # ユーザーID 1 のトークン生成（デフォルト有効期限）
        >>> token = create_access_token({"sub": "1"})
        >>> print(token[:20])
        eyJ0eXAiOiJKV1QiLCJh...
        >>>
        >>> # カスタム有効期限（1時間）
        >>> from datetime import timedelta
        >>> token = create_access_token(
        ...     {"sub": "1", "role": "admin"},
        ...     expires_delta=timedelta(hours=1)
        ... )
        >>>
        >>> # ログイン成功後の使用例
        >>> user = await user_service.authenticate(email, password)
        >>> access_token = create_access_token({"sub": str(user.id)})
        >>> return {"access_token": access_token, "token_type": "bearer"}

    Note:
        - SECRET_KEYは環境変数で設定する必要があります
        - subフィールド（user_id）は文字列として渡してください
        - トークンは有効期限後に自動的に無効化されます
        - リフレッシュトークンは別途実装が必要です
        - HTTPS環境での使用を強く推奨します
    """
    if jwt is None:
        raise ImportError("python-jose is required for JWT token creation")

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        # 設定ファイルから有効期限を取得
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),  # 発行時刻を追加
            "type": "access",  # トークンタイプを追加
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """JWTアクセストークンをデコードし、検証します。

    この関数は、APIリクエストのAuthorizationヘッダーから受け取ったトークンを
    デコードし、有効性を検証します。トークンが有効な場合、ペイロードを返します。

    検証項目:
        - 署名の検証（SECRET_KEYとの一致）
        - 有効期限の検証（exp）
        - アルゴリズムの検証（HS256）
        - subフィールドの存在確認

    Args:
        token (str): デコードするJWTトークン文字列
            - Authorizationヘッダーから抽出したトークン
            - "Bearer "プレフィックスは除去済みであること
            - 例: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

    Returns:
        dict[str, Any] | None: デコードされたトークンペイロード、無効な場合はNone
            - 成功時: {"sub": "1", "exp": 1234567890, "iat": 1234567890, ...}
            - 失敗時: None（有効期限切れ、署名不正、フォーマットエラー等）

    Raises:
        ImportError: python-joseライブラリがインストールされていない場合

    Example:
        >>> # 有効なトークンのデコード
        >>> token = create_access_token({"sub": "1"})
        >>> payload = decode_access_token(token)
        >>> if payload:
        ...     user_id = payload.get("sub")
        ...     print(f"User ID: {user_id}")
        ... else:
        ...     print("Invalid token")
        User ID: 1
        >>>
        >>> # APIエンドポイントでの使用例
        >>> authorization = request.headers.get("Authorization")
        >>> if not authorization or not authorization.startswith("Bearer "):
        ...     raise HTTPException(401, "Invalid authorization header")
        >>> token = authorization.split(" ")[1]
        >>> payload = decode_access_token(token)
        >>> if not payload:
        ...     raise HTTPException(401, "Invalid or expired token")
        >>> user_id = int(payload["sub"])

    Note:
        - トークンが無効な場合、Noneを返し、警告ログを記録します
        - 有効期限切れ、署名不正、フォーマットエラーはすべてNoneを返します
        - subフィールドが存在しない場合もNoneを返します
        - エラーの詳細はログで確認できます
        - セキュリティ上、クライアントには詳細なエラーを返さないでください
    """
    if jwt is None:
        raise ImportError("python-jose is required for JWT token decoding")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,  # 明示的に有効期限を検証
                "verify_signature": True,
            },
        )

        # 追加の検証: sub (subject) フィールドの存在確認
        if "sub" not in payload:
            logger.warning("JWTトークン検証失敗", reason="sub_field_missing")
            return None

        return payload

    except ExpiredSignatureError:
        logger.warning("JWTトークン有効期限切れ")
        return None
    except JWTError as e:
        logger.warning(
            "JWTデコードエラー",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        return None


def create_refresh_token(data: dict[str, Any]) -> str:
    """リフレッシュトークンを生成します。

    リフレッシュトークンはアクセストークンより長い有効期限を持ち、
    新しいアクセストークンを取得するために使用されます。

    Args:
        data: トークンペイロードに含めるデータ

    Returns:
        str: エンコードされたリフレッシュトークン文字列
    """
    if jwt is None:
        raise ImportError("python-jose is required for JWT token creation")

    to_encode = data.copy()
    # リフレッシュトークンの有効期限: 7日間
    expire = datetime.now(UTC) + timedelta(days=7)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    """リフレッシュトークンをデコードし、検証します。

    Args:
        token: デコードするリフレッシュトークン文字列

    Returns:
        dict[str, Any] | None: デコードされたトークンペイロード、無効な場合はNone
    """
    if jwt is None:
        raise ImportError("python-jose is required for JWT token decoding")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,
                "verify_signature": True,
            },
        )

        # トークンタイプの検証
        if payload.get("type") != "refresh":
            logger.warning("トークンタイプが'refresh'ではありません")
            return None

        if "sub" not in payload:
            logger.warning("リフレッシュトークンに'sub'フィールドがありません")
            return None

        return payload

    except ExpiredSignatureError:
        logger.warning("リフレッシュトークンの有効期限が切れています")
        return None
    except JWTError as e:
        logger.warning(f"リフレッシュトークンデコードエラー: {e}")
        return None
