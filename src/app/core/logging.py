"""アプリケーションのロギング設定."""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


class ColoredFormatter(logging.Formatter):
    """コンソール出力用のカラーログフォーマッター."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードを色付きでフォーマット."""
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """構造化ログ用のJSONフォーマッター."""

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式でフォーマット."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 追加のフィールド
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # 例外情報
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    """アプリケーションのロギング設定をセットアップ."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # 本番環境ではJSON形式、開発環境ではカラー出力
    if settings.ENVIRONMENT == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_handler.setFormatter(ColoredFormatter(console_format))

    root_logger.addHandler(console_handler)

    # File handler for production - JSON形式で出力
    if settings.ENVIRONMENT == "production":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # JSON形式のログファイル
        json_file_handler = logging.FileHandler(log_dir / "app.json.log")
        json_file_handler.setLevel(logging.INFO)
        json_file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_file_handler)

        # エラーログファイル（JSON形式）
        error_file_handler = logging.FileHandler(log_dir / "error.json.log")
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_file_handler)

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """指定された名前のロガーインスタンスを取得.

    Args:
        name: ロガー名（通常は __name__）

    Returns:
        ロガーインスタンス
    """
    return logging.getLogger(name)
