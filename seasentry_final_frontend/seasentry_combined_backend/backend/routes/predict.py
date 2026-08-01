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

from fastapi import APIRouter, HTTPException

from models import BoatInput, BoundaryCheckInput
from services import prediction_service

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


@router.get("/risk-status", summary="Last known risk status for all tracked boats")
async def all_risk_status() -> dict:
    """Returns last known status for every tracked boat — for the coastguard dashboard."""
    return {"boats": prediction_service.get_all_risk_status()}
