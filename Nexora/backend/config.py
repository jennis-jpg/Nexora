"""
config.py
=========
Central environment-variable loading and validation for the SeaSentry backend.

Load order (highest priority first):
  1. Variables already present in the process environment (Docker / systemd / shell export)
  2. Variables in backend/.env  (local development)

All downstream modules import ``get_settings()`` instead of calling
``os.environ.get()`` directly, so configuration is validated once and
missing-key warnings are printed exactly once at startup.

Usage
-----
In main.py (once, at startup)::

    from config import load_and_validate
    load_and_validate()

Anywhere else::

    from config import get_settings
    key = get_settings().openweathermap_api_key
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("seasentry.config")

_ENV_FILE = Path(__file__).parent / ".env"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE, override=False)
        logger.info("Loaded environment from %s", _ENV_FILE)
    else:
        # Fallback: search parent directories (standard dotenv behaviour)
        load_dotenv(override=False)


def _parse_cors_origins(raw: str) -> list[str]:
    """Accept '*' or a comma-separated list of origins."""
    if raw.strip() == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


# ---------------------------------------------------------------------------
# Settings dataclass — populated once from environment variables
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    # ── Auth ─────────────────────────────────────────────────────────────────
    coastguard_password: str
    """Shared password for fleet-wide coastguard endpoints.
    Leave blank to disable auth (local dev only)."""

    # ── Optional third-party APIs ─────────────────────────────────────────────
    openweathermap_api_key: str | None
    """OpenWeatherMap API key for real wind/temperature data in PDF reports.
    Free tier is sufficient (60 calls/min). Sign up at openweathermap.org.
    If unset, weather data in reports will use simulated values."""

    sea_level_api_key: str | None
    """Reserved for a paid sea-level / tide-gauge provider (e.g. INCOIS).
    Currently unused — the service uses the free Open-Meteo Marine API
    automatically, with no key required."""

    # ── Server ───────────────────────────────────────────────────────────────
    backend_host: str
    backend_port: int
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            coastguard_password=os.environ.get("COASTGUARD_PASSWORD", ""),
            openweathermap_api_key=os.environ.get("OPENWEATHERMAP_API_KEY") or None,
            sea_level_api_key=os.environ.get("SEA_LEVEL_API_KEY") or None,
            backend_host=os.environ.get("BACKEND_HOST", "0.0.0.0"),
            backend_port=int(os.environ.get("BACKEND_PORT", "8000")),
            cors_origins=_parse_cors_origins(os.environ.get("CORS_ORIGINS", "*")),
        )


# ---------------------------------------------------------------------------
# Module-level singleton — replaced on first call after load_and_validate()
# ---------------------------------------------------------------------------

_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings object, building it from env vars if needed."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


# ---------------------------------------------------------------------------
# Public startup function
# ---------------------------------------------------------------------------

def load_and_validate() -> Settings:
    """Load backend/.env into the process environment, validate, log status.

    Call this **once** at the very start of main.py — before the FastAPI app
    is constructed — so all ``os.environ.get()`` calls everywhere else see
    the values from .env.
    """
    _load_dotenv()

    # Force the singleton to be rebuilt now that env vars are loaded
    global _settings
    _settings = None
    settings = get_settings()

    # ── Required variables ────────────────────────────────────────────────────
    if not settings.coastguard_password:
        logger.warning(
            "COASTGUARD_PASSWORD is not set — coastguard endpoints are "
            "UNPROTECTED. Add COASTGUARD_PASSWORD=<password> to backend/.env "
            "(see .env.example) before deploying."
        )

    # ── Optional variables ────────────────────────────────────────────────────
    if not settings.openweathermap_api_key:
        logger.info(
            "OPENWEATHERMAP_API_KEY not set — weather data in PDF reports will "
            "use simulated values. Set it in backend/.env for real weather."
        )

    if not settings.sea_level_api_key:
        logger.info(
            "SEA_LEVEL_API_KEY not set — sea level will use Open-Meteo "
            "(free, no key required) with a simulated-data fallback."
        )

    return settings


# ---------------------------------------------------------------------------
# Config status — safe to expose via API (no secret values)
# ---------------------------------------------------------------------------

def config_status() -> dict:
    """Non-sensitive summary of configured services, safe to return via HTTP."""
    settings = get_settings()
    return {
        "coastguard_auth": bool(settings.coastguard_password),
        "weather_api": (
            "openweathermap (live)"
            if settings.openweathermap_api_key
            else "mock (simulated)"
        ),
        "sea_level_api": "open-meteo (free · no key required)",
        "cors_origins": settings.cors_origins,
        "backend_host": settings.backend_host,
        "backend_port": settings.backend_port,
    }
