"""
Unit tests for the Anomaly Scorer Service.
"""
import pytest
from services.anomaly_scorer import score_event

def test_auth_event_benign():
    result = score_event("auth", {
        "action": "login_success",
        "timestamp": "2026-07-16T14:30:00Z", # Business hours
        "geo_location": "Mumbai, India",
        "device_fingerprint": "known_device_123"
    })
    assert result["anomaly_type"] is None
    assert result["combined_score"] < 0.4

def test_auth_event_anomaly():
    result = score_event("auth", {
        "action": "login_failure",
        "timestamp": "2026-07-16T02:30:00Z", # Off-hours
        "geo_location": "Moscow, Russia",    # Foreign login
        "device_fingerprint": "new_device_999"
    })
    assert result["anomaly_type"] in ["credential_compromise", "brute_force"]
    assert result["combined_score"] >= 0.5
    assert "geo_anomaly" in result["feature_contributions"] or "geo_anomaly_score" in result["feature_contributions"]

def test_network_event_benign():
    result = score_event("network", {
        "bytes_sent": 5000,
        "bytes_received": 150000,
        "destination_port": 443,
        "protocol": "tcp"
    })
    assert result["anomaly_type"] in [None, "protocol_anomaly"]
    assert result["combined_score"] < 0.6

def test_network_event_anomaly():
    # Massive upload relative to download on unusual port
    result = score_event("network", {
        "bytes_sent": 50000000,
        "bytes_received": 1000,
        "destination_port": 4444, # Common C2 port
        "protocol": "tcp"
    })
    assert result["anomaly_type"] in ["data_exfil", "malware_c2", "c2_communication"]
    assert result["combined_score"] >= 0.4

def test_ot_event_anomaly():
    # Cross segment access on OT protocol with high deviation
    result = score_event("network", {
        "protocol": "modbus",
        "bytes_sent": 1000,
        "bytes_received": 1000,
        "metadata": {"cross_segment": True}
    })
    assert result["anomaly_type"] in ["ot_anomaly", "protocol_anomaly"]
    assert result["combined_score"] > 0.35
