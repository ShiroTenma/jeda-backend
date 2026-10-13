from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_token
from app.config import FdsConfig, get_settings
from app.schemas.behavior import BehaviorAnalysisRequest, BehaviorAnalysisResponse
from app.services import fds

logger = logging.getLogger("jeda.api")

router = APIRouter(prefix="/api", tags=["behavior"])


@router.post("/analyze-behavior", response_model=BehaviorAnalysisResponse)
def analyze_behavior(
    payload: BehaviorAnalysisRequest,
    _auth: None = Depends(require_token),
) -> BehaviorAnalysisResponse:
    """Score one behavioral snapshot.

    The client supplies the rolling soft-intervention count; the backend owns the
    formula. Accepting the count from the client is acceptable for a prototype on
    a private tailnet, but it is client-asserted and not independently verified.
    """
    config: FdsConfig = get_settings().fds
    return fds.evaluate(payload, config)
