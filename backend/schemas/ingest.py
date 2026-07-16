"""Ingestion schemas — request models for email and network log submission."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EmailIngestRequest(BaseModel):
    """Submit an email event for phishing scoring."""

    sender: str = Field(..., description="Sender email address")
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field("", description="Email body text (plain or HTML stripped)")
    urls: list[str] = Field(default_factory=list, description="URLs extracted from email body")
    headers: dict = Field(
        default_factory=dict,
        description="Relevant email headers (SPF, DKIM, DMARC results, etc.)",
    )
    attachments: list[dict] = Field(
        default_factory=list,
        description="Attachment metadata (filename, mimetype, hash — not content)",
    )
    timestamp: Optional[datetime] = Field(
        None, description="Email received timestamp; defaults to now"
    )
    asset_id: Optional[int] = Field(
        None, description="ID of the asset (mail server) that received this email"
    )


class NetworkLogIngestRequest(BaseModel):
    """Submit a network/auth log event for anomaly scoring."""

    log_type: str = Field(
        ...,
        description="Type of log: login | network_flow | ot_scada | vpn | firewall",
    )
    source_ip: Optional[str] = Field(None, description="Source IP address")
    destination_ip: Optional[str] = Field(None, description="Destination IP address")
    source_port: Optional[int] = Field(None, description="Source port")
    destination_port: Optional[int] = Field(None, description="Destination port")
    protocol: Optional[str] = Field(None, description="Protocol (TCP, UDP, ICMP, etc.)")
    user_identity: Optional[str] = Field(
        None, description="Username or email of the person involved"
    )
    action: Optional[str] = Field(
        None, description="Action: login_success | login_failure | connection | data_transfer"
    )
    bytes_sent: Optional[int] = Field(None, description="Bytes sent in this event")
    bytes_received: Optional[int] = Field(None, description="Bytes received in this event")
    duration_seconds: Optional[float] = Field(None, description="Session duration")
    geo_location: Optional[str] = Field(
        None, description="Geographic location of source IP (country/city)"
    )
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint hash")
    timestamp: Optional[datetime] = Field(
        None, description="Event timestamp; defaults to now"
    )
    asset_id: Optional[int] = Field(
        None, description="ID of the monitored asset involved"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata specific to the log type",
    )


class IngestResponse(BaseModel):
    """Response after ingesting an event."""

    event_id: int
    status: str = "queued"
    message: str = "Event received and queued for scoring"
