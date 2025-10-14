"""アプリケーション全体で使用される共通スキーマ."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス."""

    message: str = Field(..., description="レスポンスメッセージ")


class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ."""

    error: str = Field(..., description="エラーメッセージ")
    details: dict[str, Any] | None = Field(None, description="追加のエラー詳細")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="エラー発生時刻")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス."""

    status: str = Field(..., description="ヘルスステータス")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="チェック時刻")
    version: str = Field(..., description="アプリケーションバージョン")


class PaginationParams(BaseModel):
    """ページネーションパラメータ."""

    skip: int = Field(0, ge=0, description="スキップするアイテム数")
    limit: int = Field(100, ge=1, le=1000, description="返却する最大アイテム数")


class PaginatedResponse(BaseModel):
    """汎用ページネーションレスポンス."""

    total: int = Field(..., ge=0, description="総アイテム数")
    skip: int = Field(..., ge=0, description="スキップしたアイテム数")
    limit: int = Field(..., ge=1, description="返却された最大アイテム数")
    items: list[Any] = Field(..., description="アイテムリスト")
