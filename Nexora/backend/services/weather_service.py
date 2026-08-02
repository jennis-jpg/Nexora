"""
services/weather_service.py
============================
Weather lookup used to enrich the incident report PDF.

When ``OPENWEATHERMAP_API_KEY`` is set in backend/.env, this module calls
the OpenWeatherMap Current Weather API (free tier: 60 req/min) to return
real wind speed, wind direction, and temperature for the incident location.

When the key is absent or the call fails, it falls back to deterministic-ish
simulated values so incident reports always contain *something*.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

from typing_extensions import TypedDict

import requests

from config import get_settings

logger = logging.getLogger("seasentry.weather_service")

_OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

_CARDINAL_DIRS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


class WeatherData(TypedDict):
    wind_speed: str
    wind_direction: str
    temperature: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _deg_to_cardinal(degrees: float) -> str:
    """Convert a compass bearing (0–360°) to the nearest 16-point cardinal."""
    return _CARDINAL_DIRS[round(degrees / 22.5) % 16]


def _fetch_from_openweathermap(
    latitude: float,
    longitude: float,
    api_key: str,
) -> WeatherData:
    """Call the OpenWeatherMap Current Weather endpoint (metric units)."""
    resp = requests.get(
        _OWM_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": "metric",
        },
        timeout=8,
    )
    resp.raise_for_status()
    data = resp.json()

    wind = data.get("wind", {})
    main = data.get("main", {})

    wind_kmh = round(wind.get("speed", 0.0) * 3.6, 1)   # m/s → km/h
    wind_dir = _deg_to_cardinal(wind.get("deg", 0.0))
    temp_c = round(main.get("temp", 0.0), 1)

    return {
        "wind_speed": f"{wind_kmh} km/h",
        "wind_direction": wind_dir,
        "temperature": f"{temp_c} °C",
    }


def _fetch_mock(latitude: float, longitude: float) -> WeatherData:
    """Deterministic-ish simulated weather for demos / offline use."""
    wind_speed_kmh = round(random.uniform(5, 40), 1)
    wind_direction = random.choice(_CARDINAL_DIRS[:8])
    temperature_c = round(random.uniform(24, 34), 1)
    return {
        "wind_speed": f"{wind_speed_kmh} km/h",
        "wind_direction": wind_direction,
        "temperature": f"{temperature_c} °C",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_weather(latitude: float, longitude: float) -> Optional[WeatherData]:
    """Retrieve weather conditions (wind speed, direction, temperature).

    Uses OpenWeatherMap when ``OPENWEATHERMAP_API_KEY`` is set in backend/.env;
    falls back to simulated data so reports always have a value.
    """
    settings = get_settings()
    try:
        logger.info("Fetching weather for lat=%s lon=%s", latitude, longitude)
        if settings.openweathermap_api_key:
            logger.debug("Using OpenWeatherMap API")
            return _fetch_from_openweathermap(
                latitude, longitude, settings.openweathermap_api_key
            )
        logger.debug("OPENWEATHERMAP_API_KEY not set — using simulated weather data")
        return _fetch_mock(latitude, longitude)
    except Exception:
        logger.exception(
            "Weather lookup failed for lat=%s lon=%s — falling back to mock",
            latitude,
            longitude,
        )
        return _fetch_mock(latitude, longitude)
