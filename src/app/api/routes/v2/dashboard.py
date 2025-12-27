"""ダッシュボードAPI v2エンドポイント。

v1と同じ実装を使用（パス変更なし）。
"""

from app.api.routes.v1.dashboard.dashboard import router as dashboard_router

__all__ = ["dashboard_router"]
