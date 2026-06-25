"""Album diff use-case — fully async."""
import asyncio
import os
from typing import List

from core import conf
from core.local_config import (
    add_aliases,
    read_config,
    read_root_excludes,
    set_skip_lyric_check,
)
from core.matching import drop_excluded
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.identifiers import decode_local_path, encode_local_path
from core.media_probe import AUDIO_EXTS, has_lyrics
from music.crawlers.douban import crawl_douban_250
from music.crawlers.local import crawl_local
from music.matching import get_missing_albums


def _album_to_dict(obj) -> dict:
    titles = obj.get_titles()
    rate = obj.get_rate()
    return {
        "title": titles[0] if titles else "",
        "score": round(rate.score, 1) if rate is not None else None,
        "votes": rate.votes if rate is not None else None,
        "poster": obj.get_poster(),
        "link": obj.get_link(),
        "artist": obj.get_artist(),
        "year": obj.get_year(),
    }


def _serialize(albums) -> list:
    return [_album_to_dict(a) for a in albums]


async def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    loop = asyncio.get_running_loop()
    douban_albums, local_albums = await asyncio.gather(
        crawl_douban_250(),
        loop.run_in_executor(None, crawl_local, conf.MUSIC_ROOT),
    )
    if not douban_albums:
        raise UpstreamUnavailable()
    douban_albums = drop_excluded(douban_albums, read_root_excludes(conf.MUSIC_ROOT))
    return {
        "missing": _serialize(get_missing_albums(douban_albums, local_albums)),
        "extra": _serialize(get_missing_albums(local_albums, douban_albums)),
    }


async def refresh_all() -> None:
    """Repopulate the upstream Douban cache (used by cron)."""
    await crawl_douban_250(cache=False)


def _album_has_full_lyrics(folder: str) -> bool:
    """True iff every audio track in the album (incl. sub-disc folders) has lyrics."""
    if not os.path.isdir(folder):
        return True
    found_any = False
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if os.path.splitext(name)[1].lower() not in AUDIO_EXTS:
                continue
            found_any = True
            if not has_lyrics(os.path.join(root, name)):
                return False
    return found_any


async def warm_lyric_cache() -> None:
    await lyric_gaps()


async def lyric_gaps() -> list:
    """Local albums missing embedded lyrics on any track."""
    loop = asyncio.get_running_loop()
    albums = await loop.run_in_executor(None, crawl_local, conf.MUSIC_ROOT)

    async def check_album(album):
        if not album.path:
            return None
        cfg = read_config(album.path)
        if cfg.get("skip_lyric_check"):
            return None
        # mutagen reads only file headers (small I/O); run in thread pool
        has_lyr = await loop.run_in_executor(None, _album_has_full_lyrics, album.path)
        if has_lyr:
            return None
        return {
            "token": encode_local_path(album.path),
            "title": album.title,
            "artist": album.artist,
            "year": album.year,
            "poster": album.poster,
        }

    results = await asyncio.gather(*[check_album(a) for a in albums])
    result = sorted(
        [r for r in results if r is not None],
        key=lambda x: (x["title"] or "").lower(),
    )
    return result


def ignore_lyric(token: str) -> dict:
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

    added = add_aliases(target, aliases)
    return {"bound": True, "added": added}
