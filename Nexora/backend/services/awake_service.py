"""
services/awake_service.py
===========================
MODULE 2 — Hourly operator awake check (confirmation system, NOT heartbeat).
MODULE 3 — Automatic escalation to SOS when a check is missed.

Business rules:
    - Every 60 minutes, the scheduler creates a new pending awake check
      per active boat (see services/scheduler.py).
    - Each check expires 5 minutes after creation.
    - The frontend polls GET /awake-check/status/{boat_id} for the
      latest check's status.
    - The operator confirms via POST /awake-check/ack.
    - A background job (every minute) sweeps pending checks; any past
      their expires_at is marked expired and escalated to the SOS
      pipeline via sos_service.create_alert() (never duplicated logic).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from database import (
    add_incident_event,
    create_awake_check,
    get_all_pending_awake_checks,
    get_latest_awake_check,
    get_latest_pending_awake_check,
    update_awake_check,
)
from models import AlertType, AwakeCheckRecord, AwakeCheckStatus, IncidentEvent
from services.sos_service import create_alert

logger = logging.getLogger("seasentry.awake_service")

# Awake checks expire 5 minutes after creation, per the safety-check UX copy.
AWAKE_CHECK_WINDOW_MINUTES = 5

# Demo fallback coordinates used only if a boat has no other known position
# at the time an awake check expires. Real system would use last known
# telemetry from Person A's Prediction Engine / boat tracking.
_DEFAULT_LATITUDE = 0.0
_DEFAULT_LONGITUDE = 0.0


# ---------------------------------------------------------------------------
# MODULE 2 — Creation & status
# ---------------------------------------------------------------------------

def create_awake_check_for_boat(boat_id: str) -> AwakeCheckRecord:
    """
    Create a new pending awake check for a boat.

    Called by the scheduler once every 60 minutes per active boat.

    Args:
        boat_id: Unique identifier of the boat.

    Returns:
        The newly created AwakeCheckRecord.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=AWAKE_CHECK_WINDOW_MINUTES)

    record = create_awake_check(boat_id=boat_id, created_at=now, expires_at=expires_at)

    add_incident_event(
        IncidentEvent(
            boat_id=boat_id,
            event_type="AWAKE_CHECK_CREATED",
            description="Hourly operator awake check created.",
            timestamp=now,
        )
    )

    logger.info("Awake check scheduled for boat_id=%s expires_at=%s", boat_id, expires_at)
    return record


def get_awake_check_status(boat_id: str) -> Optional[AwakeCheckRecord]:
    """
    Return the latest awake check record for a boat, if one exists.

    Args:
        boat_id: Unique identifier of the boat.

    Returns:
        The latest AwakeCheckRecord, or None if the boat has no checks yet.
    """
    return get_latest_awake_check(boat_id)


def confirm_awake_check(boat_id: str) -> Optional[AwakeCheckRecord]:
    """
    Mark the latest pending awake check for a boat as confirmed.

    Args:
        boat_id: Unique identifier of the boat confirming.

    Returns:
        The updated AwakeCheckRecord, or None if there was no pending
        check to confirm (e.g. already confirmed, expired, or none exists).
    """
    pending = get_latest_pending_awake_check(boat_id)
    if pending is None:
        logger.warning("No pending awake check to confirm for boat_id=%s", boat_id)
        return None

    now = datetime.now(timezone.utc)
    pending.status = AwakeCheckStatus.CONFIRMED
    pending.confirmed_at = now
    update_awake_check(pending)

    add_incident_event(
        IncidentEvent(
            boat_id=boat_id,
            event_type="AWAKE_CHECK_CONFIRMED",
            description="Operator confirmed awake check.",
            timestamp=now,
        )
    )

    logger.info("Awake check id=%s confirmed for boat_id=%s at %s", pending.id, boat_id, now)
    return pending


# ---------------------------------------------------------------------------
# MODULE 3 — Automatic escalation
# ---------------------------------------------------------------------------

def sweep_and_escalate_expired_checks() -> None:
    """
    Sweep all pending awake checks; expire any past their deadline and
    escalate expired ones into the SOS alert pipeline.

    Runs once per minute via the scheduler. Reuses `sos_service.create_alert`
    rather than duplicating any SOS/alert logic.
    """
    now = datetime.now(timezone.utc)
    pending_checks = get_all_pending_awake_checks()

    for check in pending_checks:
        if now <= check.expires_at:
            continue  # still within the confirmation window

        try:
            check.status = AwakeCheckStatus.EXPIRED
            update_awake_check(check)

            add_incident_event(
                IncidentEvent(
                    boat_id=check.boat_id,
                    event_type="AWAKE_CHECK_EXPIRED",
                    description="Operator failed to confirm awake check in time.",
                    timestamp=now,
                )
            )

            logger.warning(
                "Awake check id=%s EXPIRED for boat_id=%s (expires_at=%s) — escalating to SOS",
                check.id, check.boat_id, check.expires_at,
            )

            create_alert(
                boat_id=check.boat_id,
                alert_type=AlertType.MISSED_AWAKE_CHECK,
                reason=(
                    "Operator failed to respond to the scheduled awake "
                    "check within five minutes."
                ),
                latitude=_DEFAULT_LATITUDE,
                longitude=_DEFAULT_LONGITUDE,
                timestamp=now,
            )

        except Exception:
            logger.exception(
                "Failed to escalate expired awake check id=%s for boat_id=%s",
                check.id, check.boat_id,
            )
