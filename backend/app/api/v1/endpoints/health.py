from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"], prefix="/api/v1")


@router.get("/health")
async def health() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


