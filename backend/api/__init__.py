"""RakshaNet API Routes Package."""

from fastapi import APIRouter

from api.ingest import router as ingest_router
from api.alerts import router as alerts_router
from api.playbooks import router as playbooks_router
from api.incidents import router as incidents_router
from api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ingest_router)
api_router.include_router(alerts_router)
api_router.include_router(playbooks_router)
api_router.include_router(incidents_router)
api_router.include_router(dashboard_router)
