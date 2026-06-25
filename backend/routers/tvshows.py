"""TV-show and anime FastAPI endpoints. Slow reads are SSE; writes are JSON."""
from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import conf
from core.images import serve_media_image
from tvshow import services
from routers import stream_result

router = APIRouter(tags=["tvshows"])


# --- SSE endpoints -------------------------------------------------------

@router.get("/tv-shows/diff")
async def tv_diff() -> StreamingResponse:
    return await stream_result(services.tv_diff, "正在对比剧集库…")


@router.get("/tv-shows/series-gaps")
async def tv_series_gaps() -> StreamingResponse:
    return await stream_result(lambda sink: services.series_gaps("tv", sink), "正在分析剧集续集…")


@router.get("/tv-shows/subtitle-gaps")
async def tv_subtitle_gaps() -> StreamingResponse:
    return await stream_result(lambda sink: services.subtitle_gaps("tv", sink), "正在检测剧集字幕…")


@router.get("/anime/diff")
async def anime_diff() -> StreamingResponse:
    return await stream_result(services.anime_diff, "正在对比动画库…")


@router.get("/anime/series-gaps")
async def anime_series_gaps() -> StreamingResponse:
    return await stream_result(lambda sink: services.series_gaps("anime", sink), "正在分析动画续集…")


@router.get("/anime/subtitle-gaps")
async def anime_subtitle_gaps() -> StreamingResponse:
    return await stream_result(lambda sink: services.subtitle_gaps("anime", sink), "正在检测动画字幕…")


# --- Fast JSON endpoints -------------------------------------------------

class IgnoreBody(BaseModel):
    tmdb_id: int
    selections: List[dict]


class AliasByIdBody(BaseModel):
    tmdb_id: int
    aliases: List[str]


# TV-shows ----------------------------------------------------------------

@router.get("/tv-shows/ignore-options")
async def tv_ignore_options(tmdb_id: int):
    return await services.ignore_options("tv", tmdb_id)


@router.post("/tv-shows/ignore")
async def tv_ignore(body: IgnoreBody):
    return await services.ignore_apply("tv", body.tmdb_id, body.selections)


@router.get("/tv-shows/subtitle-ignore-options")
async def tv_subtitle_ignore_options(tmdb_id: int):
    return await services.subtitle_ignore_options("tv", tmdb_id)


@router.post("/tv-shows/ignore-subtitle")
async def tv_ignore_subtitle(body: IgnoreBody):
    return await services.subtitle_ignore_apply("tv", body.tmdb_id, body.selections)


@router.get("/tv-shows/alias-targets")
def tv_alias_targets():
    return services.alias_targets("tv")


@router.post("/tv-shows/alias-bind")
def tv_alias_bind(body: AliasByIdBody):
    return services.alias_bind("tv", body.tmdb_id, body.aliases)


@router.get("/tv-shows/poster/{image_path:path}")
def tv_poster(image_path: str):
    return serve_media_image(conf.TV_ROOT, image_path, "poster")


# Anime -------------------------------------------------------------------

@router.get("/anime/ignore-options")
async def anime_ignore_options(tmdb_id: int):
    return await services.ignore_options("anime", tmdb_id)


@router.post("/anime/ignore")
async def anime_ignore(body: IgnoreBody):
    return await services.ignore_apply("anime", body.tmdb_id, body.selections)


@router.get("/anime/subtitle-ignore-options")
async def anime_subtitle_ignore_options(tmdb_id: int):
    return await services.subtitle_ignore_options("anime", tmdb_id)


@router.post("/anime/ignore-subtitle")
async def anime_ignore_subtitle(body: IgnoreBody):
    return await services.subtitle_ignore_apply("anime", body.tmdb_id, body.selections)


@router.get("/anime/alias-targets")
def anime_alias_targets():
    return services.alias_targets("anime")


@router.post("/anime/alias-bind")
def anime_alias_bind(body: AliasByIdBody):
    return services.alias_bind("anime", body.tmdb_id, body.aliases)


@router.get("/anime/poster/{image_path:path}")
def anime_poster(image_path: str):
    return serve_media_image(conf.ANIME_ROOT, image_path, "poster")
