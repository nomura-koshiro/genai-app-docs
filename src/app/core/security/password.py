"""パスワードハッシュ化と検証。

このモジュールは、パスワードのハッシュ化、検証、強度チェック機能を提供します。

主な機能:
    - hash_password(): bcryptでパスワードをハッシュ化
    - verify_password(): パスワードの検証
    - validate_password_strength(): パスワード強度チェック

セキュリティ設定:
    - bcrypt: パスワードハッシュアルゴリズム（コスト: 12ラウンド）
    - SHA-256事前ハッシュ化: bcryptの72バイト制限に対処

パスワード強度要件:
    - 最小8文字
    - 大文字を1つ以上
    - 小文字を1つ以上
    - 数字を1つ以上
    - 特殊文字を1つ以上（推奨）

使用例:
    >>> from app.core.security.password import hash_password, verify_password
    >>>
    >>> # パスワードのハッシュ化
    >>> hashed = hash_password("SecurePass123!")
    >>> print(hashed)
    $2b$12$KIX...
    >>>
    >>> # パスワードの検証
    >>> is_valid = verify_password("SecurePass123!", hashed)
    >>> print(is_valid)
    True
"""

import hashlib
import re

import bcrypt
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化されたパスワードを照合します。

    この関数は、ユーザーログイン時にパスワードを検証するために使用されます。
    bcryptアルゴリズムを使用して、平文パスワードがハッシュと一致するか
    セキュアに検証します。

    セキュリティ特性:
        - 定時間比較（タイミング攻撃対策）
        - bcryptのsalt自動処理
        - ハッシュ形式の自動検出

    Args:
        plain_password (str): ユーザーが入力した平文パスワード
            - ログインフォームからの入力値
            - ハッシュ化されていない状態
            - 72バイト以上のパスワードはSHA-256で事前ハッシュ化
        hashed_password (str): データベースに保存されたハッシュ化パスワード
            - bcrypt形式: $2b$12$...
            - hash_password()で生成されたもの

    Returns:
        bool: パスワードが一致する場合True、不一致の場合False
            - True: 認証成功
            - False: 認証失敗（ログイン失敗回数をインクリメント推奨）

    Example:
        >>> # ユーザー登録時
        >>> hashed = hash_password("SecurePass123!")
        >>> # データベースに保存: user.hashed_password = hashed
        >>>
        >>> # ログイン時
        >>> input_password = "SecurePass123!"
        >>> is_valid = verify_password(input_password, user.hashed_password)
        >>> if is_valid:
        ...     print("Login successful")
        ... else:
        ...     print("Invalid credentials")
        Login successful

    Note:
        - この関数は定時間で実行され、タイミング攻撃を防ぎます
        - 失敗時にログイン試行回数をカウントすることを推奨
        - 平文パスワードはログに記録しないでください
        - SHA-256ハッシュを使用してbcryptの72バイト制限に対応
    """
    # bcryptの72バイト制限に対処するため、SHA-256で事前ハッシュ化
    # これにより、任意の長さのパスワードを安全に処理でき、
    # マルチバイト文字（日本語等）も正しく扱えます
    password_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()

    # bcrypt.checkpw()は bytes を要求するため、エンコード
    return bcrypt.checkpw(password_hash.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(password: str) -> str:
    """平文パスワードをbcryptアルゴリズムでハッシュ化します。

    この関数は、ユーザー登録時やパスワード変更時に使用されます。
    bcryptアルゴリズムを使用し、自動的にsaltを生成してセキュアな
    ハッシュを生成します。

    セキュリティ特性:
        - bcryptアルゴリズム（コスト: 12ラウンド）
        - ランダムsalt自動生成
        - レインボーテーブル攻撃耐性
        - ブルートフォース攻撃耐性（計算コストが高い）

    Args:
        password (str): ハッシュ化する平文パスワード
            - ユーザー入力のパスワード
            - 最小8文字推奨（validate_password_strength参照）
            - 72バイト以上のパスワードはSHA-256で事前ハッシュ化

    Returns:
        str: bcrypt形式のハッシュ化されたパスワード
            - 形式: $2b$12$[salt][hash]
            - 長さ: 約60文字
            - データベースに保存する値

    Example:
        >>> # ユーザー登録時
        >>> password = "SecurePass123!"
        >>> hashed = hash_password(password)
        >>> print(hashed)
        $2b$12$KIXqZ9Q5ZqZ9Q5ZqZ9Q5ZeO...
        >>>
        >>> # データベースに保存
        >>> user.hashed_password = hashed
        >>> await db.commit()
        >>>
        >>> # 同じパスワードでも毎回異なるハッシュが生成される
        >>> hash1 = hash_password("password")
        >>> hash2 = hash_password("password")
        >>> print(hash1 == hash2)
        False

    Note:
        - 同じパスワードでも毎回異なるハッシュが生成されます（salt）
        - ハッシュ化は計算コストが高いため、適切に使用してください
        - 平文パスワードは絶対にデータベースに保存しないでください
        - 生成されたハッシュはString(100)フィールドに保存してください
        - SHA-256ハッシュを使用してbcryptの72バイト制限に対応
    """
    # bcryptの72バイト制限に対処するため、SHA-256で事前ハッシュ化
    # SHA-256は常に64文字の16進数文字列を生成（64バイト < 72バイト）
    # これにより、任意の長さのパスワードを安全に処理でき、
    # マルチバイト文字（日本語等）も正しく扱えます
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # bcrypt.hashpw()は bytes を要求するため、エンコード
    # gensalt()でランダムなsaltを生成（コストファクター: settings.BCRYPT_ROUNDS）
    hashed = bcrypt.hashpw(password_hash.encode("utf-8"), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS))

    # 結果をstrに変換して返す
    return hashed.decode("utf-8")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """パスワードの強度を検証し、セキュリティ要件を満たしているか確認します。

    この関数は、ユーザー登録やパスワード変更時に、パスワードが
    セキュリティ要件を満たしているかを検証します。

    パスワード要件（必須）:
        - 最小8文字
        - 大文字を1つ以上含む（A-Z）
        - 小文字を1つ以上含む（a-z）
        - 数字を1つ以上含む（0-9）

    推奨事項:
        - 特殊文字を1つ以上含む（!@#$%^&*(),.?":{}|<>）
        - 12文字以上
        - 辞書にない単語
        - 個人情報（名前、誕生日等）を含まない

    Args:
        password (str): 検証するパスワード
            - ユーザー入力のパスワード
            - ハッシュ化前の平文

    Returns:
        tuple[bool, str]: (検証結果, エラーメッセージ) のタプル
            - (True, ""): 検証成功
            - (False, "エラーメッセージ"): 検証失敗と理由

    Example:
        >>> # 弱いパスワード
        >>> is_valid, error = validate_password_strength("password")
        >>> print(f"Valid: {is_valid}, Error: {error}")
        Valid: False, Error: パスワードには大文字を含めてください
        >>>
        >>> # 強いパスワード
        >>> is_valid, error = validate_password_strength("SecurePass123!")
        >>> print(f"Valid: {is_valid}")
        Valid: True
        >>>
        >>> # ユーザー登録時の使用例
        >>> password = request.password
        >>> is_valid, error_msg = validate_password_strength(password)
        >>> if not is_valid:
        ...     raise ValidationError(error_msg)
        >>> hashed = hash_password(password)

    Note:
        - 特殊文字は推奨ですが必須ではありません（警告ログのみ）
        - より厳格な要件が必要な場合は、この関数を拡張してください
        - パスワード強度メーターUIと併用することを推奨
        - 検証失敗時のエラーメッセージは日本語です
    """
    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"

    if not re.search(r"[A-Z]", password):
        return False, "パスワードには大文字を含めてください"

    if not re.search(r"[a-z]", password):
        return False, "パスワードには小文字を含めてください"

    if not re.search(r"\d", password):
        return False, "パスワードには数字を含めてください"

    # 特殊文字は推奨だが必須ではない
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        logger.warning("パスワードに特殊文字が含まれていません（推奨）")

    return True, ""
