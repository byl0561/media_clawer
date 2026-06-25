"""Thin Redis client singleton shared by http.py and media_probe.py."""
import os
from typing import Optional

import redis as _redis_mod

_client: Optional[_redis_mod.Redis] = None


def get_cache() -> _redis_mod.Redis:
    global _client
    if _client is None:
        _client = _redis_mod.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASS", "") or None,
            decode_responses=True,
        )
    return _client
