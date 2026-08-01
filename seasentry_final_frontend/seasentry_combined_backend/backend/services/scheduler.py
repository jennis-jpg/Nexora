"""
services/scheduler.py
=======================
APScheduler configuration for Person B's Safety & Alerting System.

Two recurring jobs:
    1. create_hourly_awake_checks — every 60 minutes, creates a new
       pending awake check for every active boat (Module 2).
    2. escalate_expired_awake_checks — every 1 minute, sweeps pending
       checks and escalates expired ones to the SOS pipeline (Module 3).
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import ACTIVE_BOATS
from services.awake_service import create_awake_check_for_boat, sweep_and_escalate_expired_checks

logger = logging.getLogger("seasentry.scheduler")

scheduler = AsyncIOScheduler()


def _create_hourly_awake_checks() -> None:
    """Job: create a new pending awake check for every active boat."""
    logger.info("Running hourly awake-check creation job for %d boat(s)", len(ACTIVE_BOATS))
    for boat_id in ACTIVE_BOATS:
        try:
            create_awake_check_for_boat(boat_id)
        except Exception:
            logger.exception("Failed to create awake check for boat_id=%s", boat_id)


def _escalate_expired_awake_checks() -> None:
    """Job: sweep pending awake checks and escalate any that have expired."""
    try:
        sweep_and_escalate_expired_checks()
    except Exception:
        logger.exception("Failed during expired awake-check sweep")


def start_scheduler() -> None:
    """
    Register jobs and start the scheduler.

    Should be called once on FastAPI startup.
    """
    if scheduler.running:
        logger.warning("Scheduler already running; skipping re-initialization")
        return

    scheduler.add_job(
        _create_hourly_awake_checks,
        trigger=IntervalTrigger(minutes=60),
        id="hourly_awake_check_creation",
        replace_existing=True,
        next_run_time=None,  # first run after 60 minutes; see note below
    )
    scheduler.add_job(
        _escalate_expired_awake_checks,
        trigger=IntervalTrigger(minutes=1),
        id="awake_check_escalation_sweep",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started: hourly awake checks + 1-minute escalation sweep")


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler. Should be called on FastAPI shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
