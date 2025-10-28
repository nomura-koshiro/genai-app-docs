"""ヘルスチェックエンドポイント。

このモジュールは、アプリケーションとその依存サービス（データベース、Redis）の
正常性を確認するためのヘルスチェックエンドポイントを提供します。

Endpoints:
    GET /health: アプリケーションヘルスチェック
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core.cache import cache_manager
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    """ヘルスチェックエンドポイント - アプリケーションとその依存サービスの正常性を確認します。

    データベース（PostgreSQL）とRedisキャッシュの接続状態を検証し、
    アプリケーション全体の健全性を報告します。ロードバランサーや
    監視システム（Kubernetes liveness/readiness probe、Datadog等）から
    定期的に呼び出されることを想定しています。

    チェック項目:
        1. **データベース接続**: SELECT 1 クエリで接続確認
           - 成功: "healthy"
           - 失敗: "unhealthy"
        2. **Redisキャッシュ**: PINGコマンドで接続確認
           - REDIS_URL未設定: "disabled"
           - 接続成功: "healthy"
           - 接続失敗: "unhealthy"
        3. **総合ステータス**:
           - DBが正常: "healthy"
           - DBが異常: "degraded"（Redisの状態に関わらず）

    Returns:
        dict: ヘルスチェック結果
            - status (str): 総合ステータス（"healthy" | "degraded"）
            - timestamp (str): チェック実行時刻（ISO 8601形式、UTC）
            - version (str): アプリケーションバージョン
            - environment (str): 実行環境（development | staging | production）
            - services (dict): 各サービスの個別ステータス
                - database (str): "healthy" | "unhealthy"
                - redis (str): "healthy" | "unhealthy" | "disabled"

    Example:
        >>> # 正常時のレスポンス
        >>> $ curl http://localhost:8000/health
        >>> {
        >>>   "status": "healthy",
        >>>   "timestamp": "2025-10-16T14:30:00.000000Z",
        >>>   "version": "0.1.0",
        >>>   "environment": "development",
        >>>   "services": {
        >>>     "database": "healthy",
        >>>     "redis": "healthy"
        >>>   }
        >>> }
        >>>
        >>> # Redis未設定時のレスポンス
        >>> {
        >>>   "status": "healthy",
        >>>   "services": {
        >>>     "database": "healthy",
        >>>     "redis": "disabled"
        >>>   }
        >>> }

    Note:
        - 認証不要のパブリックエンドポイントです
        - データベース接続失敗時はエラーログを出力します
        - Kubernetesのliveness/readiness probeに最適です
        - タイムアウト: データベースクエリは接続プールの設定に依存（デフォルト30秒）
    """
    # データベースヘルスチェック
    db_status = "healthy"
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break
    except Exception as e:
        logger.error(f"データベースヘルスチェックに失敗しました: {e}")
        db_status = "unhealthy"

    # Redisヘルスチェック
    redis_client = cache_manager._redis
    redis_status = "healthy" if settings.REDIS_URL and redis_client is not None else "disabled"
    if redis_status == "healthy" and redis_client is not None:
        try:
            await redis_client.ping()
        except Exception as e:
            logger.error(f"Redisヘルスチェックに失敗しました: {e}")
            redis_status = "unhealthy"

    # 総合ステータス
    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": db_status,
            "redis": redis_status,
        },
    }
