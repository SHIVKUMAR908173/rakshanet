# RakshaNet Deployment Guide

This guide provides instructions for deploying the RakshaNet AI-Driven SOC platform to a production environment using Docker and Docker Compose.

## Prerequisites
- A Linux server (e.g., Ubuntu 22.04 LTS on AWS EC2, DigitalOcean, etc.)
- **Docker** installed (`curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`)
- **Docker Compose** installed (included with modern Docker installations)
- At least 4GB RAM (8GB recommended for ML models in memory)

## 1. Prepare the Environment

First, clone the repository to your production server:
```bash
git clone https://github.com/your-org/rakshanet.git
cd rakshanet
```

## 2. Train Initial ML Models (Optional but recommended)
If you haven't yet trained the machine learning models, run the synthetic data training script. (This requires python3 to be installed on the host, or it can be run inside a temporary container).
```bash
cd ml/data
python3 train_models.py
cd ../..
```
This will populate the `ml/models/` directory with `phishing_text_model.pkl` and `anomaly_isolation_forest.pkl`.

## 3. Configure Environment Variables
By default, `docker-compose.yml` uses sensible defaults. For a true production deployment, you should set secure passwords. 
Create a `.env` file in the root directory:

```env
POSTGRES_USER=rakshanet_admin
POSTGRES_PASSWORD=SuperSecurePassword123!
POSTGRES_DB=rakshanet_prod
JWT_SECRET=generate_a_random_long_string_here
```

## 4. Launch the Stack
Run Docker Compose in detached mode to build the images and start the services:

```bash
docker compose up --build -d
```

### Services Launched:
1. **db**: PostgreSQL database on port `5432`
2. **redis**: Redis cache on port `6379`
3. **backend**: FastAPI server on port `8000` (ML models loaded into memory)
4. **frontend**: React application on port `3000`

## 5. Seed the Default Admin User
Before you can log in, you must create the initial SOC analyst user. Execute the seed script inside the running backend container:

```bash
docker compose exec backend python seed/seed_user.py
```
*Username*: `admin@rakshanet.local`
*Password*: `password123`

## 6. Access the Dashboard
Navigate to `http://<YOUR_SERVER_IP>:3000` in your web browser. 
Log in with the credentials created in Step 5.

## Troubleshooting
- **To view backend logs:** `docker compose logs -f backend`
- **To view frontend logs:** `docker compose logs -f frontend`
- **If models fail to load:** Ensure `ml/models/` is populated and permissions allow the Docker daemon to read the files (they are mounted as read-only volumes).
