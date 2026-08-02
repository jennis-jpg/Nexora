"""
dependencies/coastguard_auth.py
=================================
FastAPI dependency that guards fleet-wide coastguard endpoints.

Usage — attach to any route that should only be accessible to the
Coastguard Control Center:

    from fastapi import Depends
    from dependencies.coastguard_auth import verify_coastguard_key

    @router.get("/some-fleet-endpoint", dependencies=[Depends(verify_coastguard_key)])
    async def fleet_endpoint() -> dict: ...

Dev mode: if COASTGUARD_PASSWORD is not set in the environment the
check is skipped entirely, so local development works without a .env
file.  The supplied key is never logged.
"""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


def verify_coastguard_key(
    x_coastguard_key: str | None = Header(default=None),
) -> None:
    """
    Validate the X-Coastguard-Key request header.

    Raises HTTPException(401) if COASTGUARD_PASSWORD is configured in the
    environment and the header is absent or does not match.  When the env
    var is not set (dev / CI mode) every request passes through unchecked.

    Args:
        x_coastguard_key: Value of the ``X-Coastguard-Key`` header,
            injected automatically by FastAPI.
    """
    password = os.environ.get("COASTGUARD_PASSWORD", "")
    if not password:
        # Dev mode — env var not configured, bypass the check.
        return
    if x_coastguard_key != password:
        raise HTTPException(status_code=401, detail="Invalid coastguard credentials")
