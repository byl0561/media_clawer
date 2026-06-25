"""Movie FastAPI endpoints. Slow reads are SSE streams; writes are plain JSON."""
from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import conf
from core.images import serve_media_image
from movie import services
from routers import stream_result

router = APIRouter(prefix="/movies", tags=["movies"])


# --- SSE endpoints (slow) ------------------------------------------------

@router.get("/diff")
async def movies_diff() -> StreamingResponse:
    return await stream_result(services.diff, "正在对比电影库…")


@router.get("/series-gaps")
async def movies_series_gaps() -> StreamingResponse:
    return await stream_result(services.series_gaps, "正在分析合集缺失…")


@router.get("/subtitle-gaps")
async def movies_subtitle_gaps() -> StreamingResponse:
    return await stream_result(services.subtitle_gaps, "正在检测字幕…")


# --- Fast JSON endpoints -------------------------------------------------

class IgnoreSubtitleBody(BaseModel):
    tmdb_id: int


class IgnoreCollectionBody(BaseModel):
    collection_id: int


class AliasByIdBody(BaseModel):
    tmdb_id: int
    aliases: List[str]


@router.post("/ignore-subtitle")
def movies_ignore_subtitle(body: IgnoreSubtitleBody):
    return services.ignore_subtitle(body.tmdb_id)


@router.post("/ignore-collection")
async def movies_ignore_collection(body: IgnoreCollectionBody):
    return await services.ignore_collection(body.collection_id)


@router.get("/alias-targets")
def movies_alias_targets():
    return services.alias_targets()


@router.post("/alias-bind")
def movies_alias_bind(body: AliasByIdBody):
    return services.alias_bind(body.tmdb_id, body.aliases)


@router.get("/poster/{image_path:path}")
def movies_poster(image_path: str):
    return serve_media_image(conf.MOVIE_ROOT, image_path, "poster")
