"""
routes/sos.py
==============
MODULE 1 — SOS SYSTEM

Exposes:
    POST /sos
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models import SOSRequest, SOSResponse
from services.sos_service import handle_sos

logger = logging.getLogger("seasentry.routes.sos")

router = APIRouter(prefix="/sos", tags=["SOS"])


@router.post("", response_model=SOSResponse, summary="Trigger a manual SOS alert")
async def trigger_sos(request: SOSRequest) -> SOSResponse:
    """
    Receive a manual SOS from a boat, store the incident, and dispatch
    an alert through the shared Coast Guard alert pipeline.

    Args:
        request: Validated SOS payload (boat_id, latitude, longitude, timestamp).

    Returns:
        SOSResponse with the dispatch status and Coast Guard acknowledgement.
    """
    try:
        return handle_sos(request)
    except Exception as exc:
        logger.exception("Unhandled error while processing SOS for boat_id=%s", request.boat_id)
        raise HTTPException(status_code=500, detail="Failed to process SOS request.") from exc
