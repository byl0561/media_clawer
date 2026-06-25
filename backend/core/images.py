"""Safe poster / cover serving (FastAPI version).

Path-traversal guard and SSRF allowlist are preserved from the Django version.
"""
import logging
import mimetypes
import os
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response

from core import conf
from core.http import _get_async_client

__all__ = ["serve_media_image", "proxy_remote_image"]

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}

_ALLOWED_IMAGE_HOSTS = (
    "doubanio.com",
    "douban.com",
    "image.tmdb.org",
    "bgm.tv",
    "bangumi.tv",
)

_REFERERS = {
    "doubanio.com": "https://www.douban.com/",
    "douban.com": "https://www.douban.com/",
    "bgm.tv": "https://bangumi.tv/",
    "bangumi.tv": "https://bangumi.tv/",
}

_BROWSER_CACHE_SECONDS = 7 * 24 * 60 * 60


def _allowed_host(host: str) -> bool:
    host = host.lower()
    return any(
        host == suffix or host.endswith("." + suffix)
        for suffix in _ALLOWED_IMAGE_HOSTS
    )


def _referer_for(host: str) -> Optional[str]:
    host = host.lower()
    for suffix, referer in _REFERERS.items():
        if host == suffix or host.endswith("." + suffix):
            return referer
    return None


async def proxy_remote_image(url: str) -> Response:
    """Proxy a remote poster/cover image through this server (SSRF-safe)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=404)
    if not _allowed_host(parsed.hostname):
        raise HTTPException(status_code=404)

    headers = {"User-Agent": conf.USER_AGENT}
    referer = _referer_for(parsed.hostname)
    if referer:
        headers["Referer"] = referer

    client = _get_async_client()
    try:
        res = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        logger.warning("image proxy fetch failed, url=%s, error=%s", url, exc)
        raise HTTPException(status_code=404)

    if res.status_code != 200:
        logger.warning(
            "image proxy non-200, url=%s, status=%s", url, res.status_code
        )
        raise HTTPException(status_code=404)

    content_type = res.headers.get("Content-Type", "image/jpeg")
    return Response(
        content=res.content,
        media_type=content_type,
        headers={"Cache-Control": f"public, max-age={_BROWSER_CACHE_SECONDS}"},
    )


def serve_media_image(media_root: str, rel_path: str, stem_suffix: str) -> FileResponse:
    """Stream ``<media_root>/<rel_path>`` if it is a legitimate image."""
    base = os.path.realpath(media_root)
    target = os.path.realpath(os.path.join(media_root, rel_path))

    if target != base and not target.startswith(base + os.sep):
        raise HTTPException(status_code=404)

    stem, ext = os.path.splitext(target)
    if not stem.endswith(stem_suffix):
        raise HTTPException(status_code=404)
    if ext.lower() not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=404)
    if not os.path.isfile(target):
        raise HTTPException(status_code=404)

    content_type, _ = mimetypes.guess_type(target)
    return FileResponse(
        target,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": f"public, max-age={_BROWSER_CACHE_SECONDS}"},
    )
