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


class ErrorResponse(BaseModel):
    """エラー情報レスポンススキーマ。

    APIエラー発生時の詳細情報を返します。FastAPIの例外ハンドラーで使用されます。

    Attributes:
        error (str): エラーメッセージ
        details (dict[str, Any] | None): 追加のエラー詳細情報（オプション）
        timestamp (datetime): エラー発生時刻（UTC、自動設定）

    Example:
        >>> from datetime import datetime
        >>> error = ErrorResponse(
        ...     error="Validation failed",
        ...     details={"field": "email", "reason": "invalid format"},
        ...     timestamp=datetime.utcnow()
        ... )

    Note:
        - FastAPIのエラーハンドラーで自動的に使用されます
        - detailsにはデバッグ情報を含めますが、機密情報は含めないでください
    """

    error: str = Field(..., description="エラーメッセージ")
    details: dict[str, Any] | None = Field(None, description="追加のエラー詳細")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="エラー発生時刻")


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
