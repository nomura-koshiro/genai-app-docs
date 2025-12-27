"""アプリケーション全体で使用されるカスタム例外クラス。

このモジュールは、HTTPステータスコードと詳細情報を持つアプリケーション固有の
例外クラスを提供します。すべてのカスタム例外はAppExceptionを継承し、
統一されたエラーハンドリングを可能にします。

例外階層:
    AppException（基底クラス）
    ├── NotFoundError (404) - リソース未検出
    ├── ValidationError (422) - バリデーションエラー
    ├── AuthenticationError (401) - 認証失敗
    ├── AuthorizationError (403) - 権限不足
    ├── PayloadTooLargeError (413) - ペイロードサイズ超過
    ├── UnsupportedMediaTypeError (415) - 非対応ファイルタイプ
    ├── DatabaseError (500) - データベース操作エラー
    └── ExternalServiceError (502) - 外部サービスエラー

使用方法:
    >>> from app.core.exceptions import NotFoundError
    >>>
    >>> # リソースが見つからない場合
    >>> raise NotFoundError("User not found", details={"user_id": 123})
    >>>
    >>> # バリデーションエラー
    >>> raise ValidationError(
    ...     "Invalid email format",
    ...     details={"field": "email", "value": "invalid"}
    ... )

エラーハンドリング:
    - すべてのカスタム例外はFastAPIのexception_handlerで捕捉されます
    - HTTPステータスコードとエラー詳細がJSON形式でクライアントに返されます
    - ログには完全なスタックトレースが記録されます

Note:
    - 例外発生時は必ず適切なメッセージとdetailsを提供してください
    - detailsにはデバッグに役立つ情報を含めますが、機密情報は含めないでください
"""

from typing import Any


