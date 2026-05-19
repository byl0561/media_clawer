"""Safe poster / cover serving.

The original per-app views did ``os.path.join(folder, user_supplied_path)``
guarded only by an ``endswith('poster')`` check, so a request such as
``../../../etc/secret-poster.png`` escaped the media library. Here the
resolved path is required to stay inside the library root, and the file is
streamed with :class:`~django.http.FileResponse` instead of being slurped
into memory.

Remote posters (Douban / TMDB / Bangumi absolute URLs) are streamed through
:func:`proxy_remote_image` instead of the previous third-party
``images.weserv.nl`` redirect. weserv was only ever there to drop the browser
``Referer`` that triggers Douban's hotlink protection; a server-side fetch has
no such header, so proxying in-process both fixes the weserv 404s and removes
the external dependency. An allowlist keeps it from doubling as an open SSRF
proxy.
"""
import logging
import mimetypes
import os
from typing import Optional
from urllib.parse import urlparse

import requests
from django.http import FileResponse, Http404, StreamingHttpResponse

from core import conf

__all__ = ["serve_media_image", "proxy_remote_image"]

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}

# Hosts whose images the crawlers actually emit. The proxy refuses anything
# else so this endpoint can't be turned into a generic SSRF / open relay.
_ALLOWED_IMAGE_HOSTS = (
    "doubanio.com",
    "douban.com",
    "image.tmdb.org",
    "bgm.tv",
    "bangumi.tv",
)

# Douban / Bangumi serve the bytes fine to a server-side client, but a
# matching Referer keeps us indistinguishable from a normal page load if they
# ever tighten things. TMDB images are open and need none.
_REFERERS = {
    "doubanio.com": "https://www.douban.com/",
    "douban.com": "https://www.douban.com/",
    "bgm.tv": "https://bangumi.tv/",
    "bangumi.tv": "https://bangumi.tv/",
}

_CHUNK_SIZE = 64 * 1024
# Browsers should cache a poster hard; the upstream URL is content-addressed.
_BROWSER_CACHE_SECONDS = 7 * 24 * 60 * 60

# Pooled session dedicated to image bytes (kept separate from the cached-HTML
# session in core.http, which tags every response for Redis text caching).
_session = requests.Session()


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


def proxy_remote_image(url: str) -> StreamingHttpResponse:
    """Stream a remote poster/cover through this server.

    Raises :class:`~django.http.Http404` for a malformed URL, a host outside
    :data:`_ALLOWED_IMAGE_HOSTS`, or any upstream failure (non-200 / network
    error) so a broken poster degrades to a normal broken-image rather than a
    500.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise Http404()
    if not _allowed_host(parsed.hostname):
        raise Http404()

    headers = {"User-Agent": conf.USER_AGENT}
    referer = _referer_for(parsed.hostname)
    if referer:
        headers["Referer"] = referer

    try:
        upstream = _session.get(
            url, headers=headers, timeout=conf.HTTP_TIMEOUT, stream=True
        )
    except requests.RequestException as exc:
        logger.warning("image proxy fetch failed, url=%s, error=%s", url, exc)
        raise Http404()

    if upstream.status_code != 200:
        upstream.close()
        logger.warning(
            "image proxy non-200, url=%s, status=%s", url, upstream.status_code
        )
        raise Http404()

    content_type = upstream.headers.get("Content-Type", "image/jpeg")
    response = StreamingHttpResponse(
        upstream.iter_content(_CHUNK_SIZE),
        content_type=content_type,
    )
    response["Cache-Control"] = f"public, max-age={_BROWSER_CACHE_SECONDS}"
    return response


def serve_media_image(media_root: str, rel_path: str, stem_suffix: str) -> FileResponse:
    """Stream ``<media_root>/<rel_path>`` if it is a legitimate image.

    Raises :class:`~django.http.Http404` unless the resolved path stays within
    ``media_root``, its filename stem ends with ``stem_suffix`` ("poster" /
    "cover") and it has an allowed image extension.
    """
    base = os.path.realpath(media_root)
    target = os.path.realpath(os.path.join(media_root, rel_path))

    if target != base and not target.startswith(base + os.sep):
        raise Http404()

    stem, ext = os.path.splitext(target)
    if not stem.endswith(stem_suffix):
        raise Http404()
    if ext.lower() not in _ALLOWED_EXTENSIONS:
        raise Http404()
    if not os.path.isfile(target):
        raise Http404()

    content_type, _ = mimetypes.guess_type(target)
    return FileResponse(
        open(target, "rb"),
        content_type=content_type or "application/octet-stream",
    )
