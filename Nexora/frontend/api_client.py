"""
api_client.py
NEW FILE, added while integrating -- connects Person B's frontend (which
previously had no backend calls at all; the Predict button was a styled
placeholder) to Person A/C/D's merged backend.

BACKEND_URL must point at wherever the FastAPI backend is actually running.
For local development the default (localhost:8000) just works. For
deployment, set it via Streamlit secrets or an environment variable -- see
the root README.md for exact Render setup steps.

Auth note: coastguard-only endpoints require the X-Coastguard-Key header.
Use ``_coastguard_headers()`` when building requests to those routes.
The key itself is stored in st.session_state["coastguard_key"] after a
successful call to ``verify_coastguard_password()``.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
import streamlit as st

DEFAULT_BACKEND_URL = "http://localhost:8000"


def _backend_url() -> str:
    try:
        if "BACKEND_URL" in st.secrets:
            return st.secrets["BACKEND_URL"]
    except Exception:
        pass
    return os.environ.get("BACKEND_URL", DEFAULT_BACKEND_URL)


def _coastguard_headers() -> dict[str, str]:
    """Return headers required by fleet-wide coastguard endpoints.

    Attaches the X-Coastguard-Key stored in session state after a
    successful login.  Falls back to an empty string (which the backend
    will reject with 401 if COASTGUARD_PASSWORD is configured).
    """
    return {"X-Coastguard-Key": st.session_state.get("coastguard_key", "")}


def verify_coastguard_password(password: str) -> bool:
    """POST /coastguard/login to verify a shared password.

    Returns True on success (HTTP 200 ``{"ok": true}``).
    Returns False on 401 or any network/HTTP error — callers should
    show a generic "Incorrect password" message rather than surfacing
    backend details.

    The password is sent in the JSON body, never in a URL parameter.
    """
    try:
        resp = requests.post(
            f"{_backend_url()}/coastguard/login",
            json={"password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        return False
    except Exception:
        return False


def call_fleet_status() -> dict[str, Any]:
    """GET /risk-status — fleet-wide status for all tracked boats.

    Requires the X-Coastguard-Key header (attached automatically from
    session state).  Raises requests.RequestException on failure.
    """
    resp = requests.get(
        f"{_backend_url()}/risk-status",
        headers=_coastguard_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def call_predict(
    lat: float,
    lon: float,
    speed_kn: float,
    heading_deg: float,
    engine_off: bool = False,
    language: str = "tamil",
    vessel_id: str = "boat_1",
) -> dict[str, Any]:
    """Calls POST /predict on the backend. Raises requests.RequestException
    on network/HTTP failure -- callers should catch this and show a
    friendly error rather than letting Streamlit crash."""
    resp = requests.post(
        f"{_backend_url()}/predict",
        json={
            "boat_id": vessel_id,
            "lat": lat,
            "lon": lon,
            "speed_knots": speed_kn,
            "heading_deg": heading_deg,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def call_border() -> list[dict[str, float]]:
    """Calls GET /border once; cache the result in session_state so we
    don't refetch the (unchanging) boundary line on every rerun."""
    resp = requests.get(f"{_backend_url()}/border", timeout=10)
    resp.raise_for_status()
    return resp.json()["points"]


def audio_url(filename: str | None) -> str | None:
    if not filename:
        return None
    return f"{_backend_url()}/audio/{filename}"


_RISK_MAP = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH"}

# Browser speechSynthesis language codes, used as a fallback (see
# audio_player.py) whenever voice_resolver.py has no recorded clip for the
# requested language.
_TTS_LANG_CODES = {
    "kannada": "kn-IN",
    "tamil":   "ta-IN",
    "english": "en-IN",
}


def call_sos(boat_id: str, lat: float, lon: float) -> dict[str, Any] | None:
    """POST /sos — trigger an SOS alert for a boat.

    Returns the backend response dict on success, or None on any
    network/HTTP failure so callers can degrade gracefully (the SOS
    is still recorded locally via session state even when offline).
    """
    try:
        resp = requests.post(
            f"{_backend_url()}/sos",
            json={
                "boat_id": boat_id,
                "latitude": lat,
                "longitude": lon,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def call_sea_level(lat: float, lon: float) -> dict[str, Any] | None:
    """GET /sea-level?lat=...&lon=... — returns sea-water level data.

    Returns None on any network/HTTP failure so callers can degrade
    gracefully (e.g. show a "—" placeholder card)."""
    try:
        resp = requests.get(
            f"{_backend_url()}/sea-level",
            params={"lat": lat, "lon": lon},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def call_predicted_sea_level(
    boat_id: str,
    lat: float,
    lon: float,
) -> dict[str, Any] | None:
    """GET /predict/sea-level/{boat_id} — three-tier sea-water level prediction.

    Returns {"tier": str, "level_m": float, "trend": str} on success,
    or None on any network/HTTP failure so callers can degrade gracefully.
    """
    try:
        resp = requests.get(
            f"{_backend_url()}/predict/sea-level/{boat_id}",
            params={"latitude": lat, "longitude": lon},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def to_vessel_dict(
    prediction: dict[str, Any],
    lat: float,
    lon: float,
    heading_deg: float,
    speed_kn: float,
    language: str = "tamil",
) -> dict[str, Any]:
    """Adapts the backend's /predict response into the shape controls.py /
    fisherman_dashboard.py expect.

    Backend /predict returns:
      boundary_status.risk        → "Low" | "Medium" | "High"
      boundary_status.distance_nm → float (nautical miles to boundary)
      boundary_status.eta_minutes → float | None
      crossed_now                 → bool
      predicted_track             → list of {lat, lon} dicts
    """
    bs = prediction.get("boundary_status", {})

    risk_raw = bs.get("risk", "Low").lower()
    risk_level = _RISK_MAP.get(risk_raw, "LOW")

    distance_nm = float(bs.get("distance_nm", 999.0))
    eta_raw = bs.get("eta_minutes")
    minutes = float(eta_raw) if eta_raw is not None else 999.0

    crossed = bool(prediction.get("crossed_now", False))

    if risk_level == "HIGH":
        alert_msg = f"DANGER: Crossing in {minutes:.0f} min! Turn back immediately."
    elif risk_level == "MEDIUM":
        alert_msg = f"Caution: {minutes:.0f} min to boundary. Move away from border."
    else:
        alert_msg = "You are safe. Boundary crossing not expected soon."

    track = prediction.get("predicted_track", [])
    pred_lat = track[-1]["lat"] if track else lat
    pred_lon = track[-1]["lon"] if track else lon

    has_recording = language in ("tamil", "kannada")

    return {
        "latitude": lat,
        "longitude": lon,
        "heading_deg": heading_deg,
        "speed_knots": speed_kn,
        "risk_level": risk_level,
        "distance_to_boundary_nm": distance_nm,
        "eta_to_boundary_min": minutes,
        "current_speed_kn": 0.0,
        "current_direction_deg": 0.0,
        "wind_speed_kn": 0.0,
        "wind_direction_deg": 0.0,
        "alert_message": alert_msg,
        "safe_heading_deg": heading_deg,
        "turn_direction": "Hold course" if risk_level == "LOW" else "Turn back",
        "voice_alert_status": (
            f"{language.title()} · recorded clip · {risk_level.lower()} risk"
            if has_recording
            else f"{language.title()} · browser speech"
        ),
        "pred_latitude": pred_lat,
        "pred_longitude": pred_lon,
        "voice_file": None,
        "alarm_file": None,
        "already_crossed": crossed,
        "tts_lang_code": _TTS_LANG_CODES.get(language, "en-IN"),
    }
