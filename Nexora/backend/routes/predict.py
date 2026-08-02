"""
routes/predict.py
===================
Person A — Geofencing & Prediction Engine.

Exposes:
    GET  /boundary-points
    POST /boundary-check
    POST /predict
    GET  /risk-status/{boat_id}
    GET  /risk-status
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from dependencies.coastguard_auth import verify_coastguard_key
from models import BoatInput, BoundaryCheckInput, SeaLevelResponse
from services import prediction_service
from services.sea_level_service import get_predicted_sea_level

logger = logging.getLogger("seasentry.routes.predict")

router = APIRouter(tags=["Prediction Engine"])


@router.get("/boundary-points", summary="Raw B1-B6 boundary line coordinates")
async def get_boundary_points() -> dict:
    """Returns the raw B1-B6 boundary line — useful for the frontend map."""
    return {"boundary": prediction_service.get_boundary_points()}


@router.post("/boundary-check", summary="Stateless one-shot boundary check")
async def boundary_check(data: BoundaryCheckInput) -> dict:
    """
    Given a position + heading/speed, return distance to the boundary,
    which side, closing speed, ETA, and risk level. No state stored —
    useful for quick testing or a stateless call.
    """
    try:
        return prediction_service.boundary_check(data)
    except Exception as exc:
        logger.exception("Unhandled error during boundary check")
        raise HTTPException(status_code=500, detail="Failed to perform boundary check.") from exc


@router.post("/predict", summary="Full prediction for a boat")
async def predict(data: BoatInput) -> dict:
    """
    Full prediction for a boat: predicted track (for the map animation),
    boundary check, risk level, and whether a crossing occurred relative
    to the boat's last known state. Automatically raises a Coast Guard
    alert if the boat newly enters High risk.
    """
    try:
        return prediction_service.predict(data)
    except Exception as exc:
        logger.exception("Unhandled error during prediction for boat_id=%s", data.boat_id)
        raise HTTPException(status_code=500, detail="Failed to generate prediction.") from exc


@router.get("/risk-status/{boat_id}", summary="Last known risk status for one boat")
async def risk_status(boat_id: str) -> dict:
    """Returns the last known boundary/risk status for a given boat."""
    status = prediction_service.get_risk_status(boat_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"No status recorded yet for boat '{boat_id}'")
    return {"boat_id": boat_id, **status}


@router.get(
    "/risk-status",
    summary="Last known risk status for all tracked boats",
    dependencies=[Depends(verify_coastguard_key)],
)
async def all_risk_status() -> dict:
    """
    Returns last known status for every tracked boat — for the coastguard
    dashboard.

    Requires a valid ``X-Coastguard-Key`` header when
    ``COASTGUARD_PASSWORD`` is set in the environment.
    """
    return {"boats": prediction_service.get_all_risk_status()}


@router.get(
    "/predict/sea-level/{boat_id}",
    response_model=SeaLevelResponse,
    summary="Predicted sea-water level tier for a boat",
)
async def predicted_sea_level(
    boat_id: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> SeaLevelResponse:
    """
    Returns a three-tier sea-water level prediction (normal / rising / high)
    plus the estimated water level in metres and current trend.

    If ``latitude`` / ``longitude`` query params are omitted, falls back to
    the boat's last known position from the prediction state store.
    Falls back to 0.0, 0.0 if the boat has never been seen.
    """
    if latitude is None or longitude is None:
        stored = prediction_service.get_risk_status(boat_id)
        latitude  = float(stored["lat"]) if stored and "lat" in stored else 0.0
        longitude = float(stored["lon"]) if stored and "lon" in stored else 0.0

    data = get_predicted_sea_level(latitude, longitude)
    return SeaLevelResponse(**data)
