"""Album FastAPI endpoints. Slow reads are SSE; writes are plain JSON."""
from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import conf
from core.images import serve_media_image
from music import services
from routers import stream_result

router = APIRouter(prefix="/albums", tags=["albums"])


# --- SSE endpoints -------------------------------------------------------

@router.get("/diff")
async def albums_diff() -> StreamingResponse:
    return await stream_result(services.diff, "正在对比音乐库…")


@router.get("/lyric-gaps")
async def albums_lyric_gaps() -> StreamingResponse:
    return await stream_result(services.lyric_gaps, "正在检测歌词…")


# --- Fast JSON endpoints -------------------------------------------------

class TokenAliasBody(BaseModel):
    token: str
    aliases: List[str]


class IgnoreLyricBody(BaseModel):
    token: str


@router.get("/alias-targets")
def albums_alias_targets():
    return services.alias_targets()


@router.post("/alias-bind")
def albums_alias_bind(body: TokenAliasBody):
    return services.alias_bind(body.token, body.aliases)


@router.post("/ignore-lyric")
def albums_ignore_lyric(body: IgnoreLyricBody):
    return services.ignore_lyric(body.token)


@router.get("/cover/{image_path:path}")
def albums_cover(image_path: str):
    return serve_media_image(conf.MUSIC_ROOT, image_path, "cover")
