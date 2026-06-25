"""Tamper-proof tokens for local-only items that lack a public unique key.

Uses HMAC-SHA256 (Python stdlib only) instead of Django's signing machinery.
The token format is ``<path>:<hex-hmac>`` — URL-safe because paths never
contain colons and the HMAC is hex. The key comes from the ``SECRET_KEY``
environment variable (same variable as the old Django setting).
"""
import hashlib
import hmac
import os

_SECRET = os.environ.get("SECRET_KEY", "media-crawler-insecure-default").encode()
_SALT = b"media_crawler.local_path"
_SEP = ":"


def _sign(path: str) -> str:
    digest = hmac.new(_SECRET, _SALT + path.encode(), hashlib.sha256).hexdigest()
    return f"{path}{_SEP}{digest}"


def encode_local_path(path: str) -> str:
    """Sign ``path`` into a URL-safe token. Idempotent for a given SECRET_KEY."""
    return _sign(path)


def decode_local_path(token: str) -> str:
    """Verify and unwrap a token previously produced by :func:`encode_local_path`.

    Raises :class:`ValueError` on tampered or malformed tokens.
    """
    if _SEP not in token:
        raise ValueError("invalid local id")
    last_sep = token.rfind(_SEP)
    path = token[:last_sep]
    expected = _sign(path)
    if not hmac.compare_digest(token, expected):
        raise ValueError("invalid local id")
    return path
