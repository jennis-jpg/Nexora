"""services/ai_service.py
========================
Ollama AI integration for SeaSentry Coast Guard tactical briefings.

Calls the local Ollama HTTP API directly (no ollama Python package needed).
Configuration via environment variables — falls back to defaults if absent:

    OLLAMA_URL   http://localhost:11434   Base URL of the Ollama server
    OLLAMA_MODEL qwen2.5:3b              Model to use for inference

Run Ollama locally before starting the backend:
    ollama serve
    ollama pull qwen2.5:3b
"""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger("seasentry.services.ai")

_OLLAMA_URL   = os.environ.get("OLLAMA_URL",   "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

_GENERATE_ENDPOINT = f"{_OLLAMA_URL.rstrip('/')}/api/generate"

_FALLBACK = (
    "AI briefing unavailable — Ollama service is offline or model not loaded. "
    "Proceed with standard Coast Guard emergency response protocol."
)

_PROMPT_TEMPLATE = """\
You are a Coast Guard tactical AI. A maritime emergency has been reported.
Provide a concise 2-sentence tactical risk assessment and the single most
important immediate action the Coast Guard should take right now.
Do not include bullet points, numbering, or headers — plain sentences only.

Incident details:
- Vessel name  : {vessel_name}
- Distance to maritime boundary: {distance_km:.1f} km
- GPS status   : {gps_status}
- Alert reason : {alert_reason}
"""


def generate_tactical_brief(
    vessel_name: str,
    distance_km: float,
    gps_status: str,
    alert_reason: str,
) -> str:
    """Call the local Ollama /api/generate endpoint for a tactical briefing.

    Parameters
    ----------
    vessel_name   : Name or ID of the vessel in distress.
    distance_km   : Distance from the maritime boundary in kilometres.
    gps_status    : Current GPS status string (e.g. "GPS OK", "Signal Lost").
    alert_reason  : Short description of why the alert was triggered.

    Returns
    -------
    A 2-sentence string with a risk assessment and recommended action,
    or a safe fallback message if Ollama is unreachable.
    """
    prompt = _PROMPT_TEMPLATE.format(
        vessel_name=vessel_name,
        distance_km=distance_km,
        gps_status=gps_status,
        alert_reason=alert_reason,
    )

    payload = {
        "model": _OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 120,
        },
    }

    try:
        resp = requests.post(_GENERATE_ENDPOINT, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        brief: str = data.get("response", "").strip()
        if not brief:
            logger.warning("Ollama returned empty response — using fallback")
            return _FALLBACK
        logger.info("AI brief generated for vessel '%s' via %s", vessel_name, _OLLAMA_MODEL)
        return brief

    except requests.exceptions.ConnectionError:
        logger.warning("Ollama not reachable at %s — returning fallback brief", _GENERATE_ENDPOINT)
        return _FALLBACK

    except Exception as exc:  # noqa: BLE001
        logger.warning("Ollama call failed (%s: %s) — returning fallback brief",
                       type(exc).__name__, exc)
        return _FALLBACK
