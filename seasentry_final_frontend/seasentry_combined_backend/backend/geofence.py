"""
geofence.py
Person A — Geofencing & Prediction Engine

Implements:
  - Dead reckoning (predicted position from speed/heading)
  - Side test (which side of the India-Sri Lanka boundary line the boat is on)
  - Cross-track distance (perpendicular distance to the boundary)
  - Closing speed + ETA (time until the boat reaches the line)
  - Risk classification (High / Medium / Low)

All boundary math works on the India-Sri Lanka maritime boundary line,
defined as an ordered sequence of points B1 -> B6 (NOT a closed polygon).
"""

import math

R_EARTH = 6371000  # meters

# Unit conversion constants
METERS_PER_NM = 1852.0       # 1 nautical mile = 1852 meters
MPS_PER_KNOT = 0.514444      # 1 knot = 0.514444 m/s


def meters_to_nm(meters):
    return meters / METERS_PER_NM


def mps_to_knots(mps):
    return mps / MPS_PER_KNOT

# ---------------------------------------------------------------------------
# Boundary definition (decimal degrees, lat/lon)
# ---------------------------------------------------------------------------
BOUNDARY_POINTS = [
    (10.0833, 80.0500),   # B1 - Palk Strait Entrance
    (9.9500,  79.5833),   # B2 - Palk Bay Northeast
    (9.6692,  79.3767),   # B3 - West of Delft Island
    (9.3633,  79.5117),   # B4 - Near Katchatheevu Island
    (9.2167,  79.5333),   # B5 - Approaching Adam's Bridge
    (9.1000,  79.5333),   # B6 - Adam's Bridge Shoals
]

RISK_HIGH_MAX_MIN = 16     # < 16 min  -> High
RISK_MEDIUM_MAX_MIN = 29   # 16-29 min -> Medium
                            # > 29 min  -> Low


# ---------------------------------------------------------------------------
# 1. Dead Reckoning
# ---------------------------------------------------------------------------
def dead_reckon(lat, lon, speed_mps, heading_deg, dt_seconds):
    """
    Predict a new (lat, lon) after dt_seconds, given current speed (m/s)
    and heading (degrees, 0 = North, clockwise).
    """
    heading_rad = math.radians(heading_deg)
    distance = speed_mps * dt_seconds  # meters travelled

    d_lat = (distance * math.cos(heading_rad)) / R_EARTH
    d_lon = (distance * math.sin(heading_rad)) / (R_EARTH * math.cos(math.radians(lat)))

    new_lat = lat + math.degrees(d_lat)
    new_lon = lon + math.degrees(d_lon)
    return new_lat, new_lon


def predict_track(lat, lon, speed_mps, heading_deg, total_seconds=3600, step_seconds=60):
    """
    Generate a predicted path as a list of (lat, lon) points,
    stepping forward every `step_seconds` up to `total_seconds`.
    Used to draw the "before crossing" simulation path on the frontend.
    """
    track = [(lat, lon)]
    cur_lat, cur_lon = lat, lon
    steps = int(total_seconds / step_seconds)
    for _ in range(steps):
        cur_lat, cur_lon = dead_reckon(cur_lat, cur_lon, speed_mps, heading_deg, step_seconds)
        track.append((cur_lat, cur_lon))
    return track


# ---------------------------------------------------------------------------
# 2. Local planar projection (equirectangular, centered on the boat)
#    Good enough for distances of a few hundred km near the equator.
# ---------------------------------------------------------------------------
def to_xy(lat, lon, ref_lat, ref_lon):
    x = math.radians(lon - ref_lon) * math.cos(math.radians(ref_lat)) * R_EARTH
    y = math.radians(lat - ref_lat) * R_EARTH
    return x, y


# ---------------------------------------------------------------------------
# 3. Side test + cross-track distance against ONE segment
# ---------------------------------------------------------------------------
def _segment_check(px, py, x1, y1, x2, y2):
    """
    Given a point (px, py) and a segment (x1,y1)-(x2,y2) in local planar
    coordinates, return:
      - dist: perpendicular distance from point to segment (meters)
      - side: +1 or -1 (which side of the line the point is on)
      - cross: the raw cross product (used for closing-speed calc)
      - seg_len: length of the segment (used for closing-speed calc)
    """
    dx, dy = x2 - x1, y2 - y1
    seg_len2 = dx * dx + dy * dy

    if seg_len2 == 0:
        t = 0.0
    else:
        t = ((px - x1) * dx + (py - y1) * dy) / seg_len2
        t = max(0.0, min(1.0, t))  # clamp to segment (not infinite line)

    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    dist = math.hypot(px - closest_x, py - closest_y)

    cross = dx * (py - y1) - dy * (px - x1)
    side = 1 if cross > 0 else (-1 if cross < 0 else 0)
    seg_len = math.sqrt(seg_len2) if seg_len2 > 0 else 1e-9

    return dist, side, cross, seg_len, dx, dy


