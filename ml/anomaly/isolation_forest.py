import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
 
LOGIN_FEATURES = [
    "hour_of_day", "geo_velocity_kmh", "device_change_flag",
    "failed_attempt_rate_10min", "privilege_level",
]
 
def fit_login_anomaly_model(
    X_baseline: pd.DataFrame, contamination: float = 0.02
) -> IsolationForest:
    model = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_baseline[LOGIN_FEATURES])
    joblib.dump(model, "checkpoints/isolation_forest_login.joblib")
    return model
 
def login_anomaly_score(model: IsolationForest, row: pd.DataFrame) -> float:
    # score_samples: higher = more normal.
    # Flip and rescale to 0-1, higher = more anomalous.
    raw = model.score_samples(row[LOGIN_FEATURES])[0]
    return float(1 - (raw - model.offset_) / (0 - model.offset_))
