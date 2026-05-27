"""Movie diff use-cases.

Holds the logic that used to live in ``movie.views`` (crawl + diff + shape
the payload). The diff is recomputed on every request; only the upstream
Douban/TMDB responses stay cached (via :mod:`core.http`), which the cron job
keeps warm.
"""
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

from core import conf
from core.aliases import append_unique_aliases
from core.exceptions import ShowNotFound, UpstreamUnavailable
from movie.crawlers.douban import crawl_douban_250
from movie.crawlers.local import crawl_local, file_filter
from movie.crawlers.tmdb import get_tmdb_movie, get_tmdb_movies_in_set
from movie.matching import get_extra_movies, get_missing_movies
from movie.models import Movie, TmdbMovie
from movie.serializers import MovieSerializer


def _is_retained(movie: Movie) -> bool:
    rate = movie.get_rate()
    # Matches TMDB's own /movie/top_rated cutoff (votes >= 300); score ≥ 7.0
    # keeps "decent" Top250 dropouts. Lower thresholds let lucky-high noise in.
    return rate.score > 7.0 and rate.votes > 300


def _enrich_local_movies(movies: list) -> None:
    """Replace each local movie's TMDB rate + collection with live ``/movie/{id}``.

    MoviePilot NFOs ship only a flat ``<rating>`` and no ``<set>`` /
    ``<uniqueid type="tmdbSet">``, and even tmm NFOs are scrape-time snapshots
    that drift from current TMDB. The diff is recomputed per request, so we
    always pull fresh — that way the retention threshold and the collection-
    tied carry-over both see the canonical current values regardless of NFO
    vintage. Cache-hit on the warm path since :func:`refresh_all` pre-warms.
    """
    for movie in movies:
        tmdb_movie = get_tmdb_movie(movie.tmdb_id)
        if tmdb_movie is None:
            continue
        movie.tmdb_rate = tmdb_movie.get_rate()
        movie.tmdb_set = tmdb_movie.move_set


def _local_movies() -> list:
    movies = crawl_local(conf.MOVIE_ROOT)
    _enrich_local_movies(movies)
    return movies


def _legal_movie(movie: TmdbMovie) -> bool:
    date_str = movie.get_date()
    if len(date_str) == 0:
        return False
    delta = datetime.today() - datetime.strptime(date_str, "%Y-%m-%d")
    return delta.days > 90


def _serialize(movies) -> list:
    return MovieSerializer(movies, many=True).data


def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    douban_movies = crawl_douban_250()
    if not douban_movies:
        raise UpstreamUnavailable()
    local_movies = _local_movies()

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


def collection_gaps() -> list:
    """Owned TMDB collections with entries missing locally.

    -> [{"collection": <name>, "missing": [<movie>, ...]}, ...]
    """
    local_movies = _local_movies()

    existing_movie_sets: dict = {}
    for movie in local_movies:
        tmdb_set_id = movie.tmdb_set.set_id
        if tmdb_set_id is None:
            continue
        existing_movie_sets.setdefault(tmdb_set_id, set()).add(movie.tmdb_id)

    result = []
    for tmdb_set_id, tmdb_ids in existing_movie_sets.items():
        missing = [
            m
            for m in get_tmdb_movies_in_set(tmdb_set_id)
            if m.tmdb_id not in tmdb_ids and _legal_movie(m)
        ]
        if missing:
            result.append(
                {
                    "collection": missing[0].move_set.name,
                    "missing": _serialize(missing),
                }
            )
    return result


def refresh_all() -> None:
    """Repopulate the upstream Douban / TMDB caches (used by cron)."""
    crawl_douban_250(cache=False)
    movies = crawl_local(conf.MOVIE_ROOT)
    for m in movies:
        get_tmdb_movie(m.tmdb_id, cache=False)
    _enrich_local_movies(movies)
    set_ids = {m.tmdb_set.set_id for m in movies if m.tmdb_set.set_id is not None}
    for set_id in set_ids:
        get_tmdb_movies_in_set(set_id, cache=False)


# --- Alias bind (manual chinese-title supplement) -----------------------
# See tvshow.services for the design rationale. Movies use the same flow:
# locate the on-disk folder by TMDB id, append rank titles to alias.txt so
# the next list/local diff text-matches them.


def _find_movie_dir(tmdb_id: int) -> Optional[str]:
    """Directory of the movie nfo whose tmdb ``uniqueid`` == ``tmdb_id``.

    ``file_filter`` accepts both tmm's ``movie.nfo`` and MoviePilot's
    ``{title} ({year}).nfo``, so this works on mixed libraries.
    """
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
    """All local movies usable as bind targets for a missing rank item."""
    targets = []
    for local in crawl_local(conf.MOVIE_ROOT):  # no enrichment needed; only metadata read
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


def alias_bind(tmdb_id: int, aliases: List[str]) -> dict:
    """Append ``aliases`` to the matched movie's ``alias.txt``."""
    base = os.path.realpath(conf.MOVIE_ROOT)
    movie_dir = _find_movie_dir(tmdb_id)
    if movie_dir is None:
        raise ShowNotFound()

    target = os.path.realpath(movie_dir)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()

    added = append_unique_aliases(target, aliases)
    return {"bound": True, "added": added}
