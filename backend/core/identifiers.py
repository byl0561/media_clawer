"""Tamper-proof tokens for local-only items that lack a public unique key.

LocalAlbum / LocalBook don't carry a TMDB / Douban / Bangumi ID, so any
"identify this local item" round-trip with the frontend would otherwise have
to send the on-disk path and trust it comes back unmodified. Django's signing
machinery seals the path with ``SECRET_KEY``: the frontend echoes the token
back as-is and :func:`decode_local_path` either returns the original path or
raises ``ValueError`` (caller treats as 404).

We deliberately use a plain ``Signer`` rather than ``TimestampSigner`` —
tokens here describe stable on-disk locations, and a user might open a bind
dialog, walk away, and submit hours later. There's no replay risk because
the action is idempotent (alias append-dedup) and authorisation lives at the
endpoint layer, not the token.
"""
from django.core.signing import BadSignature, Signer

# Salt scopes the signature to this use-case so the same token can't be reused
# (or accidentally accepted) by any other Signer in the project.
_SIGNER = Signer(salt="media_crawler.local_path")


def encode_local_path(path: str) -> str:
    """Sign ``path`` into a URL-safe token. Idempotent for a given SECRET_KEY."""
    return _SIGNER.sign(path)


def decode_local_path(token: str) -> str:
    """Verify and unwrap a token previously produced by :func:`encode_local_path`.

    Raises :class:`ValueError` when the signature is missing, malformed, or
    keyed under a different ``SECRET_KEY`` (e.g. after key rotation). Callers
    should translate this to a 404 — the binding is unrecoverable, the user
    just reopens the dialog to get a fresh token.
    """
    try:
        return _SIGNER.unsign(token)
    except BadSignature as exc:
        raise ValueError("invalid local id") from exc
