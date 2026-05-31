"""Per-item local config file: ``.mediaclawer.json``.

One JSON file next to each local item's primary metadata file (movie folder,
show folder, album folder, book parent folder) stores user-editable extras:

  - ``aliases`` (all libraries): extra title strings fed into fuzzy matching
  - ``skip_collections`` (movies only): TMDB collection IDs the user has
    dismissed (junk groupings like a theatre's catalogue) so the series-gap
    view stops carrying them
  - ``seasons`` (tv/anime only): per-season ``checked_episode`` cutoffs that
    suppress that season's outstanding-episode gaps

The JSON is UTF-8, indented, sorted-keyed, so users can hand-edit it.
"""
import json
import os
from typing import Dict, Iterable, List

__all__ = [
    "CONFIG_FILE",
    "read_config",
    "add_aliases",
    "add_skip_collection",
    "set_season_checked",
    "set_season_subtitle_checked",
    "set_skip_subtitle_check",
    "set_skip_lyric_check",
]

CONFIG_FILE = ".mediaclawer.json"


def _config_path(folder: str) -> str:
    return os.path.join(folder, CONFIG_FILE)


def _read_json(folder: str) -> dict:
    path = _config_path(folder)
    if not os.path.exists(path):
        return {}
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


def read_config(folder: str) -> dict:
    """Return the per-folder config dict, or ``{}`` when the file is absent."""
    return _read_json(folder)


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
    _update_season_field(folder, season_num, "checked_episode", episode)


def set_season_subtitle_checked(folder: str, season_num: int, episode: int) -> None:
    """Set / overwrite the ``subtitle_checked_episode`` cutoff for one season.

    Kept separate from ``checked_episode`` on purpose: "I have enough of this
    season" (series gap) and "these early episodes can be subtitle-less"
    (subtitle gap) are different decisions and shouldn't fight.
    """
    _update_season_field(folder, season_num, "subtitle_checked_episode", episode)


def _update_season_field(folder: str, season_num: int, field: str, value: int) -> None:
    data = read_config(folder)
    seasons: Dict[str, dict] = dict(data.get("seasons") or {})
    entry = dict(seasons.get(str(season_num)) or {})
    entry[field] = value
    seasons[str(season_num)] = entry
    data["seasons"] = seasons
    _write_json(folder, data)


def set_skip_subtitle_check(folder: str) -> bool:
    """Idempotent: mark this item as ignored from the subtitle-gap report."""
    return _set_flag(folder, "skip_subtitle_check")


def set_skip_lyric_check(folder: str) -> bool:
    """Idempotent: mark this album as ignored from the lyric-gap report."""
    return _set_flag(folder, "skip_lyric_check")


def _set_flag(folder: str, key: str) -> bool:
    data = read_config(folder)
    if data.get(key) is True:
        return False
    data[key] = True
    _write_json(folder, data)
    return True
