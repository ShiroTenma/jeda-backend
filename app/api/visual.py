from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from app.schemas.visual import FrameAnalysisResponse
from app.services.visual import VisualClassifier
from app.api.deps import require_token

router = APIRouter(prefix="/api", tags=["visual"])

@router.post("/analyze-frame", response_model=FrameAnalysisResponse)
async def analyze_frame(
    file: UploadFile = File(...),
    _: None = Depends(require_token),
) -> FrameAnalysisResponse:
    if file.content_type not in ("image/jpeg", "image/png", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid image content type")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty frame content")

    try:
        classifier = VisualClassifier.get_instance()
        confidence, latency = classifier.infer(content)
        return FrameAnalysisResponse(
            confidence=round(confidence, 4),
            latency_ms=round(latency, 2)
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Frame processing failed: {exc}")
