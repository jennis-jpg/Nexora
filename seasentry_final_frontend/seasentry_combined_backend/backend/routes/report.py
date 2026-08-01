"""
routes/report.py
==================
MODULE 5 — Incident report PDF.

Exposes:
    GET /crossing-report/{boat_id}
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from services.report_service import generate_incident_report_pdf

logger = logging.getLogger("seasentry.routes.report")

router = APIRouter(prefix="/crossing-report", tags=["Incident Report"])


@router.get("/{boat_id}", summary="Download the incident report PDF for a boat")
async def get_crossing_report(
    boat_id: str,
    latitude: Optional[float] = Query(default=None, description="Last known latitude"),
    longitude: Optional[float] = Query(default=None, description="Last known longitude"),
) -> FileResponse:
    """
    Generate and return the accidental maritime boundary crossing report
    as a downloadable PDF.

    Args:
        boat_id: Unique identifier of the boat.
        latitude: Optional last known latitude, used for the weather lookup.
        longitude: Optional last known longitude, used for the weather lookup.

    Returns:
        FileResponse streaming the generated PDF.
    """
    try:
        pdf_path = generate_incident_report_pdf(boat_id, latitude=latitude, longitude=longitude)
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"seasentry_report_{boat_id}.pdf",
        )
    except Exception as exc:
        logger.exception("Failed to generate incident report for boat_id=%s", boat_id)
        raise HTTPException(status_code=500, detail="Failed to generate incident report.") from exc
