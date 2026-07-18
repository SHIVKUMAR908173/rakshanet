"""
Unit tests for Correlation Engine.
"""
import pytest
from services.correlation import compute_risk_score, should_create_alert, determine_threat_type

def test_compute_risk_score_low():
    result = compute_risk_score(
        phishing_score=0.2,
        anomaly_score=0.1,
        has_correlated_signals=False
    )
    assert result["risk_score"] < 0.4
    assert result["severity"] == "info"

def test_compute_risk_score_medium():
    result = compute_risk_score(
        phishing_score=0.9,
        anomaly_score=0.9,
        has_correlated_signals=False
    )
    assert 0.4 <= result["risk_score"] < 0.8
    assert result["severity"] in ["medium", "high"]

def test_compute_risk_score_high_correlation():
    result = compute_risk_score(
        phishing_score=1.0,
        anomaly_score=1.0,
        has_correlated_signals=True
    )
    
    assert result["breakdown"]["correlation_bonus"] > 0
    assert result["risk_score"] >= 0.8
    assert result["severity"] in ["high", "critical"]

def test_determine_threat_type():
    assert determine_threat_type(0.9, 0.0, None, False) == "phishing"
    assert determine_threat_type(0.0, 0.9, "data_exfil", False) == "data_exfil"
    assert determine_threat_type(0.8, 0.8, "brute_force", True) == "credential_compromise"
