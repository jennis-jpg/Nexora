"""
services/sea_level_service.py
==============================
Sea-water level lookup using Open-Meteo Marine API.

Open-Meteo (https://open-meteo.com/en/docs/marine-weather-api) provides free
wave height forecasts with no API key required for non-commercial use.
The ``wave_height`` field is used as a practical proxy for sea state.

Fallback: if the HTTP call fails (offline, outside ocean coverage area, etc.)
the service returns deterministic-ish simulated values so the frontend always
has something to display.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

from typing_extensions import TypedDict

import requests

logger = logging.getLogger("seasentry.sea_level_service")

_OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"


class SeaLevelData(TypedDict):
    status: str        # "normal" | "rising" | "high"
    level_m: float     # wave height in metres (proxy for sea state)
    description: str   # brief human-readable summary


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _classify(level_m: float) -> SeaLevelData:
    level_m = round(level_m, 2)
    if level_m >= 2.0:
        return {
            "status": "high",
            "level_m": level_m,
            "description": "Increased risk — high swell",
        }
    if level_m >= 1.0:
        return {
            "status": "rising",
            "level_m": level_m,
            "description": "Take precaution — rising swell",
        }
    return {
        "status": "normal",
        "level_m": level_m,
        "description": "Normal sea level",
    }


def _fetch_from_open_meteo(latitude: float, longitude: float) -> SeaLevelData:
    """Call the free Open-Meteo Marine API — no API key required."""
    resp = requests.get(
        _OPEN_METEO_MARINE_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "wave_height",
            "forecast_days": 1,
        },
        timeout=8,
    )
    resp.raise_for_status()
    data = resp.json()

    wave_height = data.get("current", {}).get("wave_height")
    if wave_height is None:
        raise ValueError(
            "Open-Meteo response missing 'current.wave_height' "
            f"(location may be inland or outside ocean model coverage). "
            f"Response: {data}"
        )
    return _classify(float(wave_height))


def _fetch_mock(latitude: float, longitude: float) -> SeaLevelData:
    """Simulated sea level for demos and offline fallback."""
    level_m = round(random.uniform(0.2, 2.8), 2)
    return _classify(level_m)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_sea_level(latitude: float, longitude: float) -> Optional[SeaLevelData]:
    """Retrieve predicted sea-water level for a coordinate.

    Tries the free Open-Meteo Marine API first; falls back to simulated data
    if the call fails (network issues, coordinates outside ocean model, etc.)
    so the frontend always receives a valid response.
    """
    try:
        logger.info("Fetching sea level for lat=%s lon=%s", latitude, longitude)
        return _fetch_from_open_meteo(latitude, longitude)
    except Exception:
        logger.warning(
            "Open-Meteo sea level call failed for lat=%s lon=%s — using mock",
            latitude,
            longitude,
        )
        return _fetch_mock(latitude, longitude)


# ---------------------------------------------------------------------------
# Predicted sea-water level (new tier/trend schema for the droplet component)
# ---------------------------------------------------------------------------

def get_predicted_sea_level(latitude: float, longitude: float) -> dict:
    """Return a three-tier sea-water level prediction for the droplet UI card.

    Schema: {"tier": "normal"|"rising"|"high", "level_m": float, "trend": str}

    Currently mocked with realistic random values — swap the body of this
    function for a real tidal/oceanographic data provider (INCOIS, NOAA CO-OPS,
    Copernicus Marine) when credentials are available.  The calling route and
    frontend component are provider-agnostic; only this function changes.

    Tier thresholds:  < 0.6 m → normal  |  0.6–1.2 m → rising  |  > 1.2 m → high
    """
    level_m = round(random.uniform(0.1, 1.8), 2)

    if level_m < 0.6:
        tier = "normal"
    elif level_m <= 1.2:
        tier = "rising"
    else:
        tier = "high"

    trend = random.choice(["rising", "falling", "steady"])

    return {"tier": tier, "level_m": level_m, "trend": trend}
