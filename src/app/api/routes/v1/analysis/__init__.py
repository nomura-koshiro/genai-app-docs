"""Analysis API routes package."""

from app.api.routes.v1.analysis.routes import router as analysis_router
from app.api.routes.v1.analysis.templates import router as analysis_templates_router

__all__ = ["analysis_router", "analysis_templates_router"]
