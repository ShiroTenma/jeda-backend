from pydantic import BaseModel, Field

class CognitivePromptRequest(BaseModel):
    risk_level: str = Field(..., description="NORMAL | ELEVATED | HIGH")
    trigger: str = Field(default="sustained_visual_risk")
    intervention_style: str = Field(default="reflective")
    max_sentences: int = Field(default=1, ge=1, le=3)

class CognitiveMessageResponse(BaseModel):
    message: str = Field(..., description="1-sentence reflective/cognitive intervention message")
    source: str = Field(..., description="ai | fallback")
