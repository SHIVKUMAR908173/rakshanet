"""
Integration and API Contract tests.
Tests the FastAPI endpoints using the TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from routers.auth import get_current_user

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = lambda: {"username": "test@test.local", "role": "admin"}
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ingest_email_benign():
    payload = {
        "source_ip": "192.168.1.5",
        "timestamp": "2026-07-16T10:00:00Z",
        "subject": "Team Lunch",
        "body": "We are having lunch at 12.",
        "urls": [],
        "sender": "boss@company.com",
        "recipient": "employee@company.com",
        "headers": {"spf": "pass"}
    }
    response = client.post("/api/v1/ingest/email", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "Event accepted for processing"
    assert "event_id" in data

def test_ingest_email_phishing():
    payload = {
        "source_ip": "203.0.113.10",
        "timestamp": "2026-07-16T10:05:00Z",
        "subject": "URGENT: Verify your account",
        "body": "Click here to login and verify your credentials.",
        "urls": ["http://192.168.1.100/login/secure"],
        "sender": "admin@update-sbi.com",
        "recipient": "victim@company.com",
        "headers": {"spf": "fail"}
    }
    response = client.post("/api/v1/ingest/email", json=payload)
    assert response.status_code == 202

def test_ingest_network_log():
    payload = {
        "source_ip": "10.0.0.5",
        "timestamp": "2026-07-16T02:00:00Z",
        "log_type": "network_flow",
        "destination_ip": "198.51.100.22",
        "destination_port": 4444,
        "protocol": "tcp",
        "bytes_sent": 5000000,
        "bytes_received": 500,
        "duration_seconds": 3600
    }
    response = client.post("/api/v1/ingest/network-log", json=payload)
    assert response.status_code == 202

def test_get_dashboard_summary():
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data
    assert "critical_alerts" in data
    assert "mttd_minutes" in data

def test_get_alerts():
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    assert "alerts" in response.json()

def test_get_playbooks():
    response = client.get("/api/v1/playbooks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
