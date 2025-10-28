"""APIキー生成ユーティリティ。

このモジュールは、セキュアなランダムAPIキー生成機能を提供します。

主な機能:
    - generate_api_key(): セキュアなランダムAPIキー生成

使用例:
    >>> from app.core.security.api_key import generate_api_key
    >>>
    >>> # APIキー生成
    >>> api_key = generate_api_key()
    >>> print(f"API Key: {api_key[:10]}...")
    API Key: dGhpcyBpcyBh...
"""

import secrets


def generate_api_key() -> str:
    """暗号学的に安全なランダムAPIキーを生成します。

    この関数は、外部サービス連携や管理者用APIアクセスに使用する
    セキュアなAPIキーを生成します。secretsモジュールを使用して、
    暗号学的に安全な乱数を生成します。

    生成されるAPIキー:
        - 長さ: 32バイト（URL-safeなbase64エンコードで約43文字）
        - 文字セット: A-Za-z0-9_-（URL-safe）
        - エントロピー: 256ビット
        - 衝突確率: 極めて低い

    Returns:
        str: URL-safeなランダムAPIキー文字列
            - 例: "dGhpcyBpcyBhIHNlY3VyZSByYW5kb20gYXBpIGtleQ"
            - データベースに保存する前にハッシュ化することを推奨

    Example:
        >>> # APIキー生成
        >>> api_key = generate_api_key()
        >>> print(f"API Key: {api_key[:10]}...")
        API Key: dGhpcyBpcyBh...
        >>>
        >>> # データベースに保存（ハッシュ化推奨）
        >>> from app.core.security.password import hash_password
        >>> hashed_api_key = hash_password(api_key)  # bcryptでハッシュ化
        >>> user.api_key_hash = hashed_api_key
        >>> await db.commit()
        >>> # ユーザーに一度だけAPI keyを表示
        >>> print(f"Your API Key: {api_key}")
        >>> print("Please save it. It won't be shown again.")

    Note:
        - secrets.token_urlsafe()は暗号学的に安全な乱数を使用
        - random.choice()やuuid.uuid4()よりセキュア
        - 生成されたAPIキーはユーザーに一度だけ表示してください
        - データベースにはハッシュ化して保存することを推奨
        - 32バイトは十分なエントロピーを提供します
    """
    return secrets.token_urlsafe(32)
