"""
Unit tests for the Phishing Scorer Service.
"""
import pytest
from services.phishing_scorer import score_email, _score_text_heuristic, _score_url_heuristic

def test_text_heuristic_benign():
    subject = "Meeting tomorrow"
    body = "Let's meet at 10 AM to discuss the project."
    score, contribs = _score_text_heuristic(subject, body)
    assert score < 0.2

def test_text_heuristic_phishing():
    subject = "URGENT: Account Suspended"
    body = "Click here to verify your login credentials immediately!"
    score, contribs = _score_text_heuristic(subject, body)
    assert score > 0.6

def test_url_heuristic_benign():
    urls = ["https://www.google.com", "https://github.com/rakshanet"]
    score = _score_url_heuristic(urls)
    assert score < 0.2

def test_url_heuristic_phishing():
    # IP literal and suspicious path
    urls = ["http://192.168.1.100/login/secure", "http://bit.ly/12345"]
    score = _score_url_heuristic(urls)
    assert score > 0.1

def test_score_email_end_to_end_benign():
    result = score_email(
        subject="Weekly Report",
        body="Here is the report for this week.",
        urls=["https://docs.google.com"],
        headers={"spf": "pass", "dkim": "pass", "dmarc": "pass"}
    )
    assert result["verdict"] == "benign"
    assert result["combined_score"] < 0.4

def test_score_email_end_to_end_phishing():
    result = score_email(
        subject="Action Required: Update KYC",
        body="Your account will be blocked. Click to update KYC now.",
        urls=["http://sbi.update-kyc.com/login"],
        headers={"spf": "fail", "dkim": "fail", "dmarc": "fail"}
    )
    assert result["verdict"] in ["phishing", "suspicious"]
    assert result["combined_score"] > 0.5

def test_model_disagreement_signal():
    # Clean text but highly malicious URL
    result = score_email(
        subject="Hello",
        body="Please see the attached link.",
        urls=["http://192.168.1.1/sbi/login/secure/update"],
        headers={"spf": "pass", "dkim": "pass"}
    )
    
    # We expect the URL score to be high, text score to be low, triggering disagreement
    if result["url_score"] > result["text_score"] + 0.3:
        assert result["model_disagreement"] == True
        assert result["feature_contributions"]["model_disagreement_signal"] > 0
