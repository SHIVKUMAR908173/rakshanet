import pandas as pd
from datetime import datetime, timedelta

# Mock functions for things not provided in spec
def get_confirmed_incident_event_ids():
    return []

def load_recent_events():
    return pd.DataFrame()

def build_dataloader(df):
    return []

from .isolation_forest import fit_login_anomaly_model
from .autoencoder import TrafficAutoencoder, train_autoencoder, NETWORK_FEATURES

def get_rolling_baseline(
    events_df: pd.DataFrame,
    window_days: int = 30,
    exclude_confirmed_incidents: bool = True,
) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    baseline = events_df[events_df["timestamp"] >= cutoff]
    if exclude_confirmed_incidents:
        seen_ids = get_confirmed_incident_event_ids()
        baseline = baseline[~baseline["event_id"].isin(seen_ids)]
    return baseline
 
def scheduled_retrain_job():
    """Intended to run nightly via cron / Airflow."""
    baseline = get_rolling_baseline(load_recent_events())
    fit_login_anomaly_model(baseline)
    train_autoencoder(
        TrafficAutoencoder(),
        build_dataloader(baseline[NETWORK_FEATURES]),
    )
