"""ダッシュボードAPIパッケージ。"""

from app.api.routes.v1.dashboard.dashboard import router as dashboard_router

__all__ = ["dashboard_router"]
