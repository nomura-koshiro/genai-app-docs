"""Analysis API routes package."""

from app.api.routes.v1.analysis.analysis import router as analysis_router
from app.api.routes.v1.analysis.templates import router as analysis_templates_router

__all__ = ["analysis_router", "analysis_templates_router"]
