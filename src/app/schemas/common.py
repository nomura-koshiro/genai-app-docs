"""アプリケーション全体で使用される共通Pydanticスキーマ。

このモジュールは、複数のエンドポイントで共通利用されるスキーマを定義します。
エラーレスポンス、ヘルスチェック、ページネーション等の汎用的な機能を提供します。

主なスキーマ:
    - MessageResponse: 汎用メッセージレスポンス
    - ErrorResponse: エラー情報レスポンス
    - HealthResponse: ヘルスチェックレスポンス
    - PaginationParams: ページネーションリクエストパラメータ
    - PaginatedResponse: ページネーション付きレスポンス

使用方法:
    >>> from app.schemas.common import ErrorResponse, PaginationParams
    >>> from fastapi import HTTPException
    >>>
    >>> # エラーレスポンス
    >>> error = ErrorResponse(
    ...     error="Resource not found",
    ...     details={"resource_id": "123"}
    ... )
    >>>
    >>> # ページネーション
    >>> params = PaginationParams(skip=0, limit=10)
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """汎用メッセージレスポンススキーマ。

    シンプルな成功メッセージを返す際に使用します。

    Attributes:
        message (str): レスポンスメッセージ

    Example:
        >>> response = MessageResponse(message="Operation successful")
        >>> print(response.message)
        Operation successful
    """

    message: str = Field(..., description="レスポンスメッセージ")


class ProblemDetails(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs準拠のエラースキーマ。

    HTTPエラーレスポンスの標準形式を提供します。
    RFC 9457仕様に準拠し、相互運用性とデバッグ性を向上させます。

    Reference:
        https://www.rfc-editor.org/rfc/rfc9457.html

    Attributes:
        type (str): 問題タイプを識別するURI
            - デフォルト: "about:blank"（一般的なHTTPステータスコードエラー）
            - カスタムURI: "https://api.example.com/problems/validation-error"
        title (str): 人間が読める短い要約（HTTPステータスコードに対応）
            例: "Not Found", "Validation Error", "Unauthorized"
        status (int): HTTPステータスコード（100-599）
        detail (str | None): この問題の具体的な説明
            例: "User with ID 12345 was not found"
        instance (str | None): この問題発生の特定のURIインスタンス
            例: "/api/v1/users/12345"

    Example:
        >>> # 基本的な使用例
        >>> problem = ProblemDetails(
        ...     type="about:blank",
        ...     title="Not Found",
        ...     status=404,
        ...     detail="User with ID 12345 was not found",
        ...     instance="/api/v1/users/12345"
        ... )
        >>>
        >>> # カスタム問題タイプの例
        >>> problem = ProblemDetails(
        ...     type="https://api.example.com/problems/validation-error",
        ...     title="Validation Error",
        ...     status=422,
        ...     detail="Email format is invalid",
        ...     instance="/api/v1/users",
        ...     field="email",  # 追加のカスタムフィールド
        ...     value="invalid"
        ... )

    Note:
        - Content-Type: application/problem+json を使用します
        - 拡張フィールド（field, valueなど）の追加が可能です
        - 機密情報（パスワード、トークン等）を含めないでください
    """

    type: str = Field(
        default="about:blank",
        description="問題タイプを識別するURI"
    )
    title: str = Field(
        ...,
        description="人間が読める短い要約"
    )
    status: int = Field(
        ...,
        ge=100,
        le=599,
        description="HTTPステータスコード"
    )
    detail: str | None = Field(
        None,
        description="この問題の具体的な説明"
    )
    instance: str | None = Field(
        None,
        description="この問題発生の特定のURIインスタンス"
    )

    model_config = {"extra": "allow"}  # RFC 9457は追加フィールドを許可


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンススキーマ。

    アプリケーションの正常性を確認するためのレスポンスです。
    監視システムやロードバランサーからの定期チェックに使用されます。

    Attributes:
        status (str): ヘルスステータス（"healthy", "unhealthy"）
        timestamp (datetime): チェック実行時刻（UTC、自動設定）
        version (str): アプリケーションバージョン

    Example:
        >>> response = HealthResponse(
        ...     status="healthy",
        ...     version="1.0.0"
        ... )

    Note:
        - GET /health エンドポイントで使用されます
        - 監視システム（Prometheus, Datadog等）との連携に活用できます
    """

    status: str = Field(..., description="ヘルスステータス")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="チェック時刻")
    version: str = Field(..., description="アプリケーションバージョン")


class PaginationParams(BaseModel):
    """ページネーションリクエストパラメータスキーマ。

    リスト取得APIでのページング制御に使用します。

    Attributes:
        skip (int): スキップするアイテム数（オフセット、デフォルト: 0）
            - 最小値: 0
        limit (int): 返却する最大アイテム数（デフォルト: 100）
            - 最小値: 1
            - 最大値: 1000

    Example:
        >>> # 最初の10件取得
        >>> params = PaginationParams(skip=0, limit=10)
        >>>
        >>> # 11件目から20件目まで取得
        >>> params = PaginationParams(skip=10, limit=10)

    Note:
        - limitは1000件までに制限されています
        - 大量データ取得時はページングを使用してください
    """

    skip: int = Field(0, ge=0, description="スキップするアイテム数")
    limit: int = Field(100, ge=1, le=1000, description="返却する最大アイテム数")


class PaginatedResponse(BaseModel):
    """汎用ページネーションレスポンススキーマ。

    ページング付きのリストレスポンスに使用します。

    Attributes:
        total (int): 総アイテム数（フィルタ適用後）
        skip (int): スキップされたアイテム数
        limit (int): 返却された最大アイテム数
        items (list[Any]): アイテムリスト

    Example:
        >>> response = PaginatedResponse(
        ...     total=100,
        ...     skip=0,
        ...     limit=10,
        ...     items=[{"id": 1}, {"id": 2}, ...]
        ... )

    Note:
        - 実際の使用時はitemsの型を具体的なモデルに置き換えてください
        - 例: list[UserResponse], list[FileInfo]
    """

    total: int = Field(..., ge=0, description="総アイテム数")
    skip: int = Field(..., ge=0, description="スキップしたアイテム数")
    limit: int = Field(..., ge=1, description="返却された最大アイテム数")
    items: list[Any] = Field(..., description="アイテムリスト")
