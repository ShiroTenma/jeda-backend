import os
import httpx
from app.schemas.cognitive import CognitivePromptRequest, CognitiveMessageResponse

FALLBACK_MESSAGES = {
    "HIGH": "Take a breath and step back. Is this helping you right now?",
    "ELEVATED": "Notice what you are looking for before you keep scrolling.",
    "NORMAL": "Stay mindful of your time."
}

class CognitiveInterventionService:
    """Generates reflective intervention copy via OpenRouter using abstract metadata only."""

    def __init__(self, api_key: str | None = None, model: str = "openai/gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.model = model

    async def generate_message(self, req: CognitivePromptRequest) -> CognitiveMessageResponse:
        fallback = FALLBACK_MESSAGES.get(req.risk_level, FALLBACK_MESSAGES["NORMAL"])
        
        if not self.api_key:
            return CognitiveMessageResponse(message=fallback, source="fallback")

        system_prompt = (
            "You are an empathetic, calm mindfulness assistant helping someone pause mindless digital consumption. "
            "Write exactly ONE short, non-judgmental reflective sentence encouraging the user to pause. "
            "Do not preach, scold, or use toxic positivity."
        )

        user_prompt = (
            f"Risk Level: {req.risk_level}\n"
            f"Trigger Type: {req.trigger}\n"
            f"Intervention Style: {req.intervention_style}\n"
            f"Maximum sentences: {req.max_sentences}"
        )

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/jeda-project",
                        "X-Title": "JEDA Companion"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 60,
                        "temperature": 0.7
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    msg = data["choices"][0]["message"]["content"].strip().strip('"')
                    return CognitiveMessageResponse(message=msg, source="ai")
        except Exception:
            pass

        return CognitiveMessageResponse(message=fallback, source="fallback")
