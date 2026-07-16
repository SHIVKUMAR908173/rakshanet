"""
Demo Scenario Generator for RakshaNet.

This script simulates a coordinated Advanced Persistent Threat (APT) attack.
It sends a sequence of API requests to the backend ingest endpoints, triggering
the scoring, correlation, and playbook pipelines.

Run this script while recording the Analyst Dashboard to demonstrate:
1. Low Severity Alert: Phishing email (Initial Access)
2. Medium Severity Alert: Anomalous off-hours login (Credential Access)
3. Critical Severity Alert: Correlation Engine linking the two events (Lateral Movement/Exfil)
"""

import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_URL = "http://localhost:8000/api/v1/ingest"

def simulate_phishing_campaign():
    logging.info("--- Step 1: Sending Vernacular Phishing Email ---")
    payload = {
        "source_ip": "103.45.67.89",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 3600)),
        "subject": "URGENT: SBI Account KYC Update Required",
        "body": "Apka SBI account block ho gaya hai. Turant KYC update karein warna khata band ho jayega.",
        "urls": ["http://sbi-kyc-update-secure.com/login"],
        "sender": "alerts@sbi-kyc-update-secure.com",
        "recipient": "plant_manager@indiapower.gov.in",
        "headers": {"spf": "fail", "dkim": "fail"}
    }
    try:
        r = requests.post(f"{BASE_URL}/email", json=payload)
        logging.info(f"Phishing ingestion status: {r.status_code}")
    except Exception as e:
        logging.error(f"Failed to connect: {e}")

def simulate_anomalous_login():
    logging.info("--- Step 2: Anomalous Login from compromised identity ---")
    # Simulate a login 45 minutes after the phishing email, from an unusual location
    payload = {
        "source_ip": "45.12.34.56",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 900)),
        "log_type": "login",
        "action": "login_success",
        "user_identity": "plant_manager@indiapower.gov.in",
        "geo_location": "St. Petersburg, Russia",
        "device_fingerprint": "new_device_win10_edge"
    }
    try:
        r = requests.post(f"{BASE_URL}/network-log", json=payload)
        logging.info(f"Login anomaly ingestion status: {r.status_code}")
    except Exception as e:
        logging.error(f"Failed to connect: {e}")

def simulate_ot_scada_probe():
    logging.info("--- Step 3: Lateral Movement / SCADA Probe ---")
    # Simulate OT cross-segment traffic a few minutes after the login
    payload = {
        "source_ip": "10.0.5.50",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "log_type": "ot_scada",
        "user_identity": "plant_manager@indiapower.gov.in",
        "destination_ip": "192.168.100.15", # SCADA RTU
        "destination_port": 502, # Modbus
        "protocol": "modbus",
        "bytes_sent": 2500,
        "bytes_received": 150,
        "duration_seconds": 12,
        "metadata": {
            "cross_segment": True,
            "command_frequency": 45,
            "baseline_frequency": 2
        }
    }
    try:
        r = requests.post(f"{BASE_URL}/network-log", json=payload)
        logging.info(f"OT SCADA probe ingestion status: {r.status_code}")
    except Exception as e:
        logging.error(f"Failed to connect: {e}")

def main():
    print("=====================================================")
    print(" RakshaNet Demo Scenario Generator ")
    print(" Ensure FastAPI backend is running on localhost:8000")
    print("=====================================================\n")
    
    print("Simulating coordinated attack in 3 seconds...")
    time.sleep(3)
    
    simulate_phishing_campaign()
    print("\nWaiting for correlation engine (5s)...")
    time.sleep(5)
    
    simulate_anomalous_login()
    print("\nWaiting for correlation engine (5s)...")
    time.sleep(5)
    
    simulate_ot_scada_probe()
    
    print("\n=====================================================")
    print(" Attack simulation complete.")
    print(" Open the React Dashboard to view the resulting Alerts.")
    print(" You should see a High/Critical severity correlation.")
    print("=====================================================")

if __name__ == "__main__":
    main()
