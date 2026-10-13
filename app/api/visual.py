from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from app.schemas.rrs import RrsAnalysisResponse
from app.services.visual import VisualClassifier
from app.services.rrs import RrsEngine
from app.api.deps import require_token

router = APIRouter(prefix="/api", tags=["visual"])

_rrs_engine = RrsEngine()

@router.post("/analyze-frame", response_model=RrsAnalysisResponse)
async def analyze_frame(
    file: UploadFile = File(...),
    session_id: str = Form(default="default_session"),
    exposure_seconds: float = Form(default=10.0),
    soft_intervention_count: int = Form(default=0),
    hour_of_day: int = Form(default=12),
    _: None = Depends(require_token),
) -> RrsAnalysisResponse:
    if file.content_type not in ("image/jpeg", "image/png", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid image content type")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty frame content")

    try:
        classifier = VisualClassifier.get_instance()
        res = classifier.infer(content)
        confidence = res[0]
        
        evaluation = _rrs_engine.evaluate(
            session_id=session_id,
            current_confidence=confidence,
            exposure_seconds=exposure_seconds,
            soft_intervention_count=soft_intervention_count,
            hour_of_day=hour_of_day
        )
        return evaluation
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Frame processing failed: {exc}")
