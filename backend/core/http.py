"""Cached HTTP GET helper shared by every crawler.

Improvements over the original ``utils.request_utils``:

* a single pooled :class:`requests.Session` instead of a fresh connection
  per call;
* a mandatory (connect, read) timeout so a stalled upstream can no longer
  pin a worker forever;
* a sentinel-based cache lookup (one round-trip, no ``has_key``/``get``
  race);
* failures are logged with context instead of disappearing silently.

The non-200 / exception path still returns ``None`` (callers skip that page)
so the diff semantics are unchanged from before the refactor.
"""
import logging
import time
from typing import Optional

import requests
from django.core.cache import cache

from core import conf

__all__ = ["http_get_with_cache"]

logger = logging.getLogger(__name__)

_session = requests.Session()
_CACHE_MISS = object()


def http_get_with_cache(
    url: str,
    cookies: Optional[dict] = None,
    headers: Optional[dict] = None,
    cache_ttl_m: int = 1,
    sleep_s: float = 0.0,
    need_cache: bool = True,
) -> Optional[str]:
    """Return the response body for ``url``, served from Redis when possible.

    ``need_cache=False`` forces a live fetch (used by the cron refresh jobs to
    repopulate the cache).
    """
    if need_cache:
        cached = cache.get(url, _CACHE_MISS)
        if cached is not _CACHE_MISS:
            return cached

    if sleep_s > 0:
        time.sleep(sleep_s)

    try:
        res = _session.get(
            url,
            cookies=cookies,
            headers=headers,
            timeout=conf.HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("http get failed, url=%s, error=%s", url, exc)
        return None

    if res.status_code != 200:
        logger.warning("http get non-200, url=%s, status=%s", url, res.status_code)
        return None

    res.encoding = res.apparent_encoding
    if cache_ttl_m > 0:
        cache.set(url, res.text, cache_ttl_m * 60)
    return res.text
