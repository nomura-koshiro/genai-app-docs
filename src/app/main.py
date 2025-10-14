"""FastAPIアプリケーションのエントリーポイント。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middlewares import (
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    PrometheusMetricsMiddleware,
    RateLimitMiddleware,
)
from app.api.routes import agents, files
from app.config import settings
from app.core.cache import cache_manager
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.database import close_db, init_db

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフスパンマネージャー。"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL}")

    # Initialize database
    await init_db()
    print("Database initialized")

    # Initialize Redis cache
    if settings.REDIS_URL:
        await cache_manager.connect()
        print(f"Redis cache connected: {settings.REDIS_URL}")
    else:
        print("Redis cache disabled (REDIS_URL not configured)")

    yield

    # Shutdown
    print("Shutting down...")

    # Close Redis connection
    if settings.REDIS_URL:
        await cache_manager.disconnect()
        print("Redis cache disconnected")

    await close_db()
    print("Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    # AI Agent Application API

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
    terms_of_service="https://example.com/terms/",
)

# Custom exception handler for AppException
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """カスタムアプリケーション例外を処理します。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


# Custom middlewares (order matters - last added is executed first)
app.add_middleware(PrometheusMetricsMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(files.router, prefix="/api/files", tags=["files"])


@app.get("/")
async def root():
    """ルートエンドポイント。"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント。"""
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/metrics")
async def metrics():
    """Prometheusメトリクスエンドポイント。"""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    from starlette.responses import Response

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def main():
    """CLI用のエントリーポイント。"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
