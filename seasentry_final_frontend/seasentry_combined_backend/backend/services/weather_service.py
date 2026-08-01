"""
services/weather_service.py
============================
Weather lookup used to enrich the incident report PDF.

No real weather API key/integration is wired up for this demo, so
`get_weather` uses a mock implementation that simulates a network call
and can fail gracefully. Swap the body of `_fetch_from_provider` with a
real httpx call to a weather API when one is available.
"""

from __future__ import annotations

import logging
import random
from typing import Optional, TypedDict

logger = logging.getLogger("seasentry.weather_service")


class WeatherData(TypedDict):
    wind_speed: str
    wind_direction: str
    temperature: str


def _fetch_from_provider(latitude: float, longitude: float) -> WeatherData:
    """
    Simulate fetching weather data from an external provider.

    Replace this with a real httpx.get(...) call to a weather API
    (e.g. OpenWeatherMap, NOAA) once credentials are available.
    """
    # Deterministic-ish mock values so demos look plausible.
    wind_speed_kmh = round(random.uniform(5, 40), 1)
    wind_direction = random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
    temperature_c = round(random.uniform(24, 34), 1)

    return {
        "wind_speed": f"{wind_speed_kmh} km/h",
        "wind_direction": wind_direction,
        "temperature": f"{temperature_c} °C",
    }


def get_weather(latitude: float, longitude: float) -> Optional[WeatherData]:
    """
    Retrieve weather conditions (wind speed, wind direction, temperature)
    for a given coordinate.

    Returns None if the weather lookup fails, so callers can display
    "Not Available" per the report spec.
    """
    try:
        logger.info("Fetching weather for lat=%s lon=%s", latitude, longitude)
        return _fetch_from_provider(latitude, longitude)
    except Exception:  # pragma: no cover - defensive, mock rarely fails
        logger.exception("Weather lookup failed for lat=%s lon=%s", latitude, longitude)
        return None
