from fastapi import APIRouter, Depends
from app.schemas.cognitive import CognitivePromptRequest, CognitiveMessageResponse
from app.services.cognitive import CognitiveInterventionService
from app.api.deps import require_token

router = APIRouter(prefix="/api", tags=["cognitive"])

_cognitive_service = CognitiveInterventionService()

@router.post("/cognitive-message", response_model=CognitiveMessageResponse)
async def get_cognitive_message(
    req: CognitivePromptRequest,
    _: None = Depends(require_token),
) -> CognitiveMessageResponse:
    return await _cognitive_service.generate_message(req)
