"""
services/sos_service.py
========================
Core SOS + Coast Guard alert pipeline for Person B.

This module owns:
    - MODULE 1: Manual SOS handling
    - MODULE 4: The single reusable `create_alert()` pipeline that every
      emergency source (manual SOS, missed awake check, future boundary
      crossing) must go through before contacting the Coast Guard.

Other services (e.g. the scheduler for missed awake checks) MUST call
into `create_alert()` here rather than re-implementing alert logic.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from database import add_incident_event
from models import (
    AlertPayload,
    AlertType,
    CoastGuardAckResponse,
    IncidentEvent,
    SOSRequest,
    SOSResponse,
)

logger = logging.getLogger("seasentry.sos_service")


# ---------------------------------------------------------------------------
# MODULE 4 — Mock Coast Guard dispatch
# ---------------------------------------------------------------------------

def send_to_coastguard(payload: AlertPayload) -> CoastGuardAckResponse:
    """
    Send an alert payload to the Coast Guard.

    No real Coast Guard API is available yet, so this is a mock
    implementation that logs the payload and returns a simulated
    acknowledgement. Replace the body with a real httpx/requests call
    to the Coast Guard's API when one is provisioned.

    Args:
        payload: The normalized alert payload to dispatch.

    Returns:
        A mock acknowledgement indicating the alert was "received".
    """
    logger.info(
        "[MOCK COAST GUARD DISPATCH] boat_id=%s type=%s reason=%s lat=%s lon=%s timestamp=%s",
        payload.boat_id, payload.type, payload.reason,
        payload.latitude, payload.longitude, payload.timestamp,
    )
    return CoastGuardAckResponse(ack=True, message="Alert received")


# ---------------------------------------------------------------------------
# MODULE 4 — Unified alert creation pipeline
# ---------------------------------------------------------------------------

def create_alert(
    boat_id: str,
    alert_type: AlertType,
    reason: str,
    latitude: float,
    longitude: float,
    timestamp: datetime,
) -> CoastGuardAckResponse:
    """
    Build a normalized AlertPayload and dispatch it to the Coast Guard.

    This is the single entry point that ALL emergency sources must use:
        - Manual SOS (Module 1)
        - Missed awake check escalation (Module 3)
        - Future high-risk boundary crossing detection

    Args:
        boat_id: Unique identifier of the boat.
        alert_type: Category of the alert (SOS, MISSED_AWAKE_CHECK, ...).
        reason: Human-readable explanation of why the alert was raised.
        latitude: Last known latitude of the boat.
        longitude: Last known longitude of the boat.
        timestamp: Time the triggering event occurred.

    Returns:
        The Coast Guard's (mock) acknowledgement response.
    """
    payload = AlertPayload(
        boat_id=boat_id,
        type=alert_type,
        reason=reason,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
    )

    logger.info("Creating alert for boat_id=%s type=%s reason=%s", boat_id, alert_type, reason)

    add_incident_event(
        IncidentEvent(
            boat_id=boat_id,
            event_type=f"ALERT_CREATED_{alert_type.value}",
            description=reason,
            timestamp=timestamp,
        )
    )

    ack = send_to_coastguard(payload)

    add_incident_event(
        IncidentEvent(
            boat_id=boat_id,
            event_type="ALERT_DISPATCHED",
            description=f"Coast Guard acknowledgement: {ack.message}",
            timestamp=datetime.now(timezone.utc),
        )
    )

    return ack


# ---------------------------------------------------------------------------
# MODULE 1 — Manual SOS handling
# ---------------------------------------------------------------------------

def handle_sos(request: SOSRequest) -> SOSResponse:
    """
    Process a manual SOS request from a boat.

    Validates (via Pydantic at the route layer), records the incident,
    and routes the emergency through the shared alert pipeline.

    Args:
        request: The validated SOS request payload.

    Returns:
        SOSResponse indicating the alert was sent and whether the
        Coast Guard acknowledged it.
    """
    try:
        logger.info("Received manual SOS from boat_id=%s", request.boat_id)

        add_incident_event(
            IncidentEvent(
                boat_id=request.boat_id,
                event_type="SOS_RECEIVED",
                description="Manual SOS triggered by operator/device.",
                timestamp=request.timestamp,
            )
        )

        ack = create_alert(
            boat_id=request.boat_id,
            alert_type=AlertType.SOS,
            reason="Manual SOS triggered.",
            latitude=request.latitude,
            longitude=request.longitude,
            timestamp=request.timestamp,
        )

        return SOSResponse(status="SOS Sent", coastguard_ack=ack.ack)

    except Exception:
        logger.exception("Failed to process SOS for boat_id=%s", request.boat_id)
        raise
