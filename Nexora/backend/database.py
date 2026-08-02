"""
database.py
============
Lightweight in-memory "database" for Person B's Safety & Alerting System.

For the demo, all state is kept in process memory guarded by simple
data structures. This is intentionally swappable: replace the internals
of this module with real SQLite/SQLAlchemy calls later without touching
any route or service code, since all access goes through the functions
defined here.

NOTE: In-memory storage means data resets on process restart. That is
acceptable for this demo/prototype phase.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from itertools import count
from typing import Dict, List, Optional

from models import AwakeCheckRecord, AwakeCheckStatus, IncidentEvent

logger = logging.getLogger("seasentry.database")

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_lock = threading.RLock()

# boat_id -> list of awake check records (most recent last)
_awake_checks: Dict[str, List[AwakeCheckRecord]] = {}

# boat_id -> list of incident/timeline events (chronological)
_incident_events: Dict[str, List[IncidentEvent]] = {}

# Demo list of "active" boats that the scheduler creates awake checks for.
# In production this would come from a fleet/registration table.
ACTIVE_BOATS: List[str] = ["BOAT001", "BOAT002", "BOAT003"]

_awake_check_id_counter = count(start=1)


# ---------------------------------------------------------------------------
# Awake check persistence
# ---------------------------------------------------------------------------

def create_awake_check(boat_id: str, created_at: datetime, expires_at: datetime) -> AwakeCheckRecord:
    """Create and store a new pending awake check for a boat."""
    with _lock:
        record = AwakeCheckRecord(
            id=next(_awake_check_id_counter),
            boat_id=boat_id,
            created_at=created_at,
            expires_at=expires_at,
            status=AwakeCheckStatus.PENDING,
        )
        _awake_checks.setdefault(boat_id, []).append(record)
        logger.info("Created awake check id=%s for boat_id=%s expires_at=%s",
                    record.id, boat_id, expires_at)
        return record


def get_latest_awake_check(boat_id: str) -> Optional[AwakeCheckRecord]:
    """Return the most recently created awake check for a boat, if any."""
    with _lock:
        checks = _awake_checks.get(boat_id)
        if not checks:
            return None
        return checks[-1]


def get_latest_pending_awake_check(boat_id: str) -> Optional[AwakeCheckRecord]:
    """Return the latest awake check for a boat only if it is still pending."""
    latest = get_latest_awake_check(boat_id)
    if latest and latest.status == AwakeCheckStatus.PENDING:
        return latest
    return None


def update_awake_check(record: AwakeCheckRecord) -> None:
    """Persist an updated awake check record back into the store."""
    with _lock:
        checks = _awake_checks.get(record.boat_id, [])
        for idx, existing in enumerate(checks):
            if existing.id == record.id:
                checks[idx] = record
                logger.debug("Updated awake check id=%s status=%s", record.id, record.status)
                return
        logger.warning("Attempted to update unknown awake check id=%s", record.id)


def get_all_pending_awake_checks() -> List[AwakeCheckRecord]:
    """Return every awake check across all boats that is currently pending."""
    with _lock:
        pending = []
        for checks in _awake_checks.values():
            latest = checks[-1] if checks else None
            if latest and latest.status == AwakeCheckStatus.PENDING:
                pending.append(latest)
        return pending


# ---------------------------------------------------------------------------
# Incident / timeline event persistence
# ---------------------------------------------------------------------------

def add_incident_event(event: IncidentEvent) -> None:
    """Append an event to a boat's chronological incident timeline."""
    with _lock:
        _incident_events.setdefault(event.boat_id, []).append(event)
        logger.debug("Recorded event '%s' for boat_id=%s", event.event_type, event.boat_id)


def get_incident_events(boat_id: str) -> List[IncidentEvent]:
    """Return all recorded events for a boat in chronological order."""
    with _lock:
        return list(_incident_events.get(boat_id, []))
