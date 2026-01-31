"""FastAPI server application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    logger.info("Starting Portrait Generator API")
    logger.info(f"Output directory: {settings.OUTPUT_DIR}")
    logger.info(f"Model: {settings.GEMINI_MODEL}")

    yield

    # Shutdown
    logger.info("Shutting down Portrait Generator API")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="Portrait Generator API",
        description="AI-powered historical portrait generation with Google Gemini 3 Pro Image",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router, prefix="/api/v1", tags=["portraits"])

    logger.info("FastAPI application created")

    return app


# Create app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "portrait_generator.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
