"""Album diff use-case (logic moved out of the old ``music.views``).

Recomputed every request; only the upstream Douban response stays cached
(via :mod:`core.http`), kept warm by cron.
"""
import os
from typing import List

from core import conf
from core.local_config import add_aliases, read_config, set_skip_lyric_check
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.identifiers import decode_local_path, encode_local_path
from core.media_probe import AUDIO_EXTS, has_lyrics
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


def _album_has_full_lyrics(folder: str) -> bool:
    """An album counts as fully lyric'd iff every audio track carries lyrics.

    Empty/no-audio folders are not flagged — there's nothing to check.
    """
    try:
        names = os.listdir(folder)
    except OSError:
        return True
    for name in names:
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in AUDIO_EXTS:
            continue
        if not has_lyrics(path):
            return False
    return True


def lyric_gaps() -> list:
    """Local albums whose tracks are missing embedded lyrics on any song.

    "Any missing track means the album is flagged" — matches the user spec
    that a single tagless track in the album should surface the album. Honours
    ``skip_lyric_check`` in the album's ``.mediaclawer.json``. Each row carries
    a signed token so the frontend's ignore action can address the album
    without exposing the on-disk path.
    """
    result = []
    for album in crawl_local(conf.MUSIC_ROOT):
        if not album.path:
            continue
        cfg = read_config(album.path)
        if cfg.get("skip_lyric_check"):
            continue
        if _album_has_full_lyrics(album.path):
            continue
        result.append(
            {
                "token": encode_local_path(album.path),
                "title": album.title,
                "artist": album.artist,
                "year": album.year,
                "poster": album.poster,
            }
        )
    result.sort(key=lambda x: (x["title"] or "").lower())
    return result


def ignore_lyric(token: str) -> dict:
    """Set ``skip_lyric_check: true`` on the album's ``.mediaclawer.json``."""
    try:
        path = decode_local_path(token)
    except ValueError as exc:
        raise ShowNotFound() from exc

    base = os.path.realpath(conf.MUSIC_ROOT)
    target = os.path.realpath(path)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()
    if not os.path.isdir(target):
        raise ShowNotFound()
    return {"updated": set_skip_lyric_check(target)}


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
