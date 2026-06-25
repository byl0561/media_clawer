"""Cached async HTTP GET helper shared by every crawler (httpx)."""
import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx

from core import conf
from core.cache import get_cache

__all__ = ["async_http_get_with_cache", "close_async_client", "_get_async_client"]

logger = logging.getLogger(__name__)

_RETRYABLE_STATUSES = {429, 502, 503, 504}
_BACKOFF_CAP_SECONDS = 8
_RETRY_AFTER_CAP_SECONDS = 30

_async_client: Optional[httpx.AsyncClient] = None


def _get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=15),
            timeout=httpx.Timeout(
                connect=conf.HTTP_TIMEOUT[0],
                read=conf.HTTP_TIMEOUT[1],
                write=10.0,
                pool=5.0,
            ),
            follow_redirects=True,
        )
    return _async_client


async def close_async_client() -> None:
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None


def _parse_retry_after(value: str) -> Optional[float]:
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


def _retry_wait(response: httpx.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        seconds = _parse_retry_after(retry_after)
        if seconds is not None:
            return min(seconds, _RETRY_AFTER_CAP_SECONDS)
    return min(2 ** attempt, _BACKOFF_CAP_SECONDS)


async def async_http_get_with_cache(
    url: str,
    cookies: Optional[dict] = None,
    headers: Optional[dict] = None,
    cache_ttl_m: int = 1,
    need_cache: bool = True,
    retry: bool = False,
) -> Optional[str]:
    """Async cached HTTP GET. Concurrency is caller-controlled via Semaphore."""
    cache = get_cache()
    if need_cache:
        cached = cache.get(url)
        if cached is not None:
            return cached

    client = _get_async_client()
    max_attempts = (conf.TMDB_MAX_RETRIES + 1) if retry else 1

    for attempt in range(max_attempts):
        is_last = attempt == max_attempts - 1
        try:
            res = await client.get(
                url,
                headers=headers or {},
                cookies=cookies or {},
            )
        except httpx.RequestError as exc:
            if retry and not is_last:
                wait = min(2 ** attempt, _BACKOFF_CAP_SECONDS)
                logger.warning(
                    "async http get error, retry in %ss (%d/%d), url=%s, error=%s",
                    wait, attempt + 1, max_attempts - 1, url, exc,
                )
                await asyncio.sleep(wait)
                continue
            logger.warning("async http get failed, url=%s, error=%s", url, exc)
            return None

        if res.status_code == 200:
            text = res.text
            if cache_ttl_m > 0:
                cache.setex(url, cache_ttl_m * 60, text)
            return text

        if retry and not is_last and res.status_code in _RETRYABLE_STATUSES:
            wait = _retry_wait(res, attempt)
            logger.warning(
                "async http get %s, retry in %ss (%d/%d), url=%s",
                res.status_code, wait, attempt + 1, max_attempts - 1, url,
            )
            await asyncio.sleep(wait)
            continue

        logger.warning("async http get non-200, url=%s, status=%s", url, res.status_code)
        return None

    return None
