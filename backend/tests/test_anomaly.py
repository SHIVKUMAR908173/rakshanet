"""
Unit tests for the Anomaly Scorer Service.
"""
import pytest
from services.anomaly_scorer import score_network_event, score_auth_event, score_ot_event

def test_auth_event_benign():
    result = score_auth_event(
        action="login_success",
        timestamp="2026-07-16T14:30:00Z", # Business hours
        geo_location="Mumbai, India",
        device_fingerprint="known_device_123"
    )
    assert result["verdict"] == "benign"
    assert result["combined_score"] < 0.4

def test_auth_event_anomaly():
    result = score_auth_event(
        action="login_failure",
        timestamp="2026-07-16T02:30:00Z", # Off-hours
        geo_location="Moscow, Russia",    # Foreign login
        device_fingerprint="new_device_999"
    )
    assert result["verdict"] == "anomaly"
    assert result["combined_score"] >= 0.7
    assert result["feature_contributions"]["geo_anomaly_score"] > 0

def test_network_event_benign():
    result = score_network_event(
        bytes_sent=5000,
        bytes_received=150000,
        destination_port=443,
        protocol="tcp"
    )
    assert result["verdict"] == "benign"
    assert result["combined_score"] < 0.4

def test_network_event_anomaly():
    # Massive upload relative to download on unusual port
    result = score_network_event(
        bytes_sent=50000000,
        bytes_received=1000,
        destination_port=4444, # Common C2 port
        protocol="tcp"
    )
    assert result["verdict"] == "anomaly"
    assert result["combined_score"] >= 0.7
    assert "upload_ratio_score" in result["feature_contributions"]

def test_ot_event_anomaly():
    # Cross segment access on OT protocol with high deviation
    result = score_ot_event(
        protocol="modbus",
        bytes_sent=1000,
        bytes_received=1000,
        metadata={"cross_segment": True, "command_frequency": 50, "baseline_frequency": 5}
    )
    assert result["verdict"] == "anomaly"
    assert result["combined_score"] >= 0.7
    assert result["feature_contributions"]["cross_segment_penalty"] > 0
