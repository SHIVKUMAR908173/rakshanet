"""
Feature Engineering Script for Anomaly Detection Engine.

Extracts numerical features from raw network, auth, and OT logs for
Isolation Forest and Autoencoder models.
"""

import ast
import pandas as pd
import numpy as np

# Known safe geolocations used in heuristic scorer
SAFE_GEOLOCATIONS = ["india", "in", "mumbai", "delhi", "bangalore", "chennai",
                      "hyderabad", "pune", "kolkata", "ahmedabad", "gujarat"]

# Suspicious protocols for OT/SCADA
OT_PROTOCOLS = ["modbus", "dnp3", "opc-ua", "bacnet", "iec104", "s7comm"]

# Suspicious destination ports
SUSPICIOUS_PORTS = [4444, 5555, 8888, 1337, 31337, 6667, 6697]


def extract_auth_features(row: pd.Series) -> dict:
    """Extract features for Isolation Forest (login/auth events)."""
    features = {
        "is_failed_login": 0,
        "is_off_hours": 0,
        "is_geo_anomaly": 0,
        "is_new_device": 0
    }
    
    if row.get("action") == "login_failure":
        features["is_failed_login"] = 1
        
    ts = row.get("timestamp")
    if pd.notna(ts) and isinstance(ts, str):
        try:
            hour = int(ts[11:13])
            # Assuming UTC+5:30 logic roughly handled by hour check in heuristic,
            # simplified here for feature extraction
            if not (9 <= (hour + 5) % 24 <= 18):
                features["is_off_hours"] = 1
        except Exception:
            pass
            
    geo = str(row.get("geo_location", "")).lower()
    if geo and not any(safe in geo for safe in SAFE_GEOLOCATIONS):
        features["is_geo_anomaly"] = 1
        
    dfp = str(row.get("device_fingerprint", ""))
    if dfp.startswith("new_"):
        features["is_new_device"] = 1
        
    return features


def extract_network_features(row: pd.Series) -> dict:
    """Extract features for Autoencoder (network flow events)."""
    features = {
        "bytes_sent": float(row.get("bytes_sent") or 0),
        "bytes_received": float(row.get("bytes_received") or 0),
        "duration_seconds": float(row.get("duration_seconds") or 0),
        "is_suspicious_port": 0,
        "is_ot_protocol": 0,
        "upload_ratio": 0.0
    }
    
    port = row.get("destination_port")
    if pd.notna(port) and int(port) in SUSPICIOUS_PORTS:
        features["is_suspicious_port"] = 1
        
    proto = str(row.get("protocol", "")).lower()
    if proto in OT_PROTOCOLS:
        features["is_ot_protocol"] = 1
        
    bs = features["bytes_sent"]
    br = features["bytes_received"]
    if br > 0:
        features["upload_ratio"] = min(bs / br, 100.0)  # Cap ratio
        
    # Log transform byte counts for better neural net behavior
    features["log_bytes_sent"] = np.log1p(features["bytes_sent"])
    features["log_bytes_received"] = np.log1p(features["bytes_received"])
    
    return features


def extract_ot_features(row: pd.Series) -> dict:
    """Extract features for OT/SCADA events."""
    features = {
        "is_cross_segment": 0,
        "cmd_freq_deviation": 0.0,
        "is_off_hours": 0
    }
    
    meta = row.get("metadata", "{}")
    if isinstance(meta, str) and meta.startswith("{"):
        try:
            meta = ast.literal_eval(meta)
        except Exception:
            meta = {}
            
    if isinstance(meta, dict):
        if meta.get("cross_segment"):
            features["is_cross_segment"] = 1
            
        freq = meta.get("command_frequency")
        base = meta.get("baseline_frequency")
        if freq is not None and base is not None and base > 0:
            features["cmd_freq_deviation"] = min(abs(freq - base) / base, 10.0)
            
    ts = row.get("timestamp")
    if pd.notna(ts) and isinstance(ts, str):
        try:
            hour = int(ts[11:13])
            if not (9 <= (hour + 5) % 24 <= 18):
                features["is_off_hours"] = 1
        except Exception:
            pass
            
    return features


def process_anomaly_dataframe(df: pd.DataFrame) -> tuple:
    """
    Apply feature extraction and split into auth and network/OT subsets.
    Returns (auth_df, net_df)
    """
    
    auth_rows = []
    net_rows = []
    
    for _, row in df.iterrows():
        log_type = row.get("log_type", "")
        
        if log_type == "login":
            feats = extract_auth_features(row)
            feats["label"] = row.get("label", 0)
            auth_rows.append(feats)
            
        elif log_type == "network_flow":
            feats = extract_network_features(row)
            feats["label"] = row.get("label", 0)
            # Pad OT features
            feats.update({"is_cross_segment": 0, "cmd_freq_deviation": 0.0})
            net_rows.append(feats)
            
        elif log_type == "ot_scada":
            # For OT, combine network and OT features
            feats = extract_network_features(row)
            ot_feats = extract_ot_features(row)
            feats.update(ot_feats)
            feats["label"] = row.get("label", 0)
            net_rows.append(feats)
            
    return pd.DataFrame(auth_rows), pd.DataFrame(net_rows)
