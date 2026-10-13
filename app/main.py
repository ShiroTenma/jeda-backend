import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.behavior import router as behavior_router
from app.api.visual import router as visual_router
from app.api.cognitive import router as cognitive_router
from app.config import get_settings

logger = logging.getLogger("jeda")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not get_settings().backend_token:
        logger.warning(
            "BACKEND_TOKEN is not set; prototype requests are unauthenticated. "
            "Set it before any device beyond your own tailnet can reach this service."
        )
    yield


app = FastAPI(title="JEDA Backend", version="0.3.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "jeda-backend",
        "version": "0.3.0",
    }


app.include_router(behavior_router)
app.include_router(visual_router)
app.include_router(cognitive_router)
