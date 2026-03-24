"""
FastAPI Application Entry Point.
Initializes vector store, sets up CORS, mounts routes.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import get_settings
from memory.vector_store import vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize services on startup."""
    settings = get_settings()
    logger.info("Starting Supply Chain Orchestrator AI System...")

    # Initialize vector memory store
    try:
        vector_store.initialize()
        logger.info("Vector memory store ready")
    except Exception as e:
        logger.warning(f"Vector store init failed (non-fatal): {e}")

    yield

    logger.info("Shutting down Supply Chain Orchestrator...")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Supply Chain Orchestrator AI System",
        description=(
            "Multi-agent AI system for supply chain disruption detection, "
            "supplier discovery, risk assessment, and autonomous decision-making "
            "with human-in-the-loop approval."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    app.include_router(router, prefix="/api/v1", tags=["Supply Chain Orchestrator"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "supply-chain-orchestrator",
            "vector_store": vector_store.is_ready,
        }

    return app


app = create_app()
