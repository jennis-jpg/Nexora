"""
routes/awake_check.py
=======================
MODULE 2 — Hourly operator awake check.

Exposes:
    GET  /awake-check/status/{boat_id}
    POST /awake-check/ack

Escalation of missed checks (Module 3) runs entirely in the background
scheduler and is not exposed as a route.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models import AwakeCheckAckRequest, AwakeCheckAckResponse, AwakeCheckStatusResponse
from services.awake_service import confirm_awake_check, get_awake_check_status

logger = logging.getLogger("seasentry.routes.awake_check")

router = APIRouter(prefix="/awake-check", tags=["Awake Check"])


@router.get(
    "/status/{boat_id}",
    response_model=AwakeCheckStatusResponse,
    summary="Get the latest awake check status for a boat",
)
async def get_status(boat_id: str) -> AwakeCheckStatusResponse:
    """
    Return the status of the most recent awake check for a boat.

    The frontend polls this endpoint; if status is 'pending', it should
    display the "Safety Check" confirmation prompt to the operator.

    Args:
        boat_id: Unique identifier of the boat.

    Returns:
        AwakeCheckStatusResponse describing the latest check.
    """
    try:
        record = get_awake_check_status(boat_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"No awake check found for boat_id='{boat_id}'.",
            )
        return AwakeCheckStatusResponse(
            status=record.status,
            created_at=record.created_at,
            expires_at=record.expires_at,
            confirmed_at=record.confirmed_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error fetching awake check status for boat_id=%s", boat_id)
        raise HTTPException(status_code=500, detail="Failed to fetch awake check status.") from exc


@router.post(
    "/ack",
    response_model=AwakeCheckAckResponse,
    summary="Confirm the operator is awake",
)
async def acknowledge_awake_check(request: AwakeCheckAckRequest) -> AwakeCheckAckResponse:
    """
    Confirm the latest pending awake check for a boat.

    Args:
        request: Contains the boat_id confirming the check.

    Returns:
        AwakeCheckAckResponse with confirmation status and timestamp.
    """
    try:
        record = confirm_awake_check(request.boat_id)
        if record is None:
            raise HTTPException(
                status_code=409,
                detail=f"No pending awake check to confirm for boat_id='{request.boat_id}'.",
            )
        return AwakeCheckAckResponse(status="Awake confirmed", confirmed_at=record.confirmed_at)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error confirming awake check for boat_id=%s", request.boat_id)
        raise HTTPException(status_code=500, detail="Failed to confirm awake check.") from exc
