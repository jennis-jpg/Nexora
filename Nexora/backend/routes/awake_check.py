"""
routes/awake_check.py
=======================
MODULE 2 — Hourly operator awake check.

Exposes:
    GET  /awake-check/status/{boat_id}
    POST /awake-check/ack
    POST /awake-check/trigger-now/{boat_id}   (debug/demo only — see below)

Escalation of missed checks (Module 3) runs entirely in the background
scheduler and is not exposed as a route.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models import AwakeCheckAckRequest, AwakeCheckAckResponse, AwakeCheckStatusResponse
from services.awake_service import (
    confirm_awake_check,
    create_awake_check_for_boat,
    get_awake_check_status,
)

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


@router.post(
    "/trigger-now/{boat_id}",
    response_model=AwakeCheckStatusResponse,
    summary="[DEBUG] Manually create a pending awake check for a boat",
)
async def trigger_awake_check_now(boat_id: str) -> AwakeCheckStatusResponse:
    """
    Immediately create a new pending awake check for a boat, bypassing
    the hourly scheduler.

    DEBUG / DEMO ONLY. In production, awake checks are only ever created
    by `services/scheduler.py`'s hourly job — the scheduler's first run
    doesn't happen until 60 minutes after the server starts
    (`next_run_time=None`), which makes it impractical to demo or test
    the pending -> confirm/expire -> escalate flow without waiting an
    hour. This endpoint lets you skip that wait by creating a check on
    demand for any boat_id (does not have to be one of the demo
    ACTIVE_BOATS — useful for testing arbitrary IDs too).

    Consider removing or gating this behind an auth check before a real
    deployment; it's intentionally unauthenticated for hackathon/demo
    convenience.

    Args:
        boat_id: Unique identifier of the boat to create a check for.

    Returns:
        AwakeCheckStatusResponse for the newly created (pending) check.
    """
    try:
        record = create_awake_check_for_boat(boat_id)
        return AwakeCheckStatusResponse(
            status=record.status,
            created_at=record.created_at,
            expires_at=record.expires_at,
            confirmed_at=record.confirmed_at,
        )
    except Exception as exc:
        logger.exception("Unhandled error triggering awake check for boat_id=%s", boat_id)
        raise HTTPException(status_code=500, detail="Failed to trigger awake check.") from exc
