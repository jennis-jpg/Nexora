"""
routes/sea_level.py
=====================
Sea-water level prediction endpoint.

Exposes:
    GET /sea-level?lat=<float>&lon=<float>
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.sea_level_service import SeaLevelData, get_sea_level

router = APIRouter(prefix="/sea-level", tags=["Sea Level"])


@router.get("", summary="Predicted sea-water level for a coordinate")
async def sea_level_endpoint(
    lat: float = Query(..., description="Latitude in decimal degrees"),
    lon: float = Query(..., description="Longitude in decimal degrees"),
) -> SeaLevelData:
    """Return the predicted sea-water level (normal / rising / high) and
    the raw level in metres for the given coordinate."""
    data = get_sea_level(lat, lon)
    if data is None:
        raise HTTPException(status_code=503, detail="Sea level service temporarily unavailable")
    return data
