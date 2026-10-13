from pydantic import BaseModel, Field

class FrameAnalysisResponse(BaseModel):
    confidence: float = Field(..., ge=0.0, le=1.0, description="Risk confidence from ONNX classifier (0..1)")
    latency_ms: float = Field(..., ge=0.0, description="Inference latency in milliseconds")
    model_name: str = Field(default="baseline_classifier.onnx")
