"""Per-item local config file: ``.mediaclawer.json``.

One JSON file next to each local item's primary metadata file (movie folder,
show folder, album folder, book parent folder) replaces the two legacy text
formats:

  - ``alias.txt`` (all libraries) → JSON ``aliases``
  - ``Season N/checked_episode.txt`` (tv/anime) → JSON ``seasons.<num>.checked_episode``

It also introduces ``skip_collections`` (movies only): TMDB collection IDs the
user has dismissed (e.g. junk TMDB groupings like a theatre's catalogue) so
the series-gap view stops carrying them.

Migration is lazy: the first :func:`read_config` on a folder that has no JSON
but has legacy files pulls them in and deletes the originals atomically. Once
the JSON exists, it is the single source of truth — manually re-introduced
legacy files are not picked up.

The JSON is UTF-8, indented, sorted-keyed, so users can hand-edit it.
"""
import json
import os
import re
from typing import Dict, Iterable, List, Optional

__all__ = [
    "CONFIG_FILE",
    "read_config",
    "add_aliases",
    "add_skip_collection",
    "set_season_checked",
]

CONFIG_FILE = ".mediaclawer.json"

_LEGACY_ALIAS = "alias.txt"
_LEGACY_SEASON_CHECK = "checked_episode.txt"
# Matches both tmm-style ``Specials`` and MoviePilot/Plex-style ``Season N``.
_SEASON_DIR_RE = re.compile(r"^(?:Specials|Season\s+(\d+))$")


def _config_path(folder: str) -> str:
    return os.path.join(folder, CONFIG_FILE)


def _read_json(folder: str) -> Optional[dict]:
    path = _config_path(folder)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(folder: str, data: dict) -> None:
    """Atomic write (tmp + rename) so a crash mid-write can't truncate the file."""
    path = _config_path(folder)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def _migrate_legacy(folder: str) -> Optional[dict]:
    """Build a config dict from legacy files in ``folder`` and remove them.

    Returns the migrated dict when at least one legacy file existed (the JSON
    file is also written on disk), or ``None`` if there was nothing to do.
    """
    data: dict = {}

    alias_path = os.path.join(folder, _LEGACY_ALIAS)
    if os.path.isfile(alias_path):
        try:
            with open(alias_path, "r", encoding="utf-8") as fh:
                aliases = [ln.strip() for ln in fh.read().splitlines() if ln.strip()]
            if aliases:
                data["aliases"] = aliases
            os.remove(alias_path)
        except OSError:
            pass

    seasons: Dict[str, dict] = {}
    if os.path.isdir(folder):
        try:
            children = os.listdir(folder)
        except OSError:
            children = []
        for name in children:
            sub = os.path.join(folder, name)
            if not os.path.isdir(sub):
                continue
            match = _SEASON_DIR_RE.match(name)
            if not match:
                continue
            num = 0 if name == "Specials" else int(match.group(1))
            check = os.path.join(sub, _LEGACY_SEASON_CHECK)
            if not os.path.isfile(check):
                continue
            try:
                with open(check, "r", encoding="utf-8") as fh:
                    episode = int((fh.readline() or "0").strip() or 0)
                seasons[str(num)] = {"checked_episode": episode}
                os.remove(check)
            except (OSError, ValueError):
                pass
    if seasons:
        data["seasons"] = seasons

    if not data:
        return None
    _write_json(folder, data)
    return data


def read_config(folder: str) -> dict:
    """Return the per-folder config dict, migrating legacy files on first hit."""
    data = _read_json(folder)
    if data is not None:
        return data
    return _migrate_legacy(folder) or {}


def add_aliases(folder: str, aliases: Iterable[str]) -> int:
    """Append unseen, non-empty aliases. Returns the count actually added.

    Idempotent: re-binding the same title is a no-op and user-typed entries
    survive because we only append.
    """
    data = read_config(folder)
    existing: List[str] = list(data.get("aliases") or [])
    seen = set(existing)
    added: List[str] = []
    for raw in aliases:
        alias = (raw or "").strip()
        if alias and alias not in seen:
            seen.add(alias)
            added.append(alias)
    if added:
        data["aliases"] = existing + added
        _write_json(folder, data)
    return len(added)


def add_skip_collection(folder: str, collection_id: int) -> bool:
    """Append ``collection_id`` to ``skip_collections``. Returns True iff added.

    Idempotent — re-ignoring the same collection is a no-op.
    """
    data = read_config(folder)
    existing: List[int] = list(data.get("skip_collections") or [])
    if collection_id in existing:
        return False
    data["skip_collections"] = sorted([*existing, collection_id])
    _write_json(folder, data)
    return True


def set_season_checked(folder: str, season_num: int, episode: int) -> None:
    """Set / overwrite the ``checked_episode`` cutoff for one season."""
    data = read_config(folder)
    seasons: Dict[str, dict] = dict(data.get("seasons") or {})
    seasons[str(season_num)] = {"checked_episode": episode}
    data["seasons"] = seasons
    _write_json(folder, data)
