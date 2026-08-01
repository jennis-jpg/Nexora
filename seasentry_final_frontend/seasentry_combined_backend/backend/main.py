"""
main.py
========
FastAPI application entrypoint for the combined SeaSentry AI backend.

Wires together:
    - Person A: Geofencing & Prediction Engine
        (/predict, /boundary-check, /boundary-points, /risk-status*)
    - Person B: Safety & Alerting Systems
        - MODULE 1: SOS routes            (/sos)
        - MODULE 2/3: Awake check routes + background scheduler
                                           (/awake-check/*)
        - MODULE 5: Incident report routes (/crossing-report/{boat_id})
    - Person C: Voice Alert Layer
        - /voice/generate-alert-text, /voice/alert-audio/{alert_id}
        - Pre-recorded Kannada MP3s served from /audio/*

Integration point: services/prediction_service.py calls
services/sos_service.create_alert() the moment a boat's risk transitions
into "High", so a single Coast Guard alert pipeline handles manual SOS,
missed awake checks, AND boundary-crossing risk — no duplicated logic.

Person C's original app.py also imported voice_engine.py (pyttsx3 +
playsound) to speak alerts out loud locally — that's meant for a
machine with speakers attached, not a server, and was never called by
the API route itself, so it was intentionally left out of this merge.
The frontend is expected to play audio_url itself.

Person D (Frontend) owns their own app and is not mounted here.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.awake_check import router as awake_check_router
from routes.predict import router as predict_router
from routes.report import router as report_router
from routes.sos import router as sos_router
from routes.voice import router as voice_router
from services.scheduler import shutdown_scheduler, start_scheduler

SOUND_DIR = Path(__file__).parent / "sound"

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("seasentry.main")


# ---------------------------------------------------------------------------
# App lifespan — start/stop the scheduler with the app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown of the APScheduler alongside the FastAPI app."""
    logger.info("Starting SeaSentry AI backend (Prediction Engine + Safety & Alerting)")
    start_scheduler()
    yield
    logger.info("Shutting down SeaSentry AI backend")
    shutdown_scheduler()


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SeaSentry AI",
    description=(
        "Combined backend: Geofencing & Prediction Engine (Person A) + "
        "Safety & Alerting Systems — SOS, awake checks, escalation, and "
        "incident reporting (Person B) + Voice Alert Layer — risk-based "
        "alert text and audio resolution, English + Kannada (Person C)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten this before deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(sos_router)
app.include_router(awake_check_router)
app.include_router(report_router)
app.include_router(voice_router)

# Serve the pre-recorded Kannada alert MP3s referenced by /voice/* audio_url values
app.mount("/audio", StaticFiles(directory=str(SOUND_DIR)), name="audio")


@app.get("/", tags=["System"], summary="Health check")
async def root() -> dict:
    return {"status": "ok", "service": "seasentry-backend"}


@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    """Simple liveness endpoint."""
    return {"status": "ok", "service": "seasentry-backend"}