class AppException(Exception):
    """すべてのアプリケーション例外の基底クラス。

    この基底クラスは、HTTPステータスコードと詳細情報を持つ統一された
    例外インターフェースを提供します。すべてのカスタム例外はこのクラスを
    継承する必要があります。

    Attributes:
        message (str): ユーザーに表示されるエラーメッセージ
        status_code (int): HTTPステータスコード（デフォルト: 500）
        details (dict): エラーの詳細情報（デバッグ用）

    Args:
        message (str): エラーメッセージ
        status_code (int): HTTPステータスコード（デフォルト: 500）
        details (dict[str, Any] | None): 追加の詳細情報
            例: {"field": "email", "value": "invalid"}

    Example:
        >>> # カスタム例外の作成
        >>> class CustomError(AppException):
        ...     def __init__(self, message: str, details: dict | None = None):
        ...         super().__init__(message, status_code=400, details=details)
        >>>
        >>> # 例外の発生
        >>> raise AppException(
        ...     "Something went wrong",
        ...     status_code=500,
        ...     details={"operation": "database_query"}
        ... )

    Note:
        - この基底クラスを直接使用するのではなく、特定の例外クラスを使用してください
        - detailsには機密情報（パスワード、トークン等）を含めないでください
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """リソースが見つからない場合に発生する例外（HTTPステータス: 404）。

    この例外は、データベースクエリやファイル検索などで要求されたリソースが
    存在しない場合に発生させます。

    Args:
        message (str): エラーメッセージ（デフォルト: "Resource not found"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: リソースIDや種類を含める

    Example:
        >>> # ユーザーが見つからない
        >>> raise NotFoundError("User not found", details={"user_id": 123})
        >>>
        >>> # ファイルが見つからない
        >>> raise NotFoundError(
        ...     "File not found",
        ...     details={"file_id": "uuid-string"}
        ... )

    Note:
        - クライアントに404レスポンスが返されます
        - セキュリティ上、存在しないリソースの詳細は明かさないよう注意
    """

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(AppException):
    """入力データのバリデーションエラーが発生した場合の例外（HTTPステータス: 422）。

    この例外は、リクエストボディやクエリパラメータの検証に失敗した場合に
    発生させます。Pydanticのバリデーションエラーとは別に、
    ビジネスロジック上のバリデーションに使用します。

    Args:
        message (str): エラーメッセージ（デフォルト: "Validation error"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: フィールド名と値、エラー理由を含める

    Example:
        >>> # メールアドレスの形式エラー
        >>> raise ValidationError(
        ...     "Invalid email format",
        ...     details={"field": "email", "value": "invalid"}
        ... )
        >>>
        >>> # ファイルサイズ超過
        >>> raise ValidationError(
        ...     "File too large",
        ...     details={"size": 15000000, "max_size": 10000000}
        ... )

    Note:
        - クライアントに422レスポンスが返されます
        - Pydanticバリデーションエラーとは異なり、ビジネスロジック用です
        - detailsに具体的なエラー箇所を含めてユーザビリティを向上させます
    """

    def __init__(self, message: str = "Validation error", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class ConflictError(AppException):
    """リソースの競合が発生した場合の例外（HTTPステータス: 409）。

    この例外は、リソースの作成・更新時に競合が発生した場合に発生させます。
    例えば、他のリソースが参照しているため削除できない場合などに使用します。

    Args:
        message (str): エラーメッセージ（デフォルト: "Conflict"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: 競合の原因となるリソース情報を含める

    Example:
        >>> # 参照が存在するため削除できない
        >>> raise ConflictError(
        ...     "カテゴリを削除できません",
        ...     details={"reason": "関連するドライバーツリーが存在します"}
        ... )

    Note:
        - クライアントに409レスポンスが返されます
        - 参照整合性エラーや重複エラーなどに使用します
    """

    def __init__(self, message: str = "Conflict", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=409, details=details)


class AuthenticationError(AppException):
    """認証に失敗した場合に発生する例外（HTTPステータス: 401）。

    この例外は、ログイン失敗、トークン無効、トークン期限切れなど、
    ユーザー認証に関する問題が発生した場合に発生させます。

    Args:
        message (str): エラーメッセージ（デフォルト: "Authentication failed"）
        details (dict[str, Any] | None): 追加の詳細情報
            注意: セキュリティ上、詳細な理由は含めない

    Example:
        >>> # パスワード不一致
        >>> raise AuthenticationError("Invalid credentials")
        >>>
        >>> # トークン無効
        >>> raise AuthenticationError(
        ...     "Invalid token",
        ...     details={"token_type": "access"}
        ... )
        >>>
        >>> # トークン期限切れ
        >>> raise AuthenticationError("Token expired")

    Note:
        - クライアントに401レスポンスが返されます
        - セキュリティ上、ユーザー存在の有無を明かさないよう注意
        - 詳細なエラー情報はログにのみ記録してください
    """

    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AppException):
    """権限不足により操作が拒否された場合に発生する例外（HTTPステータス: 403）。

    この例外は、認証は成功したが、要求された操作を実行する権限がない場合に
    発生させます。管理者専用機能へのアクセスや、他のユーザーのリソースへの
    アクセス試行などで使用します。

    Args:
        message (str): エラーメッセージ（デフォルト: "Insufficient permissions"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: 必要な権限や操作内容を含める

    Example:
        >>> # 管理者権限が必要
        >>> raise AuthorizationError(
        ...     "Superuser permission required",
        ...     details={"required_role": "superuser"}
        ... )
        >>>
        >>> # 他のユーザーのリソースへのアクセス
        >>> raise AuthorizationError(
        ...     "Cannot access another user's session",
        ...     details={"session_id": "uuid-string"}
        ... )

    Note:
        - クライアントに403レスポンスが返されます
        - 401（未認証）と403（認証済みだが権限不足）を正しく使い分けてください
        - セキュリティ上、存在しないリソースへのアクセスでも403を返すことがあります
    """

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=403, details=details)


class PayloadTooLargeError(AppException):
    """ペイロードサイズが制限を超過した場合に発生する例外（HTTPステータス: 413）。

    この例外は、アップロードされたファイルやリクエストボディのサイズが
    許可された最大サイズを超えた場合に発生させます。

    Args:
        message (str): エラーメッセージ（デフォルト: "Payload too large"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: サイズ、最大サイズを含める

    Example:
        >>> # ペイロードサイズ超過
        >>> raise PayloadTooLargeError(
        ...     "File size exceeds maximum allowed size of 50MB",
        ...     details={"size": 52428800, "max_size": 52428800}
        ... )

    Note:
        - クライアントに413レスポンスが返されます
        - detailsにサイズと最大サイズを含めてユーザーに通知します
    """

    def __init__(
        self,
        message: str = "Payload too large",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=413, details=details)


class UnsupportedMediaTypeError(AppException):
    """サポートされていないメディアタイプの場合に発生する例外（HTTPステータス: 415）。

    この例外は、アップロードされたファイルの形式やメディアタイプが
    サポートされていない場合に発生させます。

    Args:
        message (str): エラーメッセージ（デフォルト: "Unsupported media type"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: 受信したメディアタイプ、サポートされているメディアタイプを含める

    Example:
        >>> # サポートされていないファイル形式
        >>> raise UnsupportedMediaTypeError(
        ...     "File type .txt is not supported",
        ...     details={"received": ".txt", "supported": [".xlsx", ".xls"]}
        ... )

    Note:
        - クライアントに415レスポンスが返されます
        - detailsにサポートされている形式を含めてユーザーに通知します
    """

    def __init__(
        self,
        message: str = "Unsupported media type",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=415, details=details)


class DatabaseError(AppException):
    """データベース操作に失敗した場合に発生する例外（HTTPステータス: 500）。

    この例外は、データベース接続エラー、クエリ実行エラー、トランザクションエラーなど、
    データベース層で発生した予期しないエラーをラップします。

    Args:
        message (str): エラーメッセージ（デフォルト: "Database operation failed"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: 操作の種類、テーブル名を含める（機密情報は除く）

    Example:
        >>> # 接続エラー
        >>> raise DatabaseError(
        ...     "Database connection failed",
        ...     details={"operation": "connect"}
        ... )
        >>>
        >>> # トランザクションエラー
        >>> raise DatabaseError(
        ...     "Transaction commit failed",
        ...     details={"operation": "commit", "table": "users"}
        ... )

    Note:
        - クライアントに500レスポンスが返されます
        - 詳細なエラー情報（SQLクエリ等）はログにのみ記録してください
        - ユーザーには一般的なエラーメッセージのみ表示します
    """

    def __init__(self, message: str = "Database operation failed", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=500, details=details)


class ExternalServiceError(AppException):
    """外部サービスとの通信に失敗した場合に発生する例外（HTTPステータス: 502）。

    この例外は、外部API、メールサービス、ストレージサービスなど、
    外部サービスとの通信でエラーが発生した場合に発生させます。

    Args:
        message (str): エラーメッセージ（デフォルト: "External service error"）
        details (dict[str, Any] | None): 追加の詳細情報
            推奨: サービス名、操作内容を含める

    Example:
        >>> # メール送信エラー
        >>> raise ExternalServiceError(
        ...     "Failed to send email",
        ...     details={"service": "smtp", "operation": "send"}
        ... )
        >>>
        >>> # ストレージサービスエラー
        >>> raise ExternalServiceError(
        ...     "Storage service unavailable",
        ...     details={"service": "azure_blob", "operation": "upload"}
        ... )

    Note:
        - クライアントに502レスポンスが返されます
        - 外部サービスのエラーは一時的な可能性があるため、リトライを推奨
        - 外部サービスの詳細なエラーはログにのみ記録してください
    """

    def __init__(self, message: str = "External service error", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=502, details=details)
