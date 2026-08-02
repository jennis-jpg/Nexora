"""
routes/voice.py
=================
Person C — Voice Alert Layer.

Exposes:
    POST /voice/generate-alert-text
    GET  /voice/alert-audio/{alert_id}

Static Kannada MP3s are served separately from /audio/* (mounted in
main.py), so the audio_url values returned here can be played directly
by the frontend.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from services.voice_service import build_alert_response, normalize_language, resolve_audio_url

logger = logging.getLogger("seasentry.routes.voice")

router = APIRouter(prefix="/voice", tags=["Voice Alerts"])


class AlertRequest(BaseModel):
    """Incoming payload describing the risk situation to voice-alert on."""

    risk_level: str
    minutes_to_crossing: int
    turn_direction: str
    turn_degrees: int
    language: str = "english"


@router.post("/generate-alert-text", summary="Generate a risk-based voice alert")
async def generate_alert_text_route(request: AlertRequest) -> dict:
    """
    Generate the alert text (and the audio asset to play) for a given
    risk level, ETA, suggested turn, and language.

    Accepts loose synonyms for risk_level (e.g. "danger", "critical" ->
    "high") and language ("kn", "ಕನ್ನಡ" -> Kannada).
    """
    audio_url, alert_text, risk = build_alert_response(
        risk_level=request.risk_level,
        minutes_to_crossing=request.minutes_to_crossing,
        turn_direction=request.turn_direction,
        turn_degrees=request.turn_degrees,
        language=request.language,
    )

    if audio_url is None:
        return {"error": "Unsupported risk or language"}

    return {
        "alert_id": f"SEA-{datetime.now(timezone.utc).strftime('%H%M%S')}",
        "risk": risk,
        "language": normalize_language(request.language),
        "alert_text": alert_text,
        "audio_url": audio_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "voice alert generated",
    }


@router.get("/alert-audio/{alert_id}", summary="Resolve the audio asset for a risk level")
async def get_alert_audio(alert_id: str, lang: str = "english") -> dict:
    """
    Resolve the audio_url for a risk-level keyword and language.

    NOTE: despite the path name, `alert_id` here is a risk-level keyword
    (e.g. "safe", "warning", "danger", "high"), matching Person C's
    original design — it is not the `alert_id` returned by
    /generate-alert-text. Kept as-is for compatibility with the
    existing frontend calls; consider renaming to /alert-audio/{risk}
    in a future revision to avoid the confusion.
    """
    alert_id = alert_id.lower()
    lang = lang.lower()

    aliases = {"safe": "low", "warning": "medium", "danger": "high", "critical": "high"}
    risk = aliases.get(alert_id, alert_id)

    audio_url = resolve_audio_url(risk, lang)
    if audio_url is None:
        return {"error": "Invalid alert_id or language"}
    return {"audio_url": audio_url}
