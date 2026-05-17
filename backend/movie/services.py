"""Movie diff use-cases.

Holds the logic that used to live in ``movie.views`` (crawl + diff + shape
the payload). The diff is recomputed on every request; only the upstream
Douban/TMDB responses stay cached (via :mod:`core.http`), which the cron job
keeps warm.
"""
from datetime import datetime

from core import conf
from core.exceptions import UpstreamUnavailable
from movie.crawlers.douban import crawl_douban_250
from movie.crawlers.local import crawl_local
from movie.crawlers.tmdb import get_tmdb_movies_in_set
from movie.matching import get_extra_movies, get_missing_movies
from movie.models import Movie, TmdbMovie
from movie.serializers import MovieSerializer


def _is_retained(movie: Movie) -> bool:
    rate = movie.get_rate()
    return rate.score > 7.5 and rate.votes > 500


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
    local_movies = crawl_local(conf.MOVIE_ROOT)

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
    local_movies = crawl_local(conf.MOVIE_ROOT)

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
    set_ids = {
        m.tmdb_set.set_id
        for m in crawl_local(conf.MOVIE_ROOT)
        if m.tmdb_set.set_id is not None
    }
    for set_id in set_ids:
        get_tmdb_movies_in_set(set_id, cache=False)
