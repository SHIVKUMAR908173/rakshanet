"""Ingestion API — endpoints for submitting emails and network logs for scoring."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.event import EventRaw
from schemas.ingest import EmailIngestRequest, NetworkLogIngestRequest, IngestResponse
from services.event_processor import process_event

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/email", response_model=IngestResponse, status_code=201)
async def ingest_email(
    request: EmailIngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an email event for phishing scoring.

    The email metadata is stored as a raw event, then queued for
    asynchronous scoring by the phishing classification engine.
    """
    event = EventRaw(
        source="email",
        event_type="phishing_candidate",
        timestamp=request.timestamp or datetime.now(timezone.utc),
        raw_payload={
            "sender": request.sender,
            "recipient": request.recipient,
            "subject": request.subject,
            "body": request.body,
            "urls": request.urls,
            "headers": request.headers,
            "attachments": request.attachments,
        },
        asset_id=request.asset_id,
        user_identity=request.recipient,
        processed=False,
    )
    db.add(event)
    await db.flush()

    # Queue scoring in the background so the API responds immediately
    background_tasks.add_task(process_event, event.id, "phishing")

    return IngestResponse(
        event_id=event.id,
        status="queued",
        message="Email event received and queued for phishing scoring",
    )


@router.post("/network-log", response_model=IngestResponse, status_code=201)
async def ingest_network_log(
    request: NetworkLogIngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a network/auth log event for anomaly scoring.

    Covers login events, network flows, VPN sessions, firewall logs,
    and OT/SCADA access patterns.
    """
    event = EventRaw(
        source=request.log_type,
        event_type=request.log_type,
        timestamp=request.timestamp or datetime.now(timezone.utc),
        raw_payload={
            "log_type": request.log_type,
            "source_ip": request.source_ip,
            "destination_ip": request.destination_ip,
            "source_port": request.source_port,
            "destination_port": request.destination_port,
            "protocol": request.protocol,
            "user_identity": request.user_identity,
            "action": request.action,
            "bytes_sent": request.bytes_sent,
            "bytes_received": request.bytes_received,
            "duration_seconds": request.duration_seconds,
            "geo_location": request.geo_location,
            "device_fingerprint": request.device_fingerprint,
            "metadata": request.metadata,
        },
        asset_id=request.asset_id,
        user_identity=request.user_identity,
        processed=False,
    )
    db.add(event)
    await db.flush()

    # Queue scoring in the background
    background_tasks.add_task(process_event, event.id, "anomaly")

    return IngestResponse(
        event_id=event.id,
        status="queued",
        message="Network log event received and queued for anomaly scoring",
    )
