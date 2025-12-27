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
    LoggingMiddleware,
    PrometheusMetricsMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.routes.system import health_router, metrics_router, root_router
from app.api.routes.v1 import (
    admin_category_router,
    admin_issue_router,
    admin_role_router,
    admin_validation_router,
    analysis_sessions_router,
    analysis_templates_router,
    dashboard_router,
    driver_tree_files_router,
    driver_tree_nodes_router,
    driver_tree_trees_router,
    project_files_router,
    project_members_router,
    projects_router,
    user_accounts_router,
)
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
        [PrometheusMetricsMiddleware] ← メトリクス収集
            ↓
        [Router] ← エンドポイント処理
            ↓
        [Exception Handlers (RFC 9457)] ← エラーハンドリング
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
    # Swagger UIのOAuth設定（本番モードのみ）
    swagger_ui_init_oauth = None
    if settings.AUTH_MODE == "production":
        swagger_ui_init_oauth = {
            "usePkceWithAuthorizationCodeGrant": True,
            "clientId": settings.AZURE_OPENAPI_CLIENT_ID,
            "scopes": f"api://{settings.AZURE_CLIENT_ID}/access_as_user",
        }

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        # レスポンスでcamelCaseを使用（alias_generatorで設定されたエイリアスを使用）
        response_model_by_alias=True,
        description=f"""
    # camp-backend

    LangChain/LangGraphを使用したAIエージェントアプリケーションのバックエンドAPI。

    ## 認証モード: {settings.AUTH_MODE}

    {"### Azure AD認証が有効です" if settings.AUTH_MODE == "production" else "### 開発モード認証（モック）"}

    ## 主な機能

    - **AIエージェントとのチャット**: LangGraphによる高度な会話エンジン
    - **セッション管理**: 会話履歴の保存と取得
    - **ファイル処理**: ファイルのアップロード・ダウンロード
    - **認証・認可**: {"Azure AD認証" if settings.AUTH_MODE == "production" else "JWT認証"} とロールベース制御
    - **モニタリング**: Prometheusメトリクス収集

    ## 認証

    ほとんどのエンドポイントはゲストアクセス可能ですが、一部の機能では認証が必要です。
    認証が必要な場合は、`Authorization: Bearer <token>` ヘッダーを含めてください。

    ### 開発環境での認証方法

    詳細は [クイックスタートガイド](docs/developer-guide/01-getting-started/05-quick-start.md) を参照してください。

    1. 右上の **「Authorize」** ボタンをクリック
    2. トークンに `mock-access-token-dev-12345` を入力
    3. **「Authorize」** をクリック

    ※ 初回は `.\\scripts\\start-postgres.ps1` でDB起動後、
    `uv run python scripts/setup_dev_admin.py` を実行して
    開発ユーザー（SystemAdmin権限付き）を作成してください。

    ## レート制限

    APIリクエストは100リクエスト/分に制限されています。
    """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_oauth2_redirect_url="/oauth2-redirect" if settings.AUTH_MODE == "production" else None,
        swagger_ui_init_oauth=swagger_ui_init_oauth,
        contact={
            "name": "開発チーム",
            "email": "koshiro.nomura@accenture.com",
        },
        license_info={
            "name": "MIT",
        },
    )

    # 例外ハンドラーを登録（RFC 9457準拠）
    register_exception_handlers(app)

    # カスタムミドルウェアを登録（実行順序は登録の逆順 - 後に追加されたものが先に実行される）
    app.add_middleware(PrometheusMetricsMiddleware)
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

    # Azure AD認証用ユーザー管理API
    app.include_router(user_accounts_router, prefix="/api/v1", tags=["user_account"])

    # 管理機能API
    app.include_router(admin_category_router, prefix="/api/v1", tags=["admin-category"])
    app.include_router(admin_role_router, prefix="/api/v1", tags=["admin-role"])
    app.include_router(admin_validation_router, prefix="/api/v1", tags=["admin-validation"])
    app.include_router(admin_issue_router, prefix="/api/v1", tags=["admin-issue"])

    # ダッシュボードAPI
    app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])

    # プロジェクト管理API
    app.include_router(projects_router, prefix="/api/v1", tags=["project"])

    # プロジェクトメンバー管理API
    app.include_router(project_members_router, prefix="/api/v1", tags=["project-member"])

    # プロジェクトファイル管理API
    app.include_router(project_files_router, prefix="/api/v1", tags=["project-file"])

    # Analysis API - テンプレート
    app.include_router(analysis_templates_router, prefix="/api/v1", tags=["analysis-template"])

    # Analysis API - セッション
    app.include_router(analysis_sessions_router, prefix="/api/v1", tags=["analysis-session"])

    # Driver Tree API - ファイル管理
    app.include_router(driver_tree_files_router, prefix="/api/v1", tags=["driver-tree-file"])

    # Driver Tree API - ツリー管理
    app.include_router(driver_tree_trees_router, prefix="/api/v1", tags=["driver-tree"])

    # Driver Tree API - ノード管理
    app.include_router(driver_tree_nodes_router, prefix="/api/v1", tags=["driver-tree-node"])

    # 基本エンドポイントを登録
    app.include_router(root_router, tags=["root"])
    app.include_router(health_router, tags=["health"])
    app.include_router(metrics_router, tags=["metrics"])

    return app
