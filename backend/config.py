"""
RakshaNet Configuration — centralised settings loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ──
    database_url: str = "postgresql+asyncpg://rakshanet:changeme_in_production@localhost:5432/rakshanet"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── Correlation Engine ──
    correlation_window_hours: int = 24
    phishing_weight: float = 0.4
    anomaly_weight: float = 0.4
    correlation_bonus_weight: float = 0.2

    # ── Alert Thresholds ──
    alert_threshold_low: float = 0.3
    alert_threshold_medium: float = 0.5
    alert_threshold_high: float = 0.7
    alert_threshold_critical: float = 0.9

    # ── Model Paths ──
    phishing_text_model_path: str = "ml/models/phishing_text_model"
    phishing_url_model_path: str = "ml/models/phishing_url_model.pkl"
    phishing_fusion_model_path: str = "ml/models/phishing_fusion_model.pkl"
    anomaly_if_model_path: str = "ml/models/anomaly_isolation_forest.pkl"
    anomaly_ae_model_path: str = "ml/models/anomaly_autoencoder.pt"

    # ── Application ──
    app_name: str = "RakshaNet"
    app_version: str = "0.1.0"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
