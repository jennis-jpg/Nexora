"""
models.py
=========
Pydantic request/response models and internal data schemas for the
combined SeaSentry backend (Person A — Prediction Engine, merged with
Person B — Safety & Alerting Systems).

Scope covered:
    - Boat prediction / boundary-check requests (Person A)
    - SOS incidents (Person B)
    - Awake (operator confirmation) checks (Person B)
    - Coast Guard alert payloads (Person B)

NOTE: Voice Layer (Person C) and Frontend (Person D) models still do
not belong here.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AwakeCheckStatus(str, Enum):
    """Lifecycle states for an hourly operator awake check."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"


class AlertType(str, Enum):
    """Type/category of an emergency alert sent to the Coast Guard."""

    SOS = "SOS"
    MISSED_AWAKE_CHECK = "MISSED_AWAKE_CHECK"
    BOUNDARY_CROSSING = "BOUNDARY_CROSSING"  # reserved for future use


# ---------------------------------------------------------------------------
# PERSON A — PREDICTION ENGINE
# ---------------------------------------------------------------------------

class BoatInput(BaseModel):
    """Incoming payload for a full boundary/track prediction on a boat."""

    boat_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    speed_knots: float = Field(..., ge=0, description="Current boat speed in knots")
    heading_deg: float = Field(..., ge=0, lt=360, description="0=North, clockwise")
    predict_minutes: int = Field(60, ge=5, le=180, description="How far ahead to simulate")


class BoundaryCheckInput(BaseModel):
    """Incoming payload for a stateless one-shot boundary check."""

    lat: float
    lon: float
    speed_knots: float
    heading_deg: float


# ---------------------------------------------------------------------------
# MODULE 1 — SOS SYSTEM
# ---------------------------------------------------------------------------

class SOSRequest(BaseModel):
    """Incoming payload for a manual SOS trigger from a boat/device."""

    boat_id: str = Field(..., description="Unique identifier of the boat")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    timestamp: datetime = Field(..., description="ISO-8601 timestamp of the SOS event")


class SOSResponse(BaseModel):
    """Response returned after an SOS has been processed and dispatched."""

    status: str = Field(..., example="SOS Sent")
    coastguard_ack: bool = Field(..., example=True)


# ---------------------------------------------------------------------------
# MODULE 4 — ALERT PIPELINE (shared payload contract)
# ---------------------------------------------------------------------------

class AlertPayload(BaseModel):
    """
    Canonical alert payload sent to the Coast Guard pipeline.

    Every emergency (manual SOS, missed awake check, future boundary
    crossing) is normalized into this shape before dispatch.
    """

    boat_id: str
    type: AlertType
    reason: str
    latitude: float
    longitude: float
    timestamp: datetime


class CoastGuardAckResponse(BaseModel):
    """Mock acknowledgement returned by the (simulated) Coast Guard API."""

    ack: bool
    message: str


# ---------------------------------------------------------------------------
# MODULE 2 & 3 — AWAKE CHECK / ESCALATION
# ---------------------------------------------------------------------------

class AwakeCheckRecord(BaseModel):
    """Internal representation of a single hourly awake check."""

    id: int
    boat_id: str
    created_at: datetime
    expires_at: datetime
    status: AwakeCheckStatus
    confirmed_at: Optional[datetime] = None


class AwakeCheckAckRequest(BaseModel):
    """Request body for an operator confirming they are awake."""

    boat_id: str = Field(..., description="Unique identifier of the boat")


class AwakeCheckAckResponse(BaseModel):
    """Response returned after successfully confirming an awake check."""

    status: str = Field(..., example="Awake confirmed")
    confirmed_at: datetime


class AwakeCheckStatusResponse(BaseModel):
    """Response returned when polling the latest awake check for a boat."""

    status: AwakeCheckStatus
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Internal record kept for incident timeline / PDF reporting
# ---------------------------------------------------------------------------

class IncidentEvent(BaseModel):
    """A single event recorded for a boat, used to build the PDF timeline."""

    boat_id: str
    event_type: str  # e.g. "SOS_RECEIVED", "AWAKE_CHECK_EXPIRED", "ALERT_SENT"
    description: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Sea-water level (droplet UI card)
# ---------------------------------------------------------------------------

class SeaLevelResponse(BaseModel):
    """Response returned by GET /predict/sea-level/{boat_id}."""

    tier: str    # "normal" | "rising" | "high"
    level_m: float
    trend: str   # "rising" | "falling" | "steady"
