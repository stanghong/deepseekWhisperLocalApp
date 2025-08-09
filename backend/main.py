from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.services.asr import ASRService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.services.orchestrator import Orchestrator
from app.services.memory import ConversationStore
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.talk import router as talk_router


logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.info("Starting application...")

    # Initialize services
    asr = ASRService(
        model_size=settings.asr_model_size,
        compute_type=settings.asr_compute_type,
        device=settings.asr_device,
        cpu_threads=settings.asr_cpu_threads,
    )
    try:
        asr.load()
    except Exception as exc:
        logger.warning("ASR preload failed (will lazy-load on first request): %s", exc)

    llm = LLMService(base_url=settings.ollama_url, model=settings.ollama_model)

    tts = TTSService(piper_path=settings.piper_path, voice_model_path=settings.piper_voice_path)
    try:
        tts.validate()
    except Exception as exc:
        logger.warning("TTS validation failed: %s", exc)

    app.state.orchestrator = Orchestrator(
        asr=asr,
        llm=llm,
        tts=tts,
        per_step_timeout_seconds=settings.request_timeout_seconds,
        memory=ConversationStore(max_turns=20),
    )

    yield

    # Shutdown
    try:
        await llm.aclose()
    except Exception:
        pass
    logger.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(health_router)
app.include_router(talk_router)

# Mount static web UI last to avoid capturing API routes
project_root = Path(__file__).resolve().parent.parent
web_dir = project_root / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


