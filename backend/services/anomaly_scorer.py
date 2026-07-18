"""
Anomaly Scorer Service — scores network/auth/OT events for behavioural anomalies.

Uses two models:
  1. Isolation Forest — for login/access behaviour (time-of-day, geo-velocity,
     device changes, failed-attempt rate)
  2. Autoencoder — for network/OT traffic (volume, protocol mix, destination
     entropy, session duration)

For the prototype/demo phase, this module includes a heuristic fallback
scorer that runs when trained models are not yet available.
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional
import os
import joblib
import numpy as np
import shap

logger = logging.getLogger("rakshanet.anomaly_scorer")

# Try loading the ML model
ML_MODEL_PATH = os.environ.get("ANOMALY_IF_MODEL_PATH", "/app/ml_models/anomaly_isolation_forest.pkl")
# Handle local dev path fallback
if not os.path.exists(ML_MODEL_PATH):
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models", "anomaly_isolation_forest.pkl"))
    if os.path.exists(local_path):
        ML_MODEL_PATH = local_path

if_model = None
if_explainer = None
try:
    if os.path.exists(ML_MODEL_PATH):
        if_model = joblib.load(ML_MODEL_PATH)
        if_explainer = shap.TreeExplainer(if_model)
        logger.info(f"Loaded Anomaly ML Model from {ML_MODEL_PATH}")
except Exception as e:
    logger.warning(f"Failed to load Anomaly ML model: {e}")


# ── Normal business hours (IST: 09:00 - 18:00) ──
BUSINESS_HOURS_START = 9
BUSINESS_HOURS_END = 18

# ── Known safe geolocations for demo ──
SAFE_GEOLOCATIONS = ["india", "in", "mumbai", "delhi", "bangalore", "chennai",
                      "hyderabad", "pune", "kolkata", "ahmedabad", "gujarat"]

# ── Suspicious protocols for OT/SCADA ──
OT_PROTOCOLS = ["modbus", "dnp3", "opc-ua", "bacnet", "iec104", "s7comm"]


def _time_anomaly_score(timestamp: Optional[datetime]) -> float:
    """Score based on whether the event occurs outside business hours."""
    if timestamp is None:
        return 0.0

    # Convert to IST (UTC+5:30) for Indian context
    ist_hour = (timestamp.hour + 5) % 24  # Rough IST offset
    if timestamp.minute >= 30:
        ist_hour = (ist_hour + 1) % 24  # +30 min adjustment

    if BUSINESS_HOURS_START <= ist_hour <= BUSINESS_HOURS_END:
        return 0.0  # Within business hours
    elif 0 <= ist_hour <= 5:
        return 0.8  # Deep night — highly anomalous
    else:
        return 0.3  # Early morning or late evening — mildly anomalous


def _geo_anomaly_score(geo_location: Optional[str]) -> float:
    """Score based on geographic anomaly (impossible travel proxy)."""
    if not geo_location:
        return 0.1  # Unknown location is mildly suspicious

    geo_lower = geo_location.lower()
    if any(safe in geo_lower for safe in SAFE_GEOLOCATIONS):
        return 0.0
    return 0.6  # Foreign location — anomalous for Indian CII


def _login_anomaly_score(payload: dict) -> float:
    """
    Heuristic anomaly scoring for login/auth events.
    Mimics Isolation Forest behaviour analysis.
    """
    score = 0.0
    contributions = {}

    action = payload.get("action", "")
    timestamp_str = payload.get("timestamp")
    timestamp = None
    if timestamp_str:
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = timestamp_str
        except (ValueError, TypeError):
            pass

    # Failed login attempts
    if action == "login_failure":
        score += 0.3
        contributions["failed_login"] = 0.3

    # Time-of-day anomaly
    time_score = _time_anomaly_score(timestamp)
    score += time_score * 0.3
    if time_score > 0:
        contributions["off_hours_access"] = round(time_score * 0.3, 4)

    # Geo-velocity / impossible travel
    geo_score = _geo_anomaly_score(payload.get("geo_location"))
    score += geo_score * 0.25
    if geo_score > 0:
        contributions["geo_anomaly"] = round(geo_score * 0.25, 4)

    # New device fingerprint
    device_fp = payload.get("device_fingerprint")
    if device_fp and device_fp.startswith("new_"):
        score += 0.15
        contributions["new_device"] = 0.15

    return min(score, 1.0), contributions


def _network_anomaly_score(payload: dict) -> float:
    """
    Heuristic anomaly scoring for network flow events.
    Mimics autoencoder reconstruction error.
    """
    score = 0.0
    contributions = {}

    bytes_sent = payload.get("bytes_sent") or 0
    bytes_received = payload.get("bytes_received") or 0
    duration = payload.get("duration_seconds") or 0
    protocol = (payload.get("protocol") or "").lower()
    dest_port = payload.get("destination_port") or 0

    if if_model is not None and if_explainer is not None:
        try:
            # We trained IsolationForest on [hour_of_day, login_failures, bytes_sent_mb]
            timestamp = payload.get("timestamp")
            hour = 12
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp)
                    else:
                        dt = timestamp
                    hour = dt.hour
                except (ValueError, TypeError):
                    pass
            bytes_mb = bytes_sent / 1_000_000
            X = np.array([[hour, 0, bytes_mb]])
            
            # Compute score
            score_if = if_model.decision_function(X)[0]
            prob = max(0.0, min(1.0, 0.5 - score_if))
            
            # Compute SHAP
            shap_values = if_explainer.shap_values(X)
            # The features for our dummy model were: hour_of_day, login_failures, bytes_sent_mb
            feature_names = ["hour_of_day", "login_failures", "bytes_sent_mb"]
            ml_contributions = {}
            for i, val in enumerate(shap_values[0]):
                # Note: For IsolationForest in SHAP, negative values push score towards anomaly
                if abs(val) > 0.1: 
                    ml_contributions[f"feature_{feature_names[i]}"] = float(val)

            return float(prob), ml_contributions
        except Exception as e:
            logger.warning(f"ML anomaly scoring failed, falling back to heuristic: {e}")

    # High outbound volume — potential data exfiltration
    if bytes_sent > 100_000_000:  # > 100 MB
        exfil_signal = min(bytes_sent / 1_000_000_000, 1.0)  # Scale to 1GB
        score += exfil_signal * 0.35
        contributions["high_outbound_volume"] = round(exfil_signal * 0.35, 4)

    # Unusual transfer ratio (upload >> download)
    if bytes_received > 0:
        ratio = bytes_sent / bytes_received
        if ratio > 10:
            score += 0.2
            contributions["abnormal_upload_ratio"] = 0.2

    # Very long session
    if duration > 28800:  # > 8 hours
        score += 0.15
        contributions["long_session"] = 0.15

    # Suspicious destination ports
    suspicious_ports = [4444, 5555, 8888, 1337, 31337, 6667, 6697]  # Common backdoor ports
    if dest_port in suspicious_ports:
        score += 0.3
        contributions["suspicious_port"] = 0.3

    # Unusual protocol
    if protocol in OT_PROTOCOLS:
        # OT protocol outside business hours is very suspicious
        timestamp = payload.get("timestamp")
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                time_score = _time_anomaly_score(timestamp)
                if time_score > 0.3:
                    score += 0.4
                    contributions["ot_off_hours"] = 0.4
            except (ValueError, TypeError):
                pass

    return min(score, 1.0), contributions


def _ot_scada_anomaly_score(payload: dict) -> float:
    """
    Heuristic anomaly scoring for OT/SCADA access patterns.
    """
    score = 0.0
    contributions = {}

    # Cross-segment traffic (where none is expected)
    metadata = payload.get("metadata", {})
    if metadata.get("cross_segment", False):
        score += 0.4
        contributions["cross_segment_traffic"] = 0.4

    # Off-hours access to control endpoints
    timestamp = payload.get("timestamp")
    if timestamp:
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            time_score = _time_anomaly_score(timestamp)
            if time_score > 0:
                score += time_score * 0.4
                contributions["ot_off_hours"] = round(time_score * 0.4, 4)
        except (ValueError, TypeError):
            pass

    # Command frequency deviation
    cmd_freq = metadata.get("command_frequency")
    baseline_freq = metadata.get("baseline_frequency")
    if cmd_freq and baseline_freq and baseline_freq > 0:
        deviation = abs(cmd_freq - baseline_freq) / baseline_freq
        if deviation > 2.0:  # More than 2x baseline
            score += 0.3
            contributions["command_frequency_deviation"] = 0.3

    # Unknown source accessing OT
    geo_score = _geo_anomaly_score(payload.get("geo_location"))
    if geo_score > 0:
        score += geo_score * 0.3
        contributions["unknown_source_ot"] = round(geo_score * 0.3, 4)

    return min(score, 1.0), contributions


def score_event(log_type: str, payload: dict) -> dict:
    """
    Score a network/auth/OT event for anomaly probability.

    Args:
        log_type: Type of log (login, network_flow, ot_scada, vpn, firewall)
        payload: Raw event payload

    Returns:
        dict with isolation_forest_score, autoencoder_error, combined_score,
        anomaly_type, and feature_contributions.
    """
    if log_type in ("login", "vpn", "auth"):
        if_score, contributions = _login_anomaly_score(payload)
        ae_score = 0.0
        anomaly_type = _classify_login_anomaly(payload, if_score)
    elif log_type == "ot_scada":
        if_score, if_contribs = _login_anomaly_score(payload)
        ae_score, ae_contribs = _ot_scada_anomaly_score(payload)
        contributions = {**if_contribs, **ae_contribs}
        anomaly_type = "ot_anomaly" if max(if_score, ae_score) > 0.4 else None
    else:  # network_flow, firewall
        if_score = 0.0
        ae_score_val, contributions = _network_anomaly_score(payload)
        ae_score = ae_score_val
        anomaly_type = _classify_network_anomaly(payload, ae_score)

    # Combined score
    combined = max(if_score, ae_score)  # Take the stronger signal

    return {
        "isolation_forest_score": round(if_score, 4),
        "autoencoder_error": round(ae_score, 4),
        "combined_score": round(combined, 4),
        "anomaly_type": anomaly_type,
        "feature_contributions": contributions,
    }


def _classify_login_anomaly(payload: dict, score: float) -> Optional[str]:
    """Classify the type of login anomaly based on features."""
    if score < 0.3:
        return None

    action = payload.get("action", "")
    geo = payload.get("geo_location", "")

    if action == "login_failure":
        return "brute_force"
    if geo and not any(s in geo.lower() for s in SAFE_GEOLOCATIONS):
        return "impossible_travel"
    return "credential_compromise"


def _classify_network_anomaly(payload: dict, score: float) -> Optional[str]:
    """Classify the type of network anomaly."""
    if score < 0.3:
        return None

    bytes_sent = payload.get("bytes_sent") or 0
    if bytes_sent > 100_000_000:
        return "data_exfil"

    dest_port = payload.get("destination_port") or 0
    suspicious_ports = [4444, 5555, 8888, 1337, 31337, 6667, 6697]
    if dest_port in suspicious_ports:
        return "c2_communication"

    return "protocol_anomaly"
