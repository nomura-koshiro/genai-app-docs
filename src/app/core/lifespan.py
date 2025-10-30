"""アプリケーションのライフサイクル管理。

このモジュールは、FastAPIアプリケーションの起動時と終了時に実行される処理を管理します。

主な役割:
    1. **起動時処理**: データベース初期化、Redis接続、設定情報ロギング
    2. **終了時処理**: Redis切断、データベース接続クローズ

Usage:
    >>> from app.core.lifespan import lifespan
    >>> from fastapi import FastAPI
    >>>
    >>> app = FastAPI(lifespan=lifespan)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import cache_manager
from app.core.config import get_env_file, settings
from app.core.database import close_db, init_db
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル（起動・終了）を管理するコンテキストマネージャー。

    FastAPIの lifespan パラメータに渡すことで、アプリケーションの起動時と
    終了時に実行される処理を定義します。

    起動時の処理（yieldの前）:
        1. ログ出力: アプリ名、バージョン、環境、設定ファイル、DB接続先
        2. データベース初期化: init_db()を呼び出し
        3. Redis接続: REDIS_URLが設定されていれば接続

    終了時の処理（yieldの後）:
        1. Redis切断: 接続していた場合はgracefulに切断
        2. データベース接続クローズ: 全てのコネクションプールを解放

    Args:
        app (FastAPI): FastAPIアプリケーションインスタンス
            - この引数は使用されませんが、FastAPIの仕様で必須です

    Yields:
        None: アプリケーション実行中（リクエスト処理中）

    Example:
        >>> # FastAPIアプリケーション作成時に指定
        >>> app = FastAPI(lifespan=lifespan)
        >>>
        >>> # 起動時のログ例
        >>> # INFO - Starting camp-backend v0.1.0
        >>> # INFO - Environment: development
        >>> # INFO - Loaded config from: .env.local, .env
        >>> # INFO - Database: ***@localhost:5432/app_db
        >>> # INFO - Database initialized
        >>> # INFO - Redis cache connected

    Note:
        - この関数は @asynccontextmanager デコレータで装飾されています
        - yieldの前後でtry-exceptを使い、エラー時もgracefulにシャットダウンします
        - データベースURLのパスワード部分は***でマスクされます（セキュリティ）
        - 本番環境では init_db() はスキップされ、Alembicマイグレーションを使用します
    """
    # アプリケーション起動処理
    logger.info(
        "アプリケーション起動",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
    )
    logger.info("環境情報", environment=settings.ENVIRONMENT)

    env_files = get_env_file()

    if env_files:
        logger.info("設定ファイル読み込み", env_files=list(env_files))

    # データベースURLからパスワードをマスク
    db_url_safe = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***"
    logger.info("データベース接続先", db_url=f"***@{db_url_safe}")

    # データベーステーブルを確認・作成
    await init_db()
    logger.info("データベーステーブルの確認が完了しました")

    # Redisキャッシュを初期化
    if settings.REDIS_URL:
        await cache_manager.connect()
        logger.info("Redisキャッシュに接続しました")
    else:
        logger.info("Redisキャッシュが無効です（REDIS_URLが設定されていません）")

    # ✨ 追加: Azure AD認証の初期化（本番モードのみ）
    if settings.AUTH_MODE == "production":
        try:
            from app.core.security.azure_ad import initialize_azure_scheme

            await initialize_azure_scheme()
            logger.info("Azure AD認証スキームを初期化しました")
        except ImportError:
            logger.error("fastapi-azure-authがインストールされていません")
        except Exception as e:
            logger.error(
                "Azure AD初期化エラー",
                error_type=type(e).__name__,
                error_message=str(e),
            )
    else:
        logger.info(f"認証モード: {settings.AUTH_MODE}（開発モード）")

    yield

    # アプリケーションシャットダウン処理
    logger.info("シャットダウン中...")

    # Redis接続を切断
    try:
        if settings.REDIS_URL:
            await cache_manager.disconnect()
            logger.info("Redisキャッシュから切断しました")
    except Exception as e:
        logger.exception("Redis切断エラー", error_type=type(e).__name__, error_message=str(e))

    try:
        await close_db()
        logger.info("データベース接続をクローズしました")
    except Exception as e:
        logger.exception("データベースクローズエラー", error_type=type(e).__name__, error_message=str(e))
