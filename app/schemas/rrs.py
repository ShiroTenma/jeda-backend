from pydantic import BaseModel, Field

class FrameAnalysisRequestMeta(BaseModel):
    session_id: str = Field(..., description="Active monitoring session ID")
    foreground_package: str = Field(..., description="Package currently in foreground")
    exposure_seconds: float = Field(default=0.0, ge=0.0, description="Elapsed exposure in current target context")
    soft_intervention_count_24h: int = Field(default=0, ge=0, description="Soft interventions accrued in 24h")
    hour_of_day: int = Field(default=12, ge=0, le=23, description="Client local hour for context multiplier")

class RrsAnalysisResponse(BaseModel):
    visual_confidence: float = Field(..., ge=0.0, le=1.0)
    p_avg: float = Field(..., ge=0.0, le=1.0)
    dn: float = Field(..., ge=0.0, le=1.0)
    ct: float = Field(..., ge=1.0, le=2.0)
    rrs: float = Field(..., ge=0.0, le=1.0)
    level: str = Field(..., description="NORMAL | ELEVATED | HIGH")
    action: str = Field(..., description="NONE | ELEVATED_MONITORING | HARD_INTERVENTION")
    duration_seconds: int = Field(default=0)
    sampling_interval_seconds: int = Field(default=3)