def nearest_boundary_segment(lat, lon):
    """
    Check the boat's position against every B1-B6 segment and return
    details for the CLOSEST one — that's the one that matters for
    crossing detection and risk classification.
    """
    px, py = to_xy(lat, lon, lat, lon)  # boat is the origin (0,0) of its own frame

    best = None
    for i in range(len(BOUNDARY_POINTS) - 1):
        lat1, lon1 = BOUNDARY_POINTS[i]
        lat2, lon2 = BOUNDARY_POINTS[i + 1]
        x1, y1 = to_xy(lat1, lon1, lat, lon)
        x2, y2 = to_xy(lat2, lon2, lat, lon)

        dist, side, cross, seg_len, dx, dy = _segment_check(px, py, x1, y1, x2, y2)

        if best is None or dist < best["dist"]:
            best = {
                "segment_index": i,
                "segment": (f"B{i+1}", f"B{i+2}"),
                "dist": dist,
                "side": side,
                "cross": cross,
                "seg_len": seg_len,
                "dx": dx,
                "dy": dy,
            }
    return best


# ---------------------------------------------------------------------------
# 4. Closing speed + ETA
# ---------------------------------------------------------------------------
def closing_speed_and_eta(lat, lon, speed_mps, heading_deg):
    """
    Returns (distance_nm, side, closing_speed_knots, eta_minutes).

    closing_speed > 0  -> boat is heading TOWARD the boundary (distance shrinking)
    closing_speed <= 0 -> boat is heading away; ETA is treated as None (Low risk)
    """
    seg = nearest_boundary_segment(lat, lon)
    dist = seg["dist"]
    side = seg["side"]
    dx, dy = seg["dx"], seg["dy"]
    seg_len = seg["seg_len"]

    heading_rad = math.radians(heading_deg)
    vx = speed_mps * math.sin(heading_rad)  # east component
    vy = speed_mps * math.cos(heading_rad)  # north component

    # d(cross)/dt = dx*vy - dy*vx  (segment endpoints treated as fixed)
    d_cross_dt = dx * vy - dy * vx
    sign = 1 if seg["cross"] >= 0 else -1
    d_dist_dt = (sign * d_cross_dt) / seg_len  # rate of change of distance (m/s)
    closing_speed = -d_dist_dt  # positive = approaching the line

    if closing_speed <= 0 or dist == 0:
        eta_minutes = None
    else:
        eta_minutes = (dist / closing_speed) / 60.0

    return {
        "distance_nm": round(meters_to_nm(dist), 3),
        "side": "India" if side > 0 else "Sri Lanka" if side < 0 else "On the line",
        "nearest_segment": seg["segment"],
        "segment_index": seg["segment_index"],
        "closing_speed_knots": round(mps_to_knots(closing_speed), 2),
        "eta_minutes": round(eta_minutes, 1) if eta_minutes is not None else None,
    }


# ---------------------------------------------------------------------------
# 5. Risk classification
# ---------------------------------------------------------------------------
def classify_risk(eta_minutes):
    if eta_minutes is None:
        return "Low"
    if eta_minutes < RISK_HIGH_MAX_MIN:
        return "High"
    if eta_minutes <= RISK_MEDIUM_MAX_MIN:
        return "Medium"
    return "Low"


def check_crossing(previous_side, current_side, previous_segment_index=None, current_segment_index=None):
    """
    A crossing has occurred if the side flipped between the last check
    and this one (and neither is None/on-the-line) AND the nearest
    segment stayed the same across both checks.

    Requiring the same segment index prevents false positives that can
    happen near a bend in the boundary (e.g. near B3), where the
    "nearest segment" itself can switch between checks and flip the
    side sign without the boat actually crossing the line.
    """
    if previous_side is None:
        return False
    if "line" in (previous_side, current_side):
        return False
    if previous_side == current_side:
        return False
    # If we don't have segment info, fall back to the old behavior.
    if previous_segment_index is None or current_segment_index is None:
        return True
    return previous_segment_index == current_segment_index
