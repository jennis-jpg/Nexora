"""
routes/incidents.py
====================
Expose the in-memory incident event timeline to the frontend.

Exposes:
    GET /incidents/{boat_id}   — events for one boat
    GET /incidents             — events for all boats that have records

This allows the Coastal Coordination Dashboard to display a live incident
feed without needing the full PDF generation pipeline.  The underlying data
store is the same database.py that SOS, awake-check, and prediction services
write to — no duplication of logic.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from database import ACTIVE_BOATS, get_incident_events
from services.prediction_service import BOAT_STATE

logger = logging.getLogger("seasentry.routes.incidents")

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _serialise_events(boat_id: str) -> list[dict]:
    """Return incident events for a boat as JSON-safe dicts."""
    events = get_incident_events(boat_id)
    return [
        {
            "boat_id": e.boat_id,
            "event_type": e.event_type,
            "description": e.description,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]


@router.get("/{boat_id}", summary="Get the incident event timeline for a boat")
async def get_boat_incidents(boat_id: str) -> dict:
    """Return all recorded incident events for a given boat in chronological order.

    Events are written by: SOS reception, awake-check escalation, boundary-crossing
    alert creation, and Coast Guard dispatch acknowledgement.  Returns an empty list
    if no events have been recorded yet (boat has never sent data).

    Response shape::

        {
            "boat_id": "BOAT001",
            "events": [
                {
                    "boat_id": "BOAT001",
                    "event_type": "SOS_RECEIVED",
                    "description": "Manual SOS triggered by operator/device.",
                    "timestamp": "2025-06-01T09:18:22+00:00"
                },
                ...
            ],
            "count": 3
        }
    """
    events = _serialise_events(boat_id)
    return {"boat_id": boat_id, "events": events, "count": len(events)}


@router.get("", summary="Get incident events for all tracked boats")
async def get_all_incidents() -> dict:
    """Return incident events for every boat that has produced at least one event.

    Combines ACTIVE_BOATS (the demo fleet the scheduler creates awake checks
    for) with BOAT_STATE keys (boats that have been submitted to /predict) to
    give a comprehensive picture of the fleet.

    Response shape::

        {
            "incidents": {
                "BOAT001": [...events...],
                "BOAT002": [...events...]
            },
            "total_boats_with_incidents": 2
        }
    """
    # Union of pre-configured demo boats and any boat that has been predicted
    all_ids: set[str] = set(ACTIVE_BOATS) | set(BOAT_STATE.keys())
    result: dict[str, list] = {}
    for bid in all_ids:
        events = _serialise_events(bid)
        if events:
            result[bid] = events

    return {
        "incidents": result,
        "total_boats_with_incidents": len(result),
    }
