"""Movie diff use-cases — fully async."""
import asyncio
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

from core import conf
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.local_config import (
    add_aliases,
    add_skip_collection,
    read_config,
    read_root_excludes,
    set_skip_subtitle_check,
)
from core.matching import drop_excluded
from core.media_probe import VIDEO_EXTS, async_has_subtitle
from movie.crawlers.douban import crawl_douban_250
from movie.crawlers.local import crawl_local, file_filter
from movie.crawlers.tmdb import get_tmdb_movie, get_tmdb_movies_in_set
from movie.matching import get_extra_movies, get_missing_movies
from movie.models import Movie, MovieSet, TmdbMovie


def _is_retained(movie: Movie) -> bool:
    rate = movie.get_rate()
    return rate.score > 7.0 and rate.votes > 300


_NO_SET = MovieSet(None, None, "TMDB")


async def _enrich_local_movies(movies: list) -> None:
    """Parallel TMDB enrichment; cap to 5 concurrent requests."""
    sem = asyncio.Semaphore(5)

    async def enrich_one(movie):
        async with sem:
            tmdb_movie = await get_tmdb_movie(movie.tmdb_id)
        if tmdb_movie is None:
            return
        movie.tmdb_rate = tmdb_movie.get_rate()
        new_set = tmdb_movie.move_set
        if new_set.set_id is not None and new_set.set_id in movie.skip_collections:
            new_set = _NO_SET
        movie.tmdb_set = new_set

    await asyncio.gather(*[enrich_one(m) for m in movies])


async def _local_movies() -> list:
    loop = asyncio.get_running_loop()
    movies = await loop.run_in_executor(None, crawl_local, conf.MOVIE_ROOT)
    await _enrich_local_movies(movies)
    return movies


def _legal_movie(movie: TmdbMovie) -> bool:
    date_str = movie.get_date()
    if len(date_str) == 0:
        return False
    delta = datetime.today() - datetime.strptime(date_str, "%Y-%m-%d")
    return delta.days > 90


def _movie_to_dict(obj) -> dict:
    titles = obj.get_titles()
    rate = obj.get_rate()
    return {
        "title": titles[0] if titles else "",
        "score": round(rate.score, 1) if rate is not None else None,
        "votes": rate.votes if rate is not None else None,
        "poster": obj.get_poster(),
        "link": obj.get_link(),
        "year": obj.get_year(),
    }


def _serialize(movies) -> list:
    return [_movie_to_dict(m) for m in movies]


async def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    douban_movies = await crawl_douban_250()
    if not douban_movies:
        raise UpstreamUnavailable()
    douban_movies = drop_excluded(douban_movies, read_root_excludes(conf.MOVIE_ROOT))
    local_movies = await _local_movies()

    missing_movies = get_missing_movies(douban_movies, local_movies)
    extra_movies = get_extra_movies(douban_movies, local_movies)
    retained_set_names = {
        m.get_collection_name() for m in extra_movies if _is_retained(m)
    }
    visible_extra = [
        m
        for m in extra_movies
        if not _is_retained(m)
        and (
            m.get_collection_name() is None
            or m.get_collection_name() not in retained_set_names
        )
    ]
    return {
        "missing": _serialize(missing_movies),
        "extra": _serialize(visible_extra),
    }


def _weighted_score(rates) -> Optional[float]:
    total_votes = 0
    weighted = 0.0
    for r in rates:
        if r is None or r.votes <= 0:
            continue
        total_votes += r.votes
        weighted += r.score * r.votes
    if total_votes == 0:
        return None
    return round(weighted / total_votes, 1)


async def series_gaps() -> list:
    """Owned TMDB collections with local and missing members."""
    local_movies = await _local_movies()

    grouped: dict = {}
    for movie in local_movies:
        set_id = movie.tmdb_set.set_id
        if set_id is None:
            continue
        grouped.setdefault(set_id, []).append(movie)

    sem = asyncio.Semaphore(5)

    async def process_set(set_id, locals_):
        async with sem:
            members = await get_tmdb_movies_in_set(set_id)
        if not members:
            return None
        local_ids = {m.tmdb_id for m in locals_}
        missing = [m for m in members if m.tmdb_id not in local_ids and _legal_movie(m)]
        if not missing:
            return None
        member_rates = [m.get_rate() for m in members]
        return {
            "collection_id": set_id,
            "collection_name": members[0].move_set.name,
            "score": _weighted_score(member_rates),
            "votes": sum((r.votes for r in member_rates if r is not None), 0),
            "local": _serialize(locals_),
            "missing": _serialize(missing),
        }

    results = await asyncio.gather(*[process_set(sid, locs) for sid, locs in grouped.items()])
    result = sorted([r for r in results if r is not None], key=lambda x: x["collection_name"] or "")
    return result


