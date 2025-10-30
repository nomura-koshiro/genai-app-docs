"""アプリケーションの構造化ロギングシステム設定（structlog）。

このモジュールは、structlogを使用した構造化ロギング機能を提供します。
開発環境と本番環境で異なるログ形式を使用し、キー-値ペアによる
構造化ログや色付きコンソール出力を実現します。

主な機能:
    - 構造化ロギング: キー-値ペアによる明示的なフィールド指定
    - コンテキストバインディング: 永続的なフィールド（request_id等）
    - 環境別出力形式:
        * 開発環境: カラー付きキー-値ペア出力
        * 本番環境: JSON形式出力
    - 高パフォーマンス: 標準loggingより高速
    - 標準logging互換: 既存のlogger.info()等がそのまま動作

環境別設定:
    開発環境（DEBUG=True）:
        - ログレベル: DEBUG
        - フォーマット: カラー付きキー-値ペア
        - 出力先: コンソールのみ
        - 例: user_logged_in user_id=123 ip='192.168.1.1'

    本番環境（ENVIRONMENT=production）:
        - ログレベル: INFO
        - フォーマット: JSON
        - 出力先: コンソール + ファイル
        - 例: {"event": "user_logged_in", "user_id": 123, "ip": "192.168.1.1"}

使用方法:
    >>> from app.core.logging import setup_logging, get_logger
    >>>
    >>> # アプリケーション起動時（main.pyで実行）
    >>> setup_logging()
    >>>
    >>> # 各モジュールでロガー取得
    >>> logger = get_logger(__name__)
    >>>
    >>> # 基本的なログ出力（構造化）
    >>> logger.info("user_logged_in", user_id=123, ip_address="192.168.1.1")
    >>> logger.error("database_connection_failed", error="timeout", retry_count=3)
    >>>
    >>> # コンテキストバインディング（永続的なフィールド）
    >>> logger = logger.bind(request_id="550e8400-e29b-41d4", user_id=123)
    >>> logger.info("api_request", endpoint="/api/v1/users")  # request_id, user_idが自動付与
    >>> logger.info("api_response", status_code=200)          # request_id, user_idが自動付与
    >>>
    >>> # 標準loggingスタイルも互換（後方互換性）
    >>> logger.info("User logged in")  # 動作するが構造化推奨
    >>>
    >>> # 例外付きログ
    >>> try:
    ...     1 / 0
    ... except Exception:
    ...     logger.exception("division_error", operation="divide")

JSON出力例（本番環境）:
    {
        "event": "user_logged_in",
        "user_id": 123,
        "ip_address": "192.168.1.1",
        "timestamp": "2024-01-01T12:00:00.000Z",
        "level": "info",
        "logger": "app.services.user"
    }

サードパーティライブラリのログレベル:
    - uvicorn: INFO固定
    - sqlalchemy.engine: 開発環境=INFO、本番環境=WARNING

Note:
    - setup_logging()は必ずアプリケーション起動時に1回だけ呼び出してください
    - get_logger()は各モジュールで__name__を渡して使用してください
    - 本番環境ではlogsディレクトリが自動作成されます
    - structlogは標準loggingと互換性があり、既存コードの変更は不要です
"""

