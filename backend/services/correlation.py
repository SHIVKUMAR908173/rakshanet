"""
Correlation & Risk Scoring Engine — merges phishing and anomaly signals
into a single, prioritised risk score per identity/asset.

Implements the weighted-sum model from Section 9.3:
  risk_score = w1 · phishing_score + w2 · anomaly_score + w3 · correlation_bonus

where correlation_bonus fires when phishing + anomaly signals occur on the
same identity within the configured time window (default 24 hours).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import settings

logger = logging.getLogger("rakshanet.correlation")


def compute_risk_score(
    phishing_score: float,
    anomaly_score: float,
    has_correlated_signals: bool = False,
) -> dict:
    """
    Compute the fused risk score from independent detection signals.

    Args:
        phishing_score: Combined phishing score (0.0 - 1.0)
        anomaly_score: Combined anomaly score (0.0 - 1.0)
        has_correlated_signals: True if phishing + anomaly signals exist
            on the same identity within the correlation window

    Returns:
        dict with risk_score, severity, and scoring breakdown
    """
    w1 = settings.phishing_weight
    w2 = settings.anomaly_weight
    w3 = settings.correlation_bonus_weight

    correlation_bonus = 1.0 if has_correlated_signals else 0.0

    risk_score = w1 * phishing_score + w2 * anomaly_score + w3 * correlation_bonus
    risk_score = round(min(risk_score, 1.0), 4)

    severity = _assign_severity(risk_score)

    return {
        "risk_score": risk_score,
        "severity": severity,
        "breakdown": {
            "phishing_component": round(w1 * phishing_score, 4),
            "anomaly_component": round(w2 * anomaly_score, 4),
            "correlation_bonus": round(w3 * correlation_bonus, 4),
            "has_correlated_signals": has_correlated_signals,
        },
    }


def _assign_severity(risk_score: float) -> str:
    """
    Assign severity tier based on risk score thresholds (Section 9.5.2).

    Thresholds are configurable per deployment via environment variables.
    """
    if risk_score >= settings.alert_threshold_critical:
        return "critical"
    elif risk_score >= settings.alert_threshold_high:
        return "high"
    elif risk_score >= settings.alert_threshold_medium:
        return "medium"
    elif risk_score >= settings.alert_threshold_low:
        return "low"
    else:
        return "info"  # Below alert threshold — logged but not alerted


def should_create_alert(risk_score: float) -> bool:
    """Determine whether a risk score warrants an alert."""
    return risk_score >= settings.alert_threshold_low


def determine_threat_type(
    phishing_score: float,
    anomaly_score: float,
    anomaly_type: Optional[str] = None,
    has_correlation: bool = False,
) -> str:
    """
    Determine the primary threat type for alert classification.

    Maps to the MITRE ATT&CK techniques in Section 9.5.1.
    """
    if has_correlation and phishing_score > 0.4 and anomaly_score > 0.4:
        return "credential_compromise"  # T1078 — phish → credential use

    if phishing_score > anomaly_score:
        return "phishing"  # T1566

    if anomaly_type:
        type_mapping = {
            "brute_force": "brute_force",        # T1110
            "impossible_travel": "credential_compromise",  # T1078
            "credential_compromise": "credential_compromise",  # T1078
            "data_exfil": "data_exfil",           # T1041
            "c2_communication": "data_exfil",     # T1041
            "ot_anomaly": "ot_anomaly",           # T1021
            "protocol_anomaly": "ot_anomaly",     # T1021
        }
        return type_mapping.get(anomaly_type, "ot_anomaly")

    return "phishing" if phishing_score > 0 else "ot_anomaly"


def get_mitre_technique(threat_type: str) -> str:
    """Map a threat type to its MITRE ATT&CK technique ID."""
    mapping = {
        "phishing": "T1566",
        "credential_compromise": "T1078",
        "brute_force": "T1110",
        "ot_anomaly": "T1021",
        "data_exfil": "T1041",
        "ddos": "T1498",
    }
    return mapping.get(threat_type, "T1566")
