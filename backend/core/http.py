"""Cached HTTP GET helper shared by every crawler.

Improvements over the original ``utils.request_utils``:

* a single pooled :class:`requests.Session` instead of a fresh connection
  per call;
* a mandatory (connect, read) timeout so a stalled upstream can no longer
  pin a worker forever;
* a sentinel-based cache lookup (one round-trip, no ``has_key``/``get``
  race);
* failures are logged with context instead of disappearing silently;
* optional bounded retry (``retry=True``, opt-in) for rate-limited /
  transient responses — only the TMDB crawlers enable it. Douban/Bangumi
  keep the original "skip on failure" behaviour, since their 429 is usually
  an anti-bot signal where retrying would only get the IP banned faster.

The non-retry path returns ``None`` on any non-200/exception exactly as
before, so the diff semantics are unchanged for the HTML scrapers.
"""
import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import requests
from django.core.cache import cache

from core import conf

__all__ = ["http_get_with_cache"]

logger = logging.getLogger(__name__)

_session = requests.Session()
_CACHE_MISS = object()

# Retried only when the caller opts in via ``retry=True``.
_RETRYABLE_STATUSES = {429, 502, 503, 504}
# Exponential backoff (2**attempt) is capped here; a server-provided
# Retry-After is honoured but also capped so a hostile/huge value can't pin a
# worker past the gunicorn timeout.
_BACKOFF_CAP_SECONDS = 8
_RETRY_AFTER_CAP_SECONDS = 30


def _parse_retry_after(value: str) -> Optional[float]:
    """Parse a ``Retry-After`` header (delta-seconds or HTTP-date)."""
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())


def _retry_wait(response: requests.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        seconds = _parse_retry_after(retry_after)
        if seconds is not None:
            return min(seconds, _RETRY_AFTER_CAP_SECONDS)
    return min(2 ** attempt, _BACKOFF_CAP_SECONDS)


def http_get_with_cache(
    url: str,
    cookies: Optional[dict] = None,
    headers: Optional[dict] = None,
    cache_ttl_m: int = 1,
    sleep_s: float = 0.0,
    need_cache: bool = True,
    retry: bool = False,
) -> Optional[str]:
    """Return the response body for ``url``, served from Redis when possible.

    ``need_cache=False`` forces a live fetch (used by the cron refresh jobs to
    repopulate the cache). ``retry=True`` adds a bounded backoff retry on 429 /
    transient 5xx and transient network errors (``conf.TMDB_MAX_RETRIES``
    extra attempts); on exhaustion it returns ``None`` like the no-retry path,
    so a single rate-limited item is skipped rather than failing the endpoint.
    """
    if need_cache:
        cached = cache.get(url, _CACHE_MISS)
        if cached is not _CACHE_MISS:
            return cached

    if sleep_s > 0:
        time.sleep(sleep_s)

    max_attempts = (conf.TMDB_MAX_RETRIES + 1) if retry else 1
    for attempt in range(max_attempts):
        is_last = attempt == max_attempts - 1
        try:
            res = _session.get(
                url,
                cookies=cookies,
                headers=headers,
                timeout=conf.HTTP_TIMEOUT,
            )
        except requests.RequestException as exc:
            if retry and not is_last:
                wait = min(2 ** attempt, _BACKOFF_CAP_SECONDS)
                logger.warning(
                    "http get error, retry in %ss (%d/%d), url=%s, error=%s",
                    wait, attempt + 1, max_attempts - 1, url, exc,
                )
                time.sleep(wait)
                continue
            logger.warning("http get failed, url=%s, error=%s", url, exc)
            return None

        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            if cache_ttl_m > 0:
                cache.set(url, res.text, cache_ttl_m * 60)
            return res.text

        if retry and not is_last and res.status_code in _RETRYABLE_STATUSES:
            wait = _retry_wait(res, attempt)
            logger.warning(
                "http get %s, retry in %ss (%d/%d), url=%s",
                res.status_code, wait, attempt + 1, max_attempts - 1, url,
            )
            time.sleep(wait)
            continue

        logger.warning("http get non-200, url=%s, status=%s", url, res.status_code)
        return None

    return None
