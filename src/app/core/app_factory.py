"""FastAPIアプリケーション生成ファクトリー。

このモジュールは、FastAPIアプリケーションインスタンスの作成と設定を行います。

主な役割:
    1. **FastAPIアプリ作成**: アプリケーションメタデータの設定
    2. **ミドルウェア登録**: CORS、ロギング、レート制限、メトリクスなど
    3. **ルーター登録**: API v1エンドポイントと基本エンドポイントの登録
    4. **例外ハンドラー登録**: カスタム例外処理の設定

Usage:
    >>> from app.core.app_factory import create_app
    >>>
    >>> app = create_app()
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.core import register_exception_handlers
from app.api.middlewares import (
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    PrometheusMetricsMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.routes.system import health, metrics, root
from app.api.routes.v1 import sample_agents, sample_files, sample_sessions, sample_users
from app.core.config import settings
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    """FastAPIアプリケーションインスタンスを作成します。

    ライフサイクル管理、ミドルウェア、ルーター、例外ハンドラーを含む
    完全に設定されたFastAPIアプリケーションを生成します。

    アーキテクチャ:
        リクエスト
            ↓
        [CORS Middleware] ← クロスオリジン制御
            ↓
        [RateLimitMiddleware] ← 100req/min制限
            ↓
        [LoggingMiddleware] ← 構造化ログ記録
            ↓
        [ErrorHandlerMiddleware] ← エラーハンドリング
            ↓
        [PrometheusMetricsMiddleware] ← メトリクス収集
            ↓
        [Router] ← エンドポイント処理
            ↓
        レスポンス

    Returns:
        FastAPI: 完全に設定されたFastAPIアプリケーションインスタンス

    Example:
        >>> from app.core.app_factory import create_app
        >>> import uvicorn
        >>>
        >>> app = create_app()
        >>> uvicorn.run(app, host="0.0.0.0", port=8000)

    Note:
        - ミドルウェアの実行順序は登録の逆順です（後に追加したものが先に実行される）
        - lifespanコンテキストマネージャーでアプリの起動・終了処理を管理しています
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="""
    # AIエージェントアプリケーション API

    LangChain/LangGraphを使用したAIエージェントアプリケーションのバックエンドAPI。

    ## 主な機能

    - **AIエージェントとのチャット**: LangGraphによる高度な会話エンジン
    - **セッション管理**: 会話履歴の保存と取得
    - **ファイル処理**: ファイルのアップロード・ダウンロード
    - **認証・認可**: JWT認証とロールベース制御
    - **モニタリング**: Prometheusメトリクス収集

    ## 認証

    ほとんどのエンドポイントはゲストアクセス可能ですが、一部の機能では認証が必要です。
    認証が必要な場合は、`Authorization: Bearer <token>` ヘッダーを含めてください。

    ## レート制限

    APIリクエストは100リクエスト/分に制限されています。
    """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "開発チーム",
            "email": "nomura.koshiro@gmail.com",
        },
        license_info={
            "name": "MIT",
        },
    )

    # 例外ハンドラーを登録
    register_exception_handlers(app)

    # カスタムミドルウェアを登録（実行順序は登録の逆順 - 後に追加されたものが先に実行される）
    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.RATE_LIMIT_CALLS,
        period=settings.RATE_LIMIT_PERIOD,
    )

    # CORSミドルウェア（config.pyで必ずALLOWED_ORIGINSが設定されている）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or [],  # 型安全性のためのフォールバック
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Accept", "Content-Type", "Authorization", "X-API-Key"],
    )

    # セキュリティヘッダーミドルウェア
    # すべてのレスポンスにセキュリティヘッダーを追加
    # （X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS）
    app.add_middleware(SecurityHeadersMiddleware)

    # APIバージョニング付きルーターを登録
    app.include_router(sample_users.router, prefix="/api/v1/sample-users", tags=["sample-users"])
    app.include_router(sample_agents.router, prefix="/api/v1/sample-agents", tags=["sample-agents"])
    app.include_router(sample_sessions.router, prefix="/api/v1/sample-sessions", tags=["sample-sessions"])
    app.include_router(sample_files.router, prefix="/api/v1/sample-files", tags=["sample-files"])

    # 基本エンドポイントを登録
    app.include_router(root.router, tags=["root"])
    app.include_router(health.router, tags=["health"])
    app.include_router(metrics.router, tags=["metrics"])

    return app