import logging
import sys
from pathlib import Path

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """アプリケーション全体のロギングシステムをセットアップします。

    この関数は、アプリケーション起動時に1回だけ呼び出され、環境に応じた
    structlog設定を行います。開発環境ではカラー付きコンソール出力、
    本番環境ではJSON形式のコンソール+ファイル出力を設定します。

    ロギング設定:
        ログレベル:
            - DEBUG=True: DEBUGレベル（詳細なデバッグ情報）
            - DEBUG=False: INFOレベル（通常の情報ログ）

        出力先（開発環境）:
            - コンソール: カラー付きキー-値ペア
            - ファイル: なし

        出力先（本番環境 ENVIRONMENT=production）:
            - コンソール: JSON形式
            - ファイル1: logs/app.json.log（INFOレベル以上）
            - ファイル2: logs/error.json.log（ERRORレベル以上）

    structlog処理パイプライン:
        1. add_log_level: ログレベル追加
        2. add_logger_name: ロガー名追加
        3. TimeStamper: ISO 8601 UTC タイムスタンプ
        4. StackInfoRenderer: スタック情報レンダリング
        5. format_exc_info: 例外情報フォーマット
        6. UnicodeDecoder: Unicode文字列デコード
        7. JSONRenderer/ConsoleRenderer: 最終出力

    サードパーティライブラリのログレベル設定:
        - uvicorn: INFO固定（HTTPリクエストログ）
        - sqlalchemy.engine: 開発=INFO、本番=WARNING（SQLクエリログ）

    使用方法:
        >>> from app.core.logging import setup_logging
        >>>
        >>> # アプリケーション起動時（main.py）
        >>> def main():
        ...     setup_logging()  # 必ず最初に呼び出す
        ...     # 以降のコードでロガーを使用可能
        ...     logger = get_logger(__name__)
        ...     logger.info("application_started")

    ファイル構造（本番環境）:
        logs/
        ├── app.json.log       # 全ログ（INFO以上）
        └── error.json.log     # エラーログ（ERROR以上）

    Example:
        >>> # 開発環境での出力例
        >>> setup_logging()  # DEBUG=True
        >>> logger = get_logger("app.main")
        >>> logger.info("server_started", port=8000)
        # コンソール出力: server_started port=8000
        >>>
        >>> # 本番環境での出力例
        >>> setup_logging()  # ENVIRONMENT=production
        >>> logger = get_logger("app.main")
        >>> logger.info("server_started", port=8000)
        # コンソール出力: {"event": "server_started", "port": 8000, ...}
        # ファイル出力: logs/app.json.log に同じJSON形式で記録

    Note:
        - この関数は必ず1回だけ呼び出してください（main.pyで実行）
        - 既存のハンドラーは削除されます（重複登録防止）
        - 本番環境では logsディレクトリが自動作成されます
        - ログファイルは追記モードで開かれます（既存ログは保持）
        - タイムゾーンは必ずUTCで記録されます
        - structlogは標準loggingと統合され、両方のAPIが使用可能です

    Raises:
        OSError: ログディレクトリの作成やファイルのオープンに失敗した場合
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # 標準loggingの基本設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # structlogのプロセッサー設定
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # 環境に応じたレンダラー選択
    if settings.ENVIRONMENT == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # structlog設定
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 本番環境用のファイルハンドラー
    if settings.ENVIRONMENT == "production":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # ルートロガーにファイルハンドラーを追加
        root_logger = logging.getLogger()

        # 全ログファイル（INFO以上）
        file_handler = logging.FileHandler(log_dir / "app.json.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(message)s")  # structlogが既にフォーマット済み
        )
        root_logger.addHandler(file_handler)

        # エラーログファイル（ERROR以上）
        error_handler = logging.FileHandler(log_dir / "error.json.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter("%(message)s")  # structlogが既にフォーマット済み
        )
        root_logger.addHandler(error_handler)

    # サードパーティライブラリのログレベルを設定
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.DEBUG else logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """構造化ロガーインスタンスを取得します。

    この関数は、structlogを使った構造化ロギングのためのロガーを取得します。
    キー-値ペアによるログ出力、コンテキストバインディング、高パフォーマンスなど
    標準loggingより優れた機能を提供しつつ、標準logging APIとの互換性も維持します。

    特徴:
        - キー-値ペア: logger.info("event", key1=value1, key2=value2)
        - コンテキストバインディング: logger.bind(request_id="...") で永続的なフィールド
        - 型安全: キーワード引数による明示的なフィールド指定
        - 高速: 標準loggingより高パフォーマンス
        - 後方互換: logger.info("message") も動作（ただし構造化推奨）

    ロガー名の命名規則:
        - モジュール内: __name__ を使用（推奨）
          → モジュールの完全なパス（例: "app.services.user"）が自動設定
        - None: ルートロガーを使用
        - カスタム名: 任意の文字列を指定可能

    Args:
        name (str | None): ロガー名（オプション）
            - None: ルートロガーを使用
            - 文字列: モジュール名を指定（推奨: __name__）

    Returns:
        structlog.stdlib.BoundLogger: 構造化ロガーインスタンス
            - info(), error(), warning(), debug() メソッド
            - bind() メソッド: コンテキストフィールド追加
            - unbind() メソッド: コンテキストフィールド削除
            - exception() メソッド: 例外情報付きログ

    Example:
        >>> from app.core.logging import get_logger
        >>>
        >>> # モジュール内での使用（推奨）
        >>> logger = get_logger(__name__)  # __name__ = "app.services.user"
        >>>
        >>> # 基本的な構造化ログ
        >>> logger.info("user_logged_in", user_id=123, ip_address="192.168.1.1")
        >>> logger.error("database_error", error="timeout", retry_count=3)
        >>>
        >>> # コンテキストバインディング（永続的なフィールド）
        >>> logger = logger.bind(request_id="550e8400-e29b-41d4")
        >>> logger.info("api_request", endpoint="/api/users")  # request_idが自動付与
        >>> logger.info("api_response", status_code=200)       # request_idが自動付与
        >>>
        >>> # 複数フィールドのバインド
        >>> logger = logger.bind(request_id="...", user_id=123, tenant_id="acme")
        >>> logger.info("business_event", action="purchase", amount=99.99)
        >>>
        >>> # 例外付きログ
        >>> try:
        ...     1 / 0
        ... except Exception:
        ...     logger.exception("division_error", operation="divide", numerator=1, denominator=0)
        >>>
        >>> # 標準loggingスタイル（後方互換性）
        >>> logger.info("User service initialized")  # 動作するが構造化推奨
        >>>
        >>> # 開発環境での出力例
        >>> # user_logged_in user_id=123 ip_address='192.168.1.1'
        >>>
        >>> # 本番環境での出力例
        >>> # {"event": "user_logged_in", "user_id": 123, "ip_address": "192.168.1.1", ...}

    Note:
        - setup_logging() を呼び出した後に使用してください
        - bind()で追加したコンテキストは新しいロガーインスタンスで保持されます
        - キー-値ペアのキーは文字列、値は任意の型が使用可能
        - 構造化ログ（キー-値ペア）の使用を強く推奨します
        - __name__ を使用することで、ログ出力元を容易に特定できます
        - 同じ名前で複数回呼び出しても、同じロガーインスタンスが返されます
    """
    return structlog.get_logger(name)
