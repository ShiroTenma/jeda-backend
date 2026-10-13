"""M2 wire contract for the behavioural path.

`POST /api/analyze-behavior` does not exist yet — it lands with the FDS engine in
M3. The request and response shapes are declared now so the contract is frozen
before anything is built on top of it (SRS section 6.1).

The client sends raw counters. Normalization and the FDS formula live here, in the
backend, so a parameter change does not invalidate comparisons against previously
recorded snapshots.
"""

from typing import Literal

from pydantic import BaseModel, Field


class BehaviorAnalysisRequest(BaseModel):
    session_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    observation_window_seconds: int = Field(ge=1)

    scroll_events: int = Field(ge=0)
    social_app_switches: int = Field(ge=0)
    active_social_session_seconds: float = Field(ge=0)
    idle_seconds: float = Field(ge=0)

    foreground_package: str | None = None
    soft_intervention_count_24h: int = Field(default=0, ge=0)


class BehaviorAnalysisResponse(BaseModel):
    fds: float = Field(ge=0.0, le=100.0)
    level: Literal["NORMAL", "ELEVATED", "HIGH"]

    # FDS may only ever ask for a soft intervention (FR-10, Appendix D.3). Encoding
    # that as a Literal means a hard block cannot be expressed on this contract at
    # all, rather than merely being discouraged by convention.
    action: Literal["NONE", "SOFT_INTERVENTION"]

    cooldown_seconds: int = Field(ge=0)
