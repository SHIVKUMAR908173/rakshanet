"""
Unit tests for Correlation Engine.
"""
import pytest
from services.correlation import calculate_risk_score, _compute_correlation_bonus
from datetime import datetime, timezone, timedelta

def test_calculate_risk_score_low():
    result = calculate_risk_score(
        phishing_score=0.2,
        anomaly_score=0.1,
        related_alerts=[]
    )
    assert result["risk_score"] < 40
    assert result["severity"] == "Low"

def test_calculate_risk_score_medium():
    result = calculate_risk_score(
        phishing_score=0.6,
        anomaly_score=0.4,
        related_alerts=[]
    )
    assert 40 <= result["risk_score"] < 70
    assert result["severity"] == "Medium"
    assert result["mitre_tactic"] == "Initial Access"

def test_calculate_risk_score_high_correlation():
    # Simulate a recent related phishing alert for the same identity
    now = datetime.now(timezone.utc)
    related_alerts = [
        {
            "id": "alert-123",
            "threat_type": "phishing",
            "severity": "Medium",
            "timestamp": now - timedelta(hours=2) # Within 24h window
        }
    ]
    
    # Current event is an anomaly
    result = calculate_risk_score(
        phishing_score=0.0,
        anomaly_score=0.75,
        related_alerts=related_alerts
    )
    
    assert result["correlation_bonus"] > 0
    assert result["risk_score"] >= 70
    assert result["severity"] in ["High", "Critical"]
    
def test_correlation_bonus_out_of_window():
    now = datetime.now(timezone.utc)
    related_alerts = [
        {
            "id": "alert-123",
            "threat_type": "phishing",
            "severity": "Medium",
            "timestamp": now - timedelta(hours=48) # Outside 24h window
        }
    ]
    
    # Should be 0 since it's outside the window
    bonus = _compute_correlation_bonus("anomaly", related_alerts)
    assert bonus == 0

def test_correlation_bonus_different_threat():
    now = datetime.now(timezone.utc)
    related_alerts = [
        {
            "id": "alert-123",
            "threat_type": "phishing",
            "severity": "High",
            "timestamp": now - timedelta(hours=2)
        }
    ]
    
    # If the current event is an anomaly and we had a recent phishing alert, 
    # the correlation bonus should be high (signals credential compromise -> lateral movement)
    bonus = _compute_correlation_bonus("anomaly", related_alerts)
    assert bonus == 25
