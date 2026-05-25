"""Shared helpers for the per-folder ``alias.txt`` files.

The local scanners (movie/tvshow) read ``alias.txt`` next to ``movie.nfo`` /
``tvshow.nfo`` to add extra titles to fuzzy matching. The bind-alias endpoints
write to that same file; this module keeps the write path uniform across
both apps (dedup + append-only so existing user-edited aliases survive).
"""
import os
from typing import Iterable, List

_ALIAS_FILE = "alias.txt"


def read_aliases(folder: str) -> List[str]:
    """Return the existing alias lines (stripped, non-empty) or ``[]``."""
    path = os.path.join(folder, _ALIAS_FILE)
    if not os.path.exists(path):
        return []
    with open(path, "r") as fh:
        return [line.strip() for line in fh.read().splitlines() if line.strip()]


def append_unique_aliases(folder: str, aliases: Iterable[str]) -> int:
    """Append each unseen, non-empty alias to ``{folder}/alias.txt``.

    Returns the count actually appended. Idempotent: re-binding the same title
    is a no-op, and user-maintained lines stay put because we only append.
    """
    existing = read_aliases(folder)
    seen = set(existing)
    added: List[str] = []
    for raw in aliases:
        alias = (raw or "").strip()
        if alias and alias not in seen:
            seen.add(alias)
            added.append(alias)
    if added:
        path = os.path.join(folder, _ALIAS_FILE)
        with open(path, "a") as fh:
            for alias in added:
                fh.write(f"{alias}\n")
    return len(added)
