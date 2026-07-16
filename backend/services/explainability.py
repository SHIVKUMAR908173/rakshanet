"""
Explainability Layer — generates plain-language explanations for alerts.

Uses SHAP-like feature contribution data from the scoring services to
build human-readable explanations. When trained models with real SHAP
values are available, this module will switch from heuristic contributions
to actual SHAP values — the output format stays the same.

Design principle (Section 9.4): every alert above threshold is shown
with its top contributing features so a non-specialist can sanity-check
the model rather than blindly trust or dismiss it.
"""

import logging
from typing import Optional

logger = logging.getLogger("rakshanet.explainability")


# ── Human-readable feature name mappings ──

FEATURE_DESCRIPTIONS = {
    # Phishing features
    "text_urgency_score": "Urgency and credential-harvest language detected in email text",
    "url_structural_score": "Suspicious URL structure (IP-literal, shortener, brand spoofing)",
    "model_disagreement_signal": "Text and URL models disagree — common evasion pattern",
    "spf_fail": "SPF email authentication check failed",
    "dkim_fail": "DKIM email signature verification failed",
    "dmarc_fail": "DMARC policy check failed",
    # Anomaly features
    "failed_login": "Failed login attempt detected",
    "off_hours_access": "Access occurred outside normal business hours (IST 09:00-18:00)",
    "geo_anomaly": "Access from unexpected geographic location",
    "new_device": "Access from a previously unseen device",
    "high_outbound_volume": "Abnormally high outbound data transfer (potential exfiltration)",
    "abnormal_upload_ratio": "Upload-to-download ratio significantly higher than normal",
    "long_session": "Unusually long session duration (> 8 hours)",
    "suspicious_port": "Communication on known backdoor/C2 port",
    "ot_off_hours": "OT/SCADA system accessed outside maintenance windows",
    "cross_segment_traffic": "Traffic crossing OT/IT network segment boundary unexpectedly",
    "command_frequency_deviation": "SCADA command frequency deviates significantly from baseline",
    "unknown_source_ot": "OT system accessed from unknown or foreign source",
    # Correlation features
    "phishing_component": "Phishing classification signal",
    "anomaly_component": "Behavioural anomaly signal",
    "correlation_bonus": "Correlated phishing + anomaly signals on same identity",
}


def generate_explanation(
    phishing_contributions: Optional[dict] = None,
    anomaly_contributions: Optional[dict] = None,
    correlation_breakdown: Optional[dict] = None,
    threat_type: str = "unknown",
    severity: str = "medium",
    top_n: int = 5,
) -> dict:
    """
    Generate a structured, human-readable explanation for an alert.

    Args:
        phishing_contributions: Feature → value dict from phishing scorer
        anomaly_contributions: Feature → value dict from anomaly scorer
        correlation_breakdown: Risk scoring breakdown from correlation engine
        threat_type: Classified threat type
        severity: Assigned severity level
        top_n: Number of top features to include

    Returns:
        dict with:
          - features: sorted list of {name, value, description}
          - summary: plain-language paragraph
          - threat_context: MITRE ATT&CK context
    """
    # ── Merge all contributions ──
    all_contributions = {}
    if phishing_contributions:
        all_contributions.update(phishing_contributions)
    if anomaly_contributions:
        all_contributions.update(anomaly_contributions)

    # ── Sort by contribution value (descending) ──
    sorted_features = sorted(
        all_contributions.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:top_n]

    # ── Build structured feature list ──
    features = []
    for name, value in sorted_features:
        if value > 0:
            features.append({
                "name": name,
                "value": round(value, 4),
                "description": FEATURE_DESCRIPTIONS.get(
                    name, f"Feature: {name.replace('_', ' ')}"
                ),
            })

    # ── Generate plain-language summary ──
    summary = _build_summary(features, threat_type, severity, correlation_breakdown)

    # ── MITRE ATT&CK context ──
    threat_context = _get_threat_context(threat_type)

    return {
        "features": features,
        "summary": summary,
        "threat_context": threat_context,
        "severity": severity,
        "threat_type": threat_type,
    }


