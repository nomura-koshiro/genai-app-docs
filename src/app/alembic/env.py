"""Alembic環境設定ファイル。

このファイルはAlembicマイグレーション実行時に読み込まれ、
データベース接続とマイグレーション処理を設定します。

非同期エンジン対応:
    SQLAlchemy 2.0の非同期エンジンに対応しています。
    asyncpgドライバーを使用したPostgreSQL非同期接続をサポートします。
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.models.analysis import (  # noqa: F401
    AnalysisChat,
    AnalysisDummyChartMaster,
    AnalysisDummyFormulaMaster,
    AnalysisFile,
    AnalysisGraphAxisMaster,
    AnalysisIssueMaster,
    AnalysisSession,
    AnalysisSnapshot,
    AnalysisStep,
    AnalysisValidationMaster,
)
from app.models.base import Base
from app.models.driver_tree import (  # noqa: F401
    DriverTree,
    DriverTreeCategory,
    DriverTreeDataFrame,
    DriverTreeFile,
    DriverTreeFormula,
    DriverTreeNode,
    DriverTreePolicy,
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
)
from app.models.project import Project, ProjectFile, ProjectMember  # noqa: F401

# すべてのモデルをインポートしてメタデータに登録
# これらのインポートは autogenerate 機能に必要
from app.models.user_account import UserAccount  # noqa: F401

# Alembic Config オブジェクト（alembic.ini の値にアクセス可能）
config = context.config

# Python ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータオブジェクト（autogenerate サポート用）
target_metadata = Base.metadata


def get_url() -> str:
    """データベースURLを取得します。

    環境変数 DATABASE_URL から接続URLを取得します。
    Alembicは同期ドライバー（psycopg2）を使用するため、
    asyncpg から psycopg2 に変換します。

    Returns:
        str: PostgreSQL接続URL（psycopg2ドライバー）
    """
    url = settings.DATABASE_URL
    # asyncpg ドライバーを psycopg2 に変換（Alembicは同期処理）
    return url.replace("postgresql+asyncpg", "postgresql+psycopg2")


def run_migrations_offline() -> None:
    """オフラインモードでマイグレーションを実行します。

    データベースに接続せずにSQLスクリプトを生成します。
    主にCI/CDパイプラインでのSQL生成や、レビュー用途に使用します。

    Example:
        $ alembic upgrade head --sql > migration.sql
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """マイグレーションを実行します。

    Args:
        connection: データベース接続オブジェクト
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # カラム型の変更を検出
        compare_server_default=True,  # デフォルト値の変更を検出
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期エンジンでマイグレーションを実行します。

    asyncpgドライバーを使用した非同期接続でマイグレーションを実行します。
    ただし、Alembicのマイグレーション処理自体は同期的に実行されます。
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """オンラインモードでマイグレーションを実行します。

    データベースに直接接続してマイグレーションを実行します。
    asyncio.run()を使用して非同期処理を実行します。
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
