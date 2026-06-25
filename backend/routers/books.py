"""Book FastAPI endpoints. Slow reads are SSE; writes are plain JSON."""
from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import conf
from core.images import serve_media_image
from book import services
from routers import stream_result

router = APIRouter(prefix="/books", tags=["books"])


# --- SSE endpoint --------------------------------------------------------

@router.get("/diff")
async def books_diff() -> StreamingResponse:
    return await stream_result(services.diff, "正在对比书库…")


# --- Fast JSON endpoints -------------------------------------------------

class TokenAliasBody(BaseModel):
    token: str
    aliases: List[str]


@router.get("/alias-targets")
def books_alias_targets():
    return services.alias_targets()


@router.post("/alias-bind")
def books_alias_bind(body: TokenAliasBody):
    return services.alias_bind(body.token, body.aliases)


@router.get("/cover/{image_path:path}")
def books_cover(image_path: str):
    return serve_media_image(conf.BOOK_ROOT, image_path, "cover")
