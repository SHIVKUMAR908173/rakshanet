"""
Data Preparation Script for Anomaly Detection Engine.

Downloads and normalizes network and authentication datasets:
- CIC-IDS2017 (Network flows, DDoS, Brute Force, Exfil)
- UNSW-NB15 (Modern attack vectors)
- Synthetic OT/SCADA logs for Indian Critical Infrastructure context
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomaly_data_prep")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/anomaly"))
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def simulate_network_flow_data(n_samples=5000):
    """
    Generate synthetic network flow data representing CIC-IDS2017 structures.
    In production, this would download and parse PCAP/CSV files.
    """
    logger.info("Generating synthetic network flow dataset (CIC-IDS2017 style)...")
    np.random.seed(42)
    
    # 90% benign, 10% malicious (data exfil, DDoS, C2)
    labels = np.random.choice([0, 1], size=n_samples, p=[0.9, 0.1])
    
    bytes_sent = np.where(labels == 1, np.random.lognormal(16, 2, n_samples), np.random.lognormal(10, 1.5, n_samples))
    bytes_received = np.where(labels == 1, np.random.lognormal(10, 2, n_samples), np.random.lognormal(14, 1.5, n_samples))
    duration = np.where(labels == 1, np.random.lognormal(8, 2, n_samples), np.random.lognormal(4, 1, n_samples))
    
    dest_ports = np.where(
        labels == 1,
        np.random.choice([4444, 5555, 8888, 1337, 80, 443], size=n_samples, p=[0.2, 0.2, 0.1, 0.1, 0.2, 0.2]),
        np.random.choice([80, 443, 53, 22], size=n_samples, p=[0.4, 0.5, 0.08, 0.02])
    )
    
    return pd.DataFrame({
        'log_type': 'network_flow',
        'bytes_sent': bytes_sent,
        'bytes_received': bytes_received,
        'duration_seconds': duration,
        'destination_port': dest_ports,
        'protocol': np.random.choice(['tcp', 'udp'], size=n_samples, p=[0.8, 0.2]),
        'label': labels
    })


def simulate_auth_data(n_samples=2000):
    """
    Generate synthetic authentication logs.
    """
    logger.info("Generating synthetic auth logs...")
    np.random.seed(4242)
    
    labels = np.random.choice([0, 1], size=n_samples, p=[0.95, 0.05])
    
    # Time of day (0-23)
    # Benign: mostly 9-18. Malicious: mostly night
    hours = np.where(
        labels == 1,
        np.random.choice(list(range(24)), size=n_samples),
        np.random.choice(list(range(8, 19)), size=n_samples)
    )
    
    # Geolocation anomalies
    geo_locations = np.where(
        labels == 1,
        np.random.choice(["Russia", "China", "Ukraine", "India", "USA"], size=n_samples, p=[0.3, 0.3, 0.2, 0.1, 0.1]),
        np.random.choice(["India", "USA", "UK"], size=n_samples, p=[0.9, 0.08, 0.02])
    )
    
    actions = np.where(
        labels == 1,
        np.random.choice(["login_failure", "login_success"], size=n_samples, p=[0.8, 0.2]),
        np.random.choice(["login_failure", "login_success"], size=n_samples, p=[0.1, 0.9])
    )
    
    # Create fake ISO timestamps based on the hour
    timestamps = [f"2026-07-16T{str(h).zfill(2)}:15:00Z" for h in hours]
    
    return pd.DataFrame({
        'log_type': 'login',
        'timestamp': timestamps,
        'geo_location': geo_locations,
        'action': actions,
        'device_fingerprint': np.where(labels == 1, "new_device_uuid", "known_device_uuid"),
        'label': labels
    })


def simulate_ot_scada_data(n_samples=1000):
    """
    Generate synthetic OT/SCADA logs for critical infrastructure.
    """
    logger.info("Generating synthetic OT/SCADA logs...")
    np.random.seed(424242)
    
    labels = np.random.choice([0, 1], size=n_samples, p=[0.98, 0.02])
    
    cross_segment = np.where(labels == 1, np.random.choice([True, False], p=[0.7, 0.3], size=n_samples), False)
    cmd_freq = np.where(labels == 1, np.random.lognormal(2, 0.5, n_samples), np.random.lognormal(0.5, 0.2, n_samples))
    
    hours = np.where(
        labels == 1,
        np.random.choice([2, 3, 4, 23], size=n_samples),
        np.random.choice(list(range(9, 18)), size=n_samples)
    )
    timestamps = [f"2026-07-16T{str(h).zfill(2)}:15:00Z" for h in hours]
    
    # Pack OT specific features into a metadata string to mimic raw logs
    metadata = []
    for cs, cf in zip(cross_segment, cmd_freq):
        metadata.append({'cross_segment': bool(cs), 'command_frequency': float(cf), 'baseline_frequency': 1.5})
        
    return pd.DataFrame({
        'log_type': 'ot_scada',
        'timestamp': timestamps,
        'protocol': np.random.choice(["modbus", "dnp3", "opc-ua"], size=n_samples),
        'metadata': metadata,
        'label': labels
    })


def main():
    logger.info("Starting data preparation for Anomaly Engine...")
    
    df_net = simulate_network_flow_data()
    df_auth = simulate_auth_data()
    df_ot = simulate_ot_scada_data()
    
    combined_df = pd.concat([df_net, df_auth, df_ot], ignore_index=True)
    
    # Shuffle
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # 70/15/15 Split
    train_df, temp_df = train_test_split(combined_df, test_size=0.3, stratify=combined_df["label"], random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df["label"], random_state=42)
    
    train_path = os.path.join(PROCESSED_DIR, "train.csv")
    val_path = os.path.join(PROCESSED_DIR, "val.csv")
    test_path = os.path.join(PROCESSED_DIR, "test.csv")
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Data prep complete. Saved to {PROCESSED_DIR}")
    logger.info(f"Train size: {len(train_df)} (Benign: {len(train_df[train_df['label']==0])}, Anomaly: {len(train_df[train_df['label']==1])})")

if __name__ == "__main__":
    main()
