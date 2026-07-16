# RakshaNet

**Threat Detection & Guided Response for Indian Critical Infrastructure**

> Built for the Maverick Effect AI Challenge 2026 — Cybersecurity Threat Detection Track

---

## Overview

RakshaNet is a unified cybersecurity platform that fuses three capabilities into one lightweight, explainable system:

1. **Phishing Classification Engine** — DistilBERT + XGBoost fusion tuned for Indian-language lures
2. **Anomaly Detection Engine** — Isolation Forest + autoencoder for network/login/OT behavioural analysis
3. **Guided Response Playbooks** — MITRE ATT&CK-aligned containment sequences with plain-language explanations

Every alert carries a SHAP-based explanation so a generalist IT engineer can act on it — no SOC analyst required.

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Email/URL   │     │  Firewall/VPN/   │     │   OT/SCADA       │
│  Gateway     │     │  Auth Logs       │     │   Network Taps   │
└──────┬───────┘     └────────┬─────────┘     └────────┬─────────┘
       │                      │                        │
       ▼                      ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Ingestion Layer (Filebeat/Fluentd)          │
└──────────┬──────────────────────────────┬───────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────┐    ┌─────────────────────────┐
│ Phishing Engine     │    │ Anomaly Detection Engine │
│ (DistilBERT+XGBoost)│    │ (IsolationForest+AE)    │
└─────────┬───────────┘    └────────────┬────────────┘
          │                             │
          ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          Correlation & Risk Scoring Layer                       │
│          + SHAP Explainability                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          Guided Response Playbook Engine (MITRE ATT&CK)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Analyst Dashboard (React)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone the repo
git clone <repo-url>
cd Rakshanet

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build

# Access
# Dashboard: http://localhost:3000
# API:       http://localhost:8000/docs
```

## Running the Demo Scenario

To see RakshaNet in action, we provide a `demo_scenario.py` script that simulates a coordinated APT attack. It will trigger the Phishing, Anomaly, and Correlation engines to generate a High/Critical severity incident in the dashboard.

1. Ensure the Docker containers are running.
2. Open the React Dashboard (`http://localhost:3000`).
3. In a new terminal, run the demo script:
```bash
cd backend/seed
python demo_scenario.py
```
4. Watch the Dashboard's **Alert Queue** as the coordinated attack unfolds.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python, FastAPI |
| ML — Phishing Text | PyTorch, HuggingFace (DistilBERT) |
| ML — Phishing URL | XGBoost, scikit-learn |
| ML — Anomaly | scikit-learn (Isolation Forest), PyTorch (Autoencoder) |
| Explainability | SHAP |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7 |
| Dashboard | React, Vite, Recharts |
| Deployment | Docker Compose |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/ingest/email` | Submit email for phishing scoring |
| POST | `/api/v1/ingest/network-log` | Submit network/auth log for anomaly scoring |
| GET | `/api/v1/alerts` | Get prioritised alert queue |
| GET | `/api/v1/alerts/{id}` | Get alert with SHAP explanation |
| POST | `/api/v1/alerts/{id}/feedback` | Record analyst verdict |
| GET | `/api/v1/playbooks/{threat_type}` | Get recommended playbook |
| POST | `/api/v1/incidents` | Open incident from alert |
| PATCH | `/api/v1/incidents/{id}` | Update incident status |
| GET | `/api/v1/dashboard/summary` | Dashboard aggregate data |

## Project Structure

```
Rakshanet/
├── backend/          # FastAPI backend & scoring services
├── frontend/         # React analyst dashboard
├── ml/               # ML training pipelines
│   ├── phishing/     # Phishing classifier training
│   ├── anomaly/      # Anomaly detector training
│   └── models/       # Saved model artifacts
├── data/             # Datasets (gitignored)
└── docs/             # Documentation
```

## License

Built for the Maverick Effect AI Challenge 2026.
