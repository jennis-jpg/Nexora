"""
api_client.py
NEW FILE, added while integrating -- connects Person B's frontend (which
previously had no backend calls at all; the Predict button was a styled
placeholder) to Person A/C/D's merged backend.

BACKEND_URL must point at wherever the FastAPI backend is actually running.
For local development the default (localhost:8000) just works. For
deployment, set it via Streamlit secrets or an environment variable -- see
the root README.md for exact Render setup steps.
"""

from __future__ import annotations

import os
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


def call_predict(
    lat: float,
    lon: float,
    speed_kn: float,
    heading_deg: float,
    engine_off: bool,
    language: str = "kannada",
    vessel_id: str = "boat_1",
) -> dict[str, Any]:
    """Calls POST /predict on the backend. Raises requests.RequestException
    on network/HTTP failure -- callers should catch this and show a
    friendly error rather than letting Streamlit crash."""
    resp = requests.post(
        f"{_backend_url()}/predict",
        json={
            "lat": lat,
            "lon": lon,
            "speed_kn": speed_kn,
            "heading_deg": heading_deg,
            "engine_off": engine_off,
            "language": language,
            "vessel_id": vessel_id,
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
# requested language -- currently that's everything except Kannada.
_TTS_LANG_CODES = {
    "kannada": "kn-IN",
    "english": "en-IN",
}


def to_vessel_dict(
    prediction: dict[str, Any],
    lat: float,
    lon: float,
    heading_deg: float,
    speed_kn: float,
    language: str = "kannada",
) -> dict[str, Any]:
    """Adapts the backend's /predict response into the exact shape
    controls.py / dashboard_cards.py expect -- see controls.py's
    DEMO_VESSEL dict for the field contract this must match."""
    turn_direction = prediction.get("turn_direction")
    minutes = prediction.get("minutes_to_crossing")
    has_recording = bool(prediction.get("voice_file"))

    return {
        "latitude": lat,
        "longitude": lon,
        "heading_deg": heading_deg,
        "speed_knots": speed_kn,
        "risk_level": _RISK_MAP.get(prediction["risk_level"], "MEDIUM"),
        "distance_to_boundary_nm": prediction["distance_to_border_nm"],
        "eta_to_boundary_min": minutes if minutes is not None else 999,
        "current_speed_kn": prediction["current_used"]["speed_kn"],
        "current_direction_deg": prediction["current_used"]["dir_deg"],
        "wind_speed_kn": prediction["wind_used"]["speed_kn"],
        "wind_direction_deg": prediction["wind_used"]["dir_deg"],
        "alert_message": prediction["alert_text"],
        "safe_heading_deg": prediction["safe_heading_deg"],
        "turn_direction": turn_direction.title() if turn_direction else "Hold course",
        "voice_alert_status": (
            f"{language.title()} · recorded clip · {prediction['risk_level']} risk"
            if has_recording
            else f"{language.title()} · browser speech (no recording yet)"
        ),
        # extra fields not in the original DEMO_VESSEL contract, used by
        # the map to draw the REAL predicted position and boundary instead
        # of the placeholder geometric approximation, and by the audio
        # player component to decide what to play:
        "pred_latitude": prediction["predicted_position"]["lat"],
        "pred_longitude": prediction["predicted_position"]["lon"],
        "voice_file": prediction.get("voice_file"),
        "alarm_file": prediction.get("alarm_file"),
        "already_crossed": prediction.get("already_crossed", False),
        "tts_lang_code": _TTS_LANG_CODES.get(language, "en-IN"),
    }
