import pytest
from app.schemas.cognitive import CognitivePromptRequest
from app.services.cognitive import CognitiveInterventionService, FALLBACK_MESSAGES

@pytest.mark.asyncio
async def test_fallback_message_when_no_api_key():
    service = CognitiveInterventionService(api_key="")
    req = CognitivePromptRequest(risk_level="HIGH")
    res = await service.generate_message(req)
    assert res.source == "fallback"
    assert res.message == FALLBACK_MESSAGES["HIGH"]

@pytest.mark.asyncio
async def test_fallback_message_when_invalid_key_or_timeout():
    # Service with invalid key falls back cleanly
    service = CognitiveInterventionService(api_key="sk-or-invalid-test-key")
    req = CognitivePromptRequest(risk_level="ELEVATED")
    res = await service.generate_message(req)
    assert res.source == "fallback"
    assert res.message == FALLBACK_MESSAGES["ELEVATED"]

def test_api_endpoint_returns_fallback_safely():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    
    response = client.post(
        "/api/cognitive-message",
        json={"risk_level": "HIGH", "trigger": "sustained_visual_risk", "max_sentences": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["source"] in ("fallback", "ai")
    assert len(data["message"]) > 0
