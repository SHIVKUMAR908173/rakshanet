"""Dashboard API — aggregate counts and trends for the analyst dashboard."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.alert import Alert
from models.incident import Incident
from schemas.incident import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregate counts and trends for the dashboard landing view.

    Returns severity breakdown, threat type distribution, daily trend data,
    and the most recent alerts for the quick-view panel.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── Alert counts by status ──
    alert_counts = await db.execute(
        select(
            func.count(Alert.id).label("total"),
            func.count(case((Alert.status == "open", Alert.id))).label("open"),
            func.count(
                case((Alert.severity == "critical", Alert.id))
            ).label("critical"),
            func.count(case((Alert.severity == "high", Alert.id))).label("high"),
            func.count(case((Alert.severity == "medium", Alert.id))).label("medium"),
            func.count(case((Alert.severity == "low", Alert.id))).label("low"),
            func.count(
                case((Alert.created_at >= today_start, Alert.id))
            ).label("today"),
            func.coalesce(func.avg(Alert.risk_score), 0.0).label("avg_risk"),
        )
    )
    row = alert_counts.one()

    # ── Incident counts ──
    incident_counts = await db.execute(
        select(
            func.count(Incident.id).label("total"),
            func.count(
                case((Incident.status.in_(["open", "in_progress"]), Incident.id))
            ).label("open"),
            func.count(
                case((Incident.status.in_(["resolved", "closed"]), Incident.id))
            ).label("resolved"),
        )
    )
    inc_row = incident_counts.one()

    # ── Threat type breakdown ──
    threat_result = await db.execute(
        select(Alert.threat_type, func.count(Alert.id)).group_by(Alert.threat_type)
    )
    threat_breakdown = {t: c for t, c in threat_result.all()}

    # ── Severity breakdown ──
    severity_result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    severity_breakdown = {s: c for s, c in severity_result.all()}

    # ── Daily alert trend (last 30 days) ──
    thirty_days_ago = now - timedelta(days=30)
    trend_result = await db.execute(
        select(
            cast(Alert.created_at, Date).label("date"),
            func.count(Alert.id).label("count"),
        )
        .where(Alert.created_at >= thirty_days_ago)
        .group_by(cast(Alert.created_at, Date))
        .order_by(cast(Alert.created_at, Date))
    )
    alerts_trend = [
        {"date": str(d), "count": c} for d, c in trend_result.all()
    ]

    # ── Recent alerts (last 10) ──
    recent_result = await db.execute(
        select(Alert)
        .order_by(Alert.created_at.desc())
        .limit(10)
    )
    recent_alerts = [
        {
            "id": a.id,
            "severity": a.severity,
            "threat_type": a.threat_type,
            "risk_score": a.risk_score,
            "status": a.status,
            "explanation_text": a.explanation_text,
            "created_at": str(a.created_at),
        }
        for a in recent_result.scalars().all()
    ]

    return DashboardSummary(
        total_alerts=row.total,
        open_alerts=row.open,
        critical_alerts=row.critical,
        high_alerts=row.high,
        medium_alerts=row.medium,
        low_alerts=row.low,
        total_incidents=inc_row.total,
        open_incidents=inc_row.open,
        resolved_incidents=inc_row.resolved,
        alerts_today=row.today,
        avg_risk_score=round(float(row.avg_risk), 3),
        threat_type_breakdown=threat_breakdown,
        severity_breakdown=severity_breakdown,
        alerts_trend=alerts_trend,
        recent_alerts=recent_alerts,
    )
