"""
routes/weather.py
==================
Thin HTTP wrapper around services/weather_service.py.

Exposes:
    GET /weather?lat=<float>&lon=<float>

Returns real OpenWeatherMap data when OPENWEATHERMAP_API_KEY is set in the
environment, otherwise returns simulated weather data so the response is
always populated.  The Coastal Coordination Dashboard calls this endpoint
for each dock station coordinate on every refresh cycle.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.weather_service import get_weather

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", summary="Current weather conditions for a coordinate")
async def weather_endpoint(
    lat: float = Query(..., description="Latitude in decimal degrees"),
    lon: float = Query(..., description="Longitude in decimal degrees"),
) -> dict:
    """Return current weather (wind speed, wind direction, temperature) for a
    coordinate.

    Delegates to OpenWeatherMap when ``OPENWEATHERMAP_API_KEY`` is configured,
    falling back to deterministic-ish simulated data so the endpoint always
    returns HTTP 200 regardless of external service availability.

    Response shape::

        {
            "wind_speed":     "14.4 km/h",
            "wind_direction": "SE",
            "temperature":    "28.3 °C"
        }
    """
    data = get_weather(lat, lon)
    if data is None:
        raise HTTPException(status_code=503, detail="Weather service temporarily unavailable")
    return data
