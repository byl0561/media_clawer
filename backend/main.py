"""FastAPI application entry-point for media crawler."""
import logging
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.http import close_async_client
from routers import books, core, movies, music, tvshows
from scheduler import start_scheduler

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

app = FastAPI(title="Media Crawler API", version="1.0.0")


@app.exception_handler(UpstreamUnavailable)
async def _upstream_unavailable(request: Request, exc: UpstreamUnavailable):
    return JSONResponse(
        status_code=503,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(ShowNotFound)
async def _show_not_found(request: Request, exc: ShowNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail, "code": exc.code},
    )


app.include_router(movies.router, prefix="/v1")
app.include_router(tvshows.router, prefix="/v1")
app.include_router(music.router, prefix="/v1")
app.include_router(books.router, prefix="/v1")
app.include_router(core.router, prefix="/v1")


@app.on_event("startup")
async def _startup():
    start_scheduler()


@app.on_event("shutdown")
async def _shutdown():
    await close_async_client()
