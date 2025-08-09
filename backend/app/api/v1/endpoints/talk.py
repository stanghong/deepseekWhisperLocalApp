from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request
from typing import Optional
from fastapi.responses import Response

from ....core.config import settings
from ....services.orchestrator import Orchestrator


router = APIRouter(tags=["talk"], prefix="/api/v1")


@router.post("/talk")
async def talk(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(default=None),
    system_prompt: Optional[str] = Form(default=None),
) -> Response:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    suffix = Path(file.filename).suffix or ".webm"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)
            content = await file.read()
            tmp.write(content)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}") from exc
    finally:
        await file.close()

    try:
        orch = getattr(request.app.state, "orchestrator", None)
        if orch is None:
            raise RuntimeError("Orchestrator not initialized")
        result = await orch.talk(
            tmp_path,
            conversation_id=conversation_id,
            system_prompt=system_prompt,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    headers = {
        "X-Transcript": quote(result.transcript, safe=""),
        "X-Reply": quote(result.reply_text, safe=""),
        "X-Conversation-Id": quote(getattr(result, "conversation_id", conversation_id or ""), safe=""),
    }
    return Response(content=result.audio_wav_bytes, media_type="audio/wav", headers=headers)


@router.post("/reset")
async def reset_conversation(request: Request, conversation_id: str = Form(...)) -> dict:
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    orch.reset_conversation(conversation_id)
    return {"status": "reset", "conversation_id": conversation_id}


