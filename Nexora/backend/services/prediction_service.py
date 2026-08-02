"""
services/prediction_service.py
================================
Person A — Geofencing & Prediction Engine, wrapped as a service module
so it follows the same routes/services pattern as Person B's modules.

Owns:
    - In-memory boat state store (last known boundary/risk status)
    - /predict and /boundary-check business logic (dead reckoning,
      predicted track, crossing detection)
    - Integration with Person B's alert pipeline: a boat transitioning
      INTO "High" risk raises a BOUNDARY_CROSSING alert through
      services.sos_service.create_alert(), exactly the hook both
      Person A's and Person B's original READMEs called for.

NOTE: alerts are only fired on a risk-level *transition* into "High"
(not on every poll) so a boat sitting in the high-risk zone doesn't
spam the Coast Guard pipeline with a duplicate alert on every tick.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from geofence import (
    BOUNDARY_POINTS,
    check_crossing,
    classify_risk,
    closing_speed_and_eta,
    is_in_valid_region,
    predict_track,
)
from models import AlertType, BoatInput, BoundaryCheckInput
from services.sos_service import create_alert

logger = logging.getLogger("seasentry.prediction_service")

# boat_id -> last known status dict (as returned by closing_speed_and_eta,
# plus a "risk" key)
BOAT_STATE: Dict[str, dict] = {}


def knots_to_mps(knots: float) -> float:
    return knots * 0.514444


def get_boundary_points() -> List[dict]:
    """Return the raw B1-B6 boundary line — useful for the frontend map."""
    return [{"lat": lat, "lon": lon} for lat, lon in BOUNDARY_POINTS]


def boundary_check(data: BoundaryCheckInput) -> dict:
    """
    Stateless one-shot check: given a position + heading/speed, return
    distance to the boundary, which side, closing speed, ETA, and risk.
    No state stored and no alert fired — used for quick testing.
    """
    speed_mps = knots_to_mps(data.speed_knots)
    result = closing_speed_and_eta(data.lat, data.lon, speed_mps, data.heading_deg)
    result["risk"] = classify_risk(result["eta_minutes"])
    return result


def _maybe_raise_boundary_alert(boat_id: str, previous_risk: Optional[str], status: dict) -> None:
    """
    Fire a BOUNDARY_CROSSING alert through the shared Coast Guard pipeline
    the moment a boat's risk transitions into "High". No-op on repeat
    High readings so the pipeline isn't spammed every tick.
    """
    if status["risk"] != "High" or previous_risk == "High":
        return

    try:
        create_alert(
            boat_id=boat_id,
            alert_type=AlertType.BOUNDARY_CROSSING,
            reason=(
                f"Boat entered High risk zone — ETA to boundary "
                f"{status['eta_minutes']} min, side={status['side']}, "
                f"nearest segment={status['nearest_segment']}."
            ),
            latitude=status.get("lat", 0.0),
            longitude=status.get("lon", 0.0),
            timestamp=datetime.now(timezone.utc),
        )
    except Exception:
        logger.exception("Failed to raise boundary-crossing alert for boat_id=%s", boat_id)


def predict(data: BoatInput) -> dict:
    """
    Full prediction for a boat: predicted track (for the map animation),
    boundary check, risk level, and whether a crossing occurred relative
    to the boat's last known state. Also drives the Coast Guard alert
    pipeline when a boat newly enters High risk.
    """
    speed_mps = knots_to_mps(data.speed_knots)

    # Region validation — warn but still process if outside known areas.
    # Valid areas: Palk Strait & Gulf of Mannar (9–10°N, 79–80°E) and
    # Karnataka Coast / Arabian Sea (12–15°N, 74–75°E).
    in_region, region_name = is_in_valid_region(data.lat, data.lon)
    if not in_region:
        logger.warning(
            "boat_id=%s is outside all valid operational regions "
            "(lat=%.4f, lon=%.4f). Boundary math will still run but "
            "results may be unreliable for this location.",
            data.boat_id, data.lat, data.lon,
        )

    # Predicted path for the "before/after crossing" simulation on the map
    track = predict_track(
        data.lat, data.lon, speed_mps, data.heading_deg,
        total_seconds=data.predict_minutes * 60, step_seconds=60,
    )

    # Current boundary status
    status = closing_speed_and_eta(data.lat, data.lon, speed_mps, data.heading_deg)
    status["risk"] = classify_risk(status["eta_minutes"])
    status["lat"] = data.lat
    status["lon"] = data.lon

    # Crossing detection vs. last known state for this boat
    previous = BOAT_STATE.get(data.boat_id)
    previous_side = previous["side"] if previous else None
    previous_segment_index = previous["segment_index"] if previous else None
    previous_risk = previous["risk"] if previous else None
    crossed = check_crossing(
        previous_side, status["side"],
        previous_segment_index, status["segment_index"],
    )

    # Find the predicted point (if any) where the track crosses the
    # boundary, for drawing the before/after segments on the frontend map
    crossing_index = None
    prev_side_along_track = status["side"]
    prev_segment_along_track = status["segment_index"]
    for i, (t_lat, t_lon) in enumerate(track[1:], start=1):
        seg_status = closing_speed_and_eta(t_lat, t_lon, speed_mps, data.heading_deg)
        if check_crossing(
            prev_side_along_track, seg_status["side"],
            prev_segment_along_track, seg_status["segment_index"],
        ):
            crossing_index = i
            break
        prev_side_along_track = seg_status["side"]
        prev_segment_along_track = seg_status["segment_index"]

    response = {
        "boat_id": data.boat_id,
        "current_position": {"lat": data.lat, "lon": data.lon},
        "predicted_track": [{"lat": p[0], "lon": p[1]} for p in track],
        "crossing_index": crossing_index,
        "boundary_status": status,
        "crossed_now": crossed,
        "region": region_name or "Unknown",
    }

    # Fire the Coast Guard alert (if this is a new transition into High risk)
    _maybe_raise_boundary_alert(data.boat_id, previous_risk, status)

    # Update state store
    BOAT_STATE[data.boat_id] = status
    return response


def get_risk_status(boat_id: str) -> Optional[dict]:
    """Return the last known boundary/risk status for a given boat."""
    return BOAT_STATE.get(boat_id)


def get_all_risk_status() -> List[dict]:
    """Return last known status for every tracked boat — for the coastguard dashboard."""
    return [{"boat_id": bid, **status} for bid, status in BOAT_STATE.items()]
