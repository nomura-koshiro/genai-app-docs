"""データベース接続とセッション管理モジュール。

このモジュールは、SQLAlchemyの非同期エンジンとセッションファクトリを設定し、
アプリケーション全体で使用されるデータベース接続を管理します。

主な役割:
    1. **非同期エンジンの作成**: create_async_engine()で接続プールを初期化
    2. **セッションファクトリの提供**: AsyncSessionLocalでセッション生成
    3. **依存性注入用ジェネレータ**: get_db()でFastAPIエンドポイントにセッション提供
    4. **ライフサイクル管理**: init_db()とclose_db()でアプリ起動・終了時の処理

SQLAlchemy非同期パターン:
    このモジュールはSQLAlchemy 2.0の非同期APIを使用しています:
        - create_async_engine(): 非同期エンジン作成
        - AsyncSession: 非同期セッション
        - async/await: すべてのDB操作は非同期

接続プール設定:
    - pool_size: 5（通常時の接続数）
    - max_overflow: 10（ピーク時の追加接続数、最大15接続）
    - pool_recycle: 1800秒（30分ごとに接続をリサイクル）
    - pool_pre_ping: True（接続前にPINGで確認）

使用方法:
    FastAPIエンドポイントでの依存性注入:
        >>> from app.core.database import get_db
        >>> from fastapi import Depends
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>>
        >>> @app.get("/users")
        >>> async def get_users(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(SampleUser))
        >>>     return result.scalars().all()

    サービス層での直接使用:
        >>> from app.core.database import AsyncSessionLocal
        >>>
        >>> async def create_user(user_data: dict):
        >>>     async with AsyncSessionLocal() as session:
        >>>         user = SampleUser(**user_data)
        >>>         session.add(user)
        >>>         await session.commit()
        >>>         return user

テーブル作成（開発・テスト環境のみ）:
    >>> from app.core.database import init_db
    >>>
    >>> # アプリ起動時
    >>> await init_db()  # Base.metadata.create_all()を実行

Note:
    - 本番環境ではAlembicマイグレーションを使用します（init_db()は使用不可）
    - セッションは必ず async with または try-finally で確実にクローズしてください
    - トランザクション管理はサービス層またはリポジトリ層で行います
"""

import contextlib
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse

from azure.identity import DefaultAzureCredential
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging import get_logger
from app.models.base import Base

logger = get_logger(__name__)


def get_database_url() -> str:
    """環境に応じたDATABASE_URLを取得します.

    Azure Managed Identity が有効な場合、トークンを取得してパスワード部分に設定します。
    ローカル環境では通常のパスワード認証を使用します。

    Returns:
        str: データベース接続URL
    """
    if not settings.USE_MANAGED_IDENTITY:
        logger.info("データベース接続: パスワード認証を使用")
        return settings.DATABASE_URL

    logger.info("データベース接続: Azure Managed Identity を使用")

    try:
        # トークン取得
        credential = DefaultAzureCredential(managed_identity_client_id=settings.AZURE_CLIENT_ID)
        token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

        # URLをパース
        parsed = urlparse(settings.DATABASE_URL)

        # パスワード部分にトークンを設定
        # 形式: postgresql+asyncpg://username:token@host:port/database
        netloc = f"{parsed.username}:{token.token}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"

        # URL再構築
        db_url = urlunparse(parsed._replace(netloc=netloc))

        logger.info(
            "マネージドIDトークン取得成功",
            username=parsed.username,
            host=parsed.hostname,
        )
        return db_url

    except Exception as e:
        logger.error(
            "マネージドIDトークン取得失敗",
            error=str(e),
            exc_info=True,
        )
        raise


# 非同期エンジンを作成（環境別の接続プール設定）
engine = create_async_engine(
    get_database_url(),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # 接続前のPINGチェック
    pool_size=settings.DB_POOL_SIZE,  # 接続プールサイズ
    max_overflow=settings.DB_MAX_OVERFLOW,  # プールが満杯の場合の追加接続数
    pool_recycle=settings.DB_POOL_RECYCLE,  # 接続リサイクル時間（秒）
    pool_timeout=30,  # タイムアウトを明示的に設定
)

