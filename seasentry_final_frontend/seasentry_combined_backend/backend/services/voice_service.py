"""
services/voice_service.py
===========================
Person C — Voice Alert Layer.

Generates the text of a risk-based navigation alert (English text, used
both directly and as the caption for the pre-recorded Kannada MP3s), and
resolves which audio asset the frontend should play for a given risk
level + language.

NOTE: This is adapted from Person C's original `alert_generator.py`.
The original also imported `voice_engine.py` (pyttsx3 + playsound) to
speak alerts out loud locally — that only makes sense on a machine with
speakers attached, not a backend server, and the API route never called
it (it only used the returned text + a static audio_url). That local
playback code is intentionally NOT wired into this service; the
frontend is expected to play `audio_url` itself (via <audio> for the
Kannada MP3s served from /audio/*, or the Web Speech API / OS TTS for
"system_voice").
"""

from __future__ import annotations

from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Input normalization (accepts loose synonyms from the caller)
# ---------------------------------------------------------------------------

_RISK_SYNONYMS = {
    "safe": "low",
    "normal": "low",
    "low": "low",
    "warning": "medium",
    "alert": "medium",
    "medium": "medium",
    "danger": "high",
    "critical": "high",
    "high": "high",
}

_LANGUAGE_KANNADA = {"kannada", "kn", "kan", "ಕನ್ನಡ"}
_LANGUAGE_ENGLISH = {"english", "en", "eng"}

_KANNADA_AUDIO = {
    "low": "/audio/kannada_safe.mp3",
    "medium": "/audio/kannada_warning.mp3",
    "high": "/audio/kannada_danger.mp3",
}


def normalize_risk(risk_level: str) -> str:
    """Map loose risk-level synonyms (e.g. 'danger', 'critical') to low/medium/high."""
    return _RISK_SYNONYMS.get(risk_level.strip().lower(), risk_level.strip().lower())


def normalize_language(language: str) -> str:
    """Lowercase/trim the language field. Kept separate for validation clarity."""
    return language.strip().lower()


# ---------------------------------------------------------------------------
# Alert text generation
# ---------------------------------------------------------------------------

def generate_alert_text(
    risk_level: str,
    minutes_to_crossing: int,
    turn_direction: str,
    turn_degrees: int,
) -> str:
    """
    Build the plain-English alert message for a risk level.

    Args:
        risk_level: Normalized risk level ('low', 'medium', or 'high').
        minutes_to_crossing: ETA in minutes to the boundary.
        turn_direction: Suggested turn direction (e.g. 'PORT', 'STARBOARD').
        turn_degrees: Suggested turn amount in degrees.

    Returns:
        The alert text (used both as the API's `alert_text` field and,
        in future, as input to a TTS engine on the frontend).
    """
    if risk_level == "low":
        return (
            "Safe. Your vessel is currently safe. "
            "Boundary crossing is not expected soon."
        )
    if risk_level == "medium":
        return (
            f"Warning! Boundary crossing may occur in "
            f"{minutes_to_crossing} minutes. "
            f"Prepare to turn {turn_direction} by {turn_degrees} degrees."
        )
    if risk_level == "high":
        return (
            f"Danger! Boundary crossing predicted in "
            f"{minutes_to_crossing} minutes. "
            f"Turn {turn_direction} by {turn_degrees} degrees immediately."
        )
    return "Unknown risk level."


# ---------------------------------------------------------------------------
# Audio resolution
# ---------------------------------------------------------------------------

def resolve_audio_url(risk_level: str, language: str) -> Optional[str]:
    """
    Resolve which audio asset the frontend should play.

    Kannada risk levels map to a pre-recorded MP3 served from /audio/*.
    English (or any unrecognized language) falls back to "system_voice",
    signalling the frontend should use its own TTS engine with the
    returned alert_text.

    Returns None only if risk_level isn't a recognized low/medium/high.
    """
    if risk_level not in ("low", "medium", "high"):
        return None

    if language in _LANGUAGE_KANNADA:
        return _KANNADA_AUDIO[risk_level]

    # English and any unrecognized language both fall back to system TTS.
    return "system_voice"


def build_alert_response(
    risk_level: str,
    minutes_to_crossing: int,
    turn_direction: str,
    turn_degrees: int,
    language: str,
) -> Tuple[Optional[str], str, str]:
    """
    Normalize inputs and produce (audio_url, alert_text, normalized_risk)
    for the /voice/generate-alert-text route.
    """
    risk = normalize_risk(risk_level)
    lang = normalize_language(language)
    text = generate_alert_text(risk, minutes_to_crossing, turn_direction, turn_degrees)
    audio_url = resolve_audio_url(risk, lang)
    return audio_url, text, risk
