"""Prototype request authentication.

If `BACKEND_TOKEN` is unset the backend runs unauthenticated for local
development convenience, and says so on startup. Once a token is configured every
protected route requires it. Comparison is constant-time.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings

logger = logging.getLogger("jeda.auth")


def require_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.backend_token:
        return

    expected = f"Bearer {settings.backend_token}"
    if not hmac.compare_digest(authorization or "", expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "A valid backend token is required.",
                }
            },
        )