# 非同期セッションファクトリを作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI依存性注入用のデータベースセッションジェネレータ。

    非同期コンテキストマネージャーを使用してセッションを生成し、
    リクエスト処理後に自動的にクローズします。エラー発生時は
    自動的にロールバックを実行します。

    セッションライフサイクル:
        1. AsyncSessionLocal()でセッション作成
        2. yieldでエンドポイント関数にセッション提供
        3. エンドポイント処理完了後、finallyブロックでセッションクローズ
        4. 例外発生時はexceptブロックでロールバック

    トランザクション管理:
        - **読み取り専用操作**: コミット不要、自動的にセッションクローズ
        - **書き込み操作**: サービス層またはリポジトリ層で明示的にcommit()
        - **エラー時**: 自動的にrollback()が実行される

    Yields:
        AsyncSession: データベースセッションインスタンス
            - execute(): SQLクエリ実行
            - add(): オブジェクト追加
            - commit(): トランザクションコミット
            - rollback(): トランザクションロールバック

    Example:
        >>> from fastapi import APIRouter, Depends
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>> from app.core.database import get_db
        >>>
        >>> router = APIRouter()
        >>>
        >>> @router.get("/users")
        >>> async def get_users(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(SampleUser))
        >>>     users = result.scalars().all()
        >>>     return users
        >>>
        >>> @router.post("/users")
        >>> async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
        >>>     user = SampleUser(**user_data)
        >>>     db.add(user)
        >>>     await db.commit()  # 明示的にコミット
        >>>     return user

    Note:
        - FastAPIの Depends() 関数と組み合わせて使用します
        - セッションはリクエストごとに新規作成され、レスポンス後に破棄されます
        - エンドポイント関数の引数に `db: AsyncSession = Depends(get_db)` を追加するだけで使えます
        - トランザクション分離レベルはPostgreSQLのデフォルト（READ COMMITTED）
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """データベーステーブルを確認し、存在しない場合は作成します（開発・テスト環境専用）。

    Base.metadata.create_all()を実行し、すべてのモデルに対応するテーブルを作成します。
    既存のテーブルやデータは削除されません。
    本番環境では自動的にスキップされ、Alembicマイグレーションの使用を推奨します。

    実行内容:
        1. 環境チェック: ENVIRONMENT == "production" の場合はスキップ
        2. テーブル確認・作成: Base.metadata.create_all() を非同期実行（既存テーブルはスキップ）
        3. ログ出力: テーブル確認完了メッセージ

    対象テーブル:
        app/models/ ディレクトリ内のすべてのモデル:
            - sample_users: ユーザー情報
            - sample_sessions: チャットセッション
            - sample_messages: セッションメッセージ
            - sample_files: アップロードファイル

    Warning:
        **本番環境では絶対に使用しないでください**
        - スキーマ変更の履歴が残らない
        - ロールバックができない
        - テーブル削除やカラム変更は自動で行われない

    使用方法:
        >>> # アプリ起動時（main.pyのlifespan関数内）
        >>> from app.core.database import init_db
        >>>
        >>> await init_db()
        >>> # development/test環境: テーブル作成
        >>> # production環境: スキップ（警告ログ出力）

    本番環境での推奨方法:
        Alembicマイグレーションを使用:
            $ alembic revision --autogenerate -m "Create users table"
            $ alembic upgrade head

    Note:
        - 開発中はこの関数でテーブル自動作成できます
        - テーブル削除はしません（既存テーブルはそのまま）
        - app.main.pyのlifespan関数から自動的に呼び出されます
        - テスト環境では毎回テーブルを再作成することを推奨（conftest.py参照）
    """
    if settings.ENVIRONMENT == "production":
        logger.warning("本番環境ではinit_dbをスキップします。代わりにAlembicマイグレーションを使用してください。")
        return

    logger.info("データベーステーブルを確認中（存在しない場合は作成）")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@contextlib.asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession]:
    """ミドルウェアや非DIコンテキストで使用するセッションコンテキストマネージャー。

    FastAPIの依存性注入（Depends）が使用できない場面
    （例: ミドルウェア、バックグラウンドタスク）で使用します。

    Yields:
        AsyncSession: データベースセッションインスタンス

    Example:
        >>> async with get_async_session_context() as session:
        ...     result = await session.execute(select(User))
        ...     users = result.scalars().all()
        ...     await session.commit()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """データベース接続プールを解放し、すべての接続をクローズします。

    アプリケーション終了時（シャットダウン時）に呼び出され、
    すべてのデータベース接続をgracefulにクローズします。

    実行内容:
        1. engine.dispose()を呼び出し
        2. 接続プール内のすべての接続を終了
        3. 保留中のトランザクションをロールバック
        4. リソースを完全に解放

    タイミング:
        app.main.pyのlifespan関数の終了時（yieldの後）に自動実行されます。

    Example:
        >>> # アプリ終了時（main.pyのlifespan関数内）
        >>> from app.core.database import close_db
        >>>
        >>> try:
        >>>     await close_db()
        >>>     logger.info("データベース接続をクローズしました")
        >>> except Exception as e:
        >>>     logger.error(f"データベースクローズエラー: {e}")

    Note:
        - この関数を手動で呼び出す必要はありません（lifespanが自動処理）
        - Graceful shutdown: すべての接続が適切にクローズされます
        - PostgreSQLの接続数制限（max_connections）に達するのを防ぎます
    """
    await engine.dispose()
