import time
import logging
import requests

from django.core.cache import cache

__all__ = ['http_get_with_cache']

logger = logging.getLogger()


def http_get_with_cache(url: str, cookies=None, headers=None, cache_ttl_m=1, sleep_s=0.0, need_cache=True) -> str or None:
    if need_cache and cache.has_key(url):
        return cache.get(url)

    if sleep_s > 0:
        time.sleep(sleep_s)

    res = requests.get(url, cookies=cookies, headers=headers)

    if res.status_code != 200:
        logger.error(f'http_get_with_cache error, url: {url}')
        return None

    res.encoding = res.apparent_encoding
    if cache_ttl_m > 0:
        cache.set(url, res.text, cache_ttl_m * 60)
    return res.text
