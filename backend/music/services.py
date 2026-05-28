"""Album diff use-case (logic moved out of the old ``music.views``).

Recomputed every request; only the upstream Douban response stays cached
(via :mod:`core.http`), kept warm by cron.
"""
import os
from typing import List

from core import conf
from core.local_config import add_aliases
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.identifiers import decode_local_path, encode_local_path
from music.crawlers.douban import crawl_douban_250
from music.crawlers.local import crawl_local
from music.matching import get_missing_albums
from music.serializers import AlbumSerializer


def _serialize(albums) -> list:
    return AlbumSerializer(albums, many=True).data


def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    douban_albums = crawl_douban_250()
    if not douban_albums:
        raise UpstreamUnavailable()
    local_albums = crawl_local(conf.MUSIC_ROOT)
    return {
        "missing": _serialize(get_missing_albums(douban_albums, local_albums)),
        "extra": _serialize(get_missing_albums(local_albums, douban_albums)),
    }


def refresh_all() -> None:
    """Repopulate the upstream Douban cache (used by cron)."""
    crawl_douban_250(cache=False)


# --- Alias bind (manual chinese-title supplement) -----------------------
# Album entries have no public unique key (no TMDB/Douban ID on the local
# side), so the alias-bind handshake uses a signed token wrapping the
# on-disk folder path (see core.identifiers). The tvshow/movie flow uses
# tmdb_id directly; structurally identical otherwise.


def alias_targets() -> list:
    """All local albums usable as bind targets for a missing rank item."""
    targets = []
    for local in crawl_local(conf.MUSIC_ROOT):
        if not local.path:
            continue
        targets.append(
            {
                "token": encode_local_path(local.path),
                "title": local.title,
                "year": local.year,
                "artist": local.artist,
                "poster": local.poster,
            }
        )
    targets.sort(key=lambda x: x["title"] or "")
    return targets


def alias_bind(token: str, aliases: List[str]) -> dict:
    """Append ``aliases`` to the album's ``.mediaclawer.json``."""
    try:
        path = decode_local_path(token)
    except ValueError as exc:
        raise ShowNotFound() from exc

    base = os.path.realpath(conf.MUSIC_ROOT)
    target = os.path.realpath(path)
    # 双重防御：即使 token 解码出的 path 越过 root，也拒绝
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()
    if not os.path.isdir(target):
        raise ShowNotFound()

    added = add_aliases(target, aliases)
    return {"bound": True, "added": added}
