"""
Database Seeding Script — populates the database with initial reference data.

Seeds:
  - 6 MITRE ATT&CK-aligned playbooks (Section 9.5.1)
  - Sample assets for demo
  - Default admin user
"""

import asyncio
import json
import os
import sys

# Add backend to path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, async_session, Base
from models.playbook import Playbook
from models.asset import Asset
from models.user import User


SEED_DIR = os.path.dirname(os.path.abspath(__file__))


async def seed_playbooks(session):
    """Load playbooks from JSON and insert into database."""
    playbooks_path = os.path.join(SEED_DIR, "playbooks.json")
    with open(playbooks_path, "r") as f:
        playbooks_data = json.load(f)

    for pb_data in playbooks_data:
        playbook = Playbook(
            name=pb_data["name"],
            threat_type=pb_data["threat_type"],
            severity=pb_data["severity"],
            mitre_technique=pb_data["mitre_technique"],
            mitre_technique_name=pb_data["mitre_technique_name"],
            description=pb_data["description"],
            action_sequence_json=pb_data["action_sequence"],
            requires_human_confirmation=pb_data["requires_human_confirmation"],
            estimated_time_minutes=pb_data["estimated_time_minutes"],
        )
        session.add(playbook)

    print(f"  ✓ Seeded {len(playbooks_data)} playbooks")


async def seed_assets(session):
    """Seed sample assets representing monitored infrastructure."""
    assets = [
        Asset(
            hostname="mail-gw-01",
            ip="10.0.1.10",
            asset_type="server",
            criticality_tier="high",
            sector="government",
            location="Ahmedabad, Gujarat",
        ),
        Asset(
            hostname="fw-perimeter-01",
            ip="10.0.0.1",
            asset_type="network_device",
            criticality_tier="critical",
            sector="government",
            location="Ahmedabad, Gujarat",
        ),
        Asset(
            hostname="scada-plc-01",
            ip="10.10.1.50",
            asset_type="ot_scada",
            criticality_tier="critical",
            sector="power",
            location="Vadodara, Gujarat",
        ),
        Asset(
            hostname="core-banking-srv",
            ip="10.0.2.20",
            asset_type="server",
            criticality_tier="critical",
            sector="banking",
            location="Mumbai, Maharashtra",
        ),
        Asset(
            hostname="his-ehr-01",
            ip="10.0.3.15",
            asset_type="server",
            criticality_tier="high",
            sector="health",
            location="Surat, Gujarat",
        ),
        Asset(
            hostname="vpn-gateway",
            ip="10.0.0.5",
            asset_type="network_device",
            criticality_tier="high",
            sector="government",
            location="Gandhinagar, Gujarat",
        ),
        Asset(
            hostname="water-scada-rtu",
            ip="10.10.2.30",
            asset_type="ot_scada",
            criticality_tier="critical",
            sector="transport",
            location="Rajkot, Gujarat",
        ),
        Asset(
            hostname="web-portal-01",
            ip="203.0.113.50",
            asset_type="server",
            criticality_tier="high",
            sector="government",
            location="Gandhinagar, Gujarat",
        ),
    ]

    for asset in assets:
        session.add(asset)

    print(f"  ✓ Seeded {len(assets)} assets")


async def seed_users(session):
    """Seed default analyst/admin users."""
    users = [
        User(
            name="Admin",
            email="admin@rakshanet.local",
            role="admin",
            department="Security Operations",
        ),
        User(
            name="Analyst One",
            email="analyst1@rakshanet.local",
            role="analyst",
            department="IT Security",
        ),
        User(
            name="OT Engineer",
            email="ot-engineer@rakshanet.local",
            role="engineer",
            department="OT Operations",
        ),
    ]

    for user in users:
        session.add(user)

    print(f"  ✓ Seeded {len(users)} users")


async def run_seed():
    """Run all seed functions."""
    print("🌱 Seeding RakshaNet database...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Database tables created")

    async with async_session() as session:
        await seed_users(session)
        await seed_playbooks(session)
        await seed_assets(session)
        await session.commit()

    print("✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(run_seed())
