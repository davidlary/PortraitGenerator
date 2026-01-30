"""API module for Portrait Generator."""

from .models import (
    PortraitRequest,
    PortraitResult,
    SubjectData,
    EvaluationResult,
)

# Import create_app lazily to avoid circular imports
def create_app():
    """Create FastAPI application (lazy import)."""
    from .server import create_app as _create_app
    return _create_app()

__all__ = [
    "create_app",
    "PortraitRequest",
    "PortraitResult",
    "SubjectData",
    "EvaluationResult",
]
