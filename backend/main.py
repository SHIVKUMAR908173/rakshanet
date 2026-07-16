"""
RakshaNet — Main Application Entry Point

Threat Detection & Guided Response Platform for Indian Critical Infrastructure.
Built for the Maverick Effect AI Challenge 2026 — Cybersecurity Track.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db, close_db
from api import api_router
from routers import alerts, playbooks, incidents, ingest, dashboard, auth

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rakshanet")


# ── Lifespan (startup / shutdown) ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise database on startup, clean up on shutdown."""
    logger.info("🛡️  RakshaNet starting up...")
    import models  # Ensure all models are registered with Base.metadata
    await init_db()
    logger.info("✅ Database tables ready")
    yield
    logger.info("🛡️  RakshaNet shutting down...")
    await close_db()


# ── Application ──
app = FastAPI(
    title="RakshaNet",
    description=(
        "Threat Detection & Guided Response Platform for Indian Critical Infrastructure. "
        "Fuses phishing classification, behavioural anomaly detection, and MITRE ATT&CK-aligned "
        "response playbooks into a single, explainable system."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(api_router)
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Root health check endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "description": "Threat Detection & Guided Response for Indian Critical Infrastructure",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "up",
            "phishing_engine": "ready",
            "anomaly_engine": "ready",
            "correlation_engine": "ready",
            "playbook_engine": "ready",
        },
    }