def _build_summary(
    features: list[dict],
    threat_type: str,
    severity: str,
    correlation: Optional[dict] = None,
) -> str:
    """Build a plain-language summary from the top contributing features."""
    if not features:
        return f"Alert generated with {severity} severity for {threat_type} threat."

    # Build the "flagged mainly due to:" sentence
    reasons = [f["description"].lower() for f in features[:3]]
    reasons_text = "; ".join(reasons)

    severity_preamble = {
        "critical": "CRITICAL ALERT — Immediate action required.",
        "high": "HIGH SEVERITY — Prompt response recommended.",
        "medium": "Moderate-severity alert — review within 4 hours.",
        "low": "Low-severity observation — included in weekly digest.",
    }
    preamble = severity_preamble.get(severity, "Alert generated.")

    correlation_note = ""
    if correlation and correlation.get("has_correlated_signals"):
        correlation_note = (
            " Multiple independent detection signals on the same identity "
            "increase confidence in this alert."
        )

    return (
        f"{preamble} Flagged mainly due to: {reasons_text}.{correlation_note}"
    )


def _get_threat_context(threat_type: str) -> dict:
    """Return MITRE ATT&CK context for the threat type."""
    contexts = {
        "phishing": {
            "mitre_id": "T1566",
            "mitre_name": "Phishing",
            "tactic": "Initial Access",
            "description": "Adversary sent a phishing message to gain access to the target system.",
            "recommended_actions": [
                "Quarantine the email",
                "Block the sender domain",
                "Notify affected user",
                "Check if credentials were submitted",
            ],
        },
        "credential_compromise": {
            "mitre_id": "T1078",
            "mitre_name": "Valid Accounts",
            "tactic": "Defense Evasion, Persistence, Privilege Escalation, Initial Access",
            "description": "Compromised credentials are being used to access systems.",
            "recommended_actions": [
                "Force password reset",
                "Terminate active sessions",
                "Require step-up authentication",
                "Review recent activity on the account",
            ],
        },
        "brute_force": {
            "mitre_id": "T1110",
            "mitre_name": "Brute Force",
            "tactic": "Credential Access",
            "description": "Repeated login attempts suggesting credential stuffing or brute-force attack.",
            "recommended_actions": [
                "Temporarily lock the account",
                "Enable CAPTCHA",
                "Rate-limit source IP range",
                "Review for credential reuse",
            ],
        },
        "ot_anomaly": {
            "mitre_id": "T1021",
            "mitre_name": "Remote Services",
            "tactic": "Lateral Movement",
            "description": "Anomalous access to OT/SCADA control endpoints detected.",
            "recommended_actions": [
                "Isolate the network segment",
                "Page on-call OT engineer",
                "Escalate to SOC lead immediately",
                "Capture network traffic for forensics",
            ],
        },
        "data_exfil": {
            "mitre_id": "T1041",
            "mitre_name": "Exfiltration Over C2 Channel",
            "tactic": "Exfiltration",
            "description": "Abnormal outbound data transfer suggesting data exfiltration.",
            "recommended_actions": [
                "Block egress from the host",
                "Isolate the host",
                "Snapshot for forensic analysis",
                "Open formal incident",
            ],
        },
        "ddos": {
            "mitre_id": "T1498",
            "mitre_name": "Network Denial of Service",
            "tactic": "Impact",
            "description": "Traffic volume anomaly consistent with DDoS attack on public endpoint.",
            "recommended_actions": [
                "Enable upstream traffic scrubbing",
                "Apply rate-limiting rules",
                "Notify ISP",
                "Report to CERT-In",
            ],
        },
    }
    return contexts.get(threat_type, {
        "mitre_id": "unknown",
        "mitre_name": "Unknown Technique",
        "tactic": "Unknown",
        "description": "Threat type not yet classified.",
        "recommended_actions": ["Review the alert details manually."],
    })
