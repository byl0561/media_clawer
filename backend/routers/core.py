"""Shared (app-agnostic) FastAPI endpoints."""
from fastapi import APIRouter, HTTPException

from core.images import proxy_remote_image

router = APIRouter(tags=["core"])


@router.get("/images/proxy")
async def image_proxy(url: str = ""):
    if not url:
        raise HTTPException(status_code=404)
    return await proxy_remote_image(url)