async def refresh_all() -> None:
    """Repopulate the upstream Douban / TMDB caches (used by cron)."""
    loop = asyncio.get_running_loop()
    await crawl_douban_250(cache=False)
    movies = await loop.run_in_executor(None, crawl_local, conf.MOVIE_ROOT)

    sem = asyncio.Semaphore(5)

    async def refresh_movie(m):
        async with sem:
            await get_tmdb_movie(m.tmdb_id, cache=False)

    await asyncio.gather(*[refresh_movie(m) for m in movies])
    await _enrich_local_movies(movies)

    set_ids = {m.tmdb_set.set_id for m in movies if m.tmdb_set.set_id is not None}

    async def refresh_set(sid):
        async with sem:
            await get_tmdb_movies_in_set(sid, cache=False)

    await asyncio.gather(*[refresh_set(sid) for sid in set_ids])


def _find_movie_dir(tmdb_id: int) -> Optional[str]:
    base = os.path.realpath(conf.MOVIE_ROOT)
    if not os.path.isdir(base):
        return None
    for current, _dirs, files in os.walk(base):
        for fname in files:
            if not file_filter(fname):
                continue
            try:
                tree = ET.parse(os.path.join(current, fname))
                node = tree.getroot().find("./uniqueid[@type='tmdb']")
                if node is not None and node.text and int(node.text) == tmdb_id:
                    return current
            except (ET.ParseError, ValueError, TypeError):
                continue
    return None


def alias_targets() -> list:
    targets = []
    for local in crawl_local(conf.MOVIE_ROOT):
        targets.append(
            {
                "tmdb_id": local.tmdb_id,
                "title": local.title,
                "year": local.year,
                "poster": local.poster,
            }
        )
    targets.sort(key=lambda x: x["title"] or "")
    return targets


async def _folder_has_subtitle(folder: str, sem: asyncio.Semaphore) -> bool:
    try:
        names = os.listdir(folder)
    except OSError:
        return True
    video_files = [
        os.path.join(folder, n) for n in names
        if os.path.splitext(n)[1].lower() in VIDEO_EXTS
    ]
    if not video_files:
        return False
    results = await asyncio.gather(*[async_has_subtitle(p, sem) for p in video_files])
    return any(results)


async def warm_subtitle_cache() -> None:
    await subtitle_gaps()


async def subtitle_gaps() -> list:
    """Local movies missing both external and embedded subtitles."""
    loop = asyncio.get_running_loop()
    movies = await loop.run_in_executor(None, crawl_local, conf.MOVIE_ROOT)
    ffprobe_sem = asyncio.Semaphore(8)

    async def check_movie(movie):
        if not movie.path:
            return None
        cfg = read_config(movie.path)
        if cfg.get("skip_subtitle_check"):
            return None
        if await _folder_has_subtitle(movie.path, ffprobe_sem):
            return None
        return movie

    results = await asyncio.gather(*[check_movie(m) for m in movies])
    result = sorted(
        [m for m in results if m is not None],
        key=lambda m: (m.title or "").lower(),
    )
    return _serialize(result)


def ignore_subtitle(tmdb_id: int) -> dict:
    base = os.path.realpath(conf.MOVIE_ROOT)
    movie_dir = _find_movie_dir(tmdb_id)
    if movie_dir is None:
        raise ShowNotFound()
    target = os.path.realpath(movie_dir)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()
    return {"updated": set_skip_subtitle_check(target)}


async def ignore_collection(collection_id: int) -> dict:
    base = os.path.realpath(conf.MOVIE_ROOT)
    updated = 0
    for movie in await _local_movies():
        if movie.tmdb_set.set_id != collection_id:
            continue
        if not movie.path:
            continue
        target = os.path.realpath(movie.path)
        if target != base and not target.startswith(base + os.sep):
            continue
        if add_skip_collection(target, collection_id):
            updated += 1
    return {"updated": updated}


def alias_bind(tmdb_id: int, aliases: List[str]) -> dict:
    base = os.path.realpath(conf.MOVIE_ROOT)
    movie_dir = _find_movie_dir(tmdb_id)
    if movie_dir is None:
        raise ShowNotFound()
    target = os.path.realpath(movie_dir)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()
    added = add_aliases(target, aliases)
    return {"bound": True, "added": added}
