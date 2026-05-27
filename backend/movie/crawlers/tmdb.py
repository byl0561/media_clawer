"""TMDB collection ("movie set") and single-movie lookup."""
import json
from typing import Optional

from core import conf
from core.http import http_get_with_cache
from movie.models import MovieSet, Rate, TmdbMovie


def get_tmdb_movie(tmdb_id: int, cache: bool = True) -> Optional[TmdbMovie]:
    """Single-movie payload used to backfill MoviePilot NFOs.

    MP NFOs (current as of 2026-05) emit only a flat ``<rating>`` and no
    ``<set>``/``<uniqueid type="tmdbSet">``. ``votes`` and ``belongs_to_collection``
    are pulled from here so the retention threshold and the sequel-tied
    carry-over can do their job — see ``movie.services._enrich_local_movies``.
    """
    url = (
        f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        f"?api_key={conf.TMDB_API_KEY}&language=zh-CN"
    )
    res = http_get_with_cache(
        url,
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        sleep_s=0.2,
        need_cache=cache,
        retry=True,
    )
    if res is None:
        return None

    data = json.loads(res)
    collection = data.get("belongs_to_collection")
    movie_set = MovieSet(
        collection["id"] if collection else None,
        collection["name"] if collection else None,
        "TMDB",
    )
    return TmdbMovie(
        data["title"],
        data["original_title"],
        data.get("release_date") or "",
        data["original_language"],
        data.get("poster_path"),
        Rate(data["vote_average"], data["vote_count"], "TMDB"),
        data["id"],
        movie_set,
    )


def get_tmdb_movies_in_set(movie_set_id: int, cache: bool = True) -> list:
    url = (
        f"https://api.themoviedb.org/3/collection/{movie_set_id}"
        f"?api_key={conf.TMDB_API_KEY}&language=zh-CN"
    )
    res = http_get_with_cache(
        url,
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        sleep_s=0.2,
        need_cache=cache,
        retry=True,
    )
    if res is None:
        return []

    data = json.loads(res)
    movie_set = MovieSet(data["id"], data["name"], "TMDB")
    movies = []
    for movie_data in data["parts"]:
        movies.append(
            TmdbMovie(
                movie_data["title"],
                movie_data["original_title"],
                movie_data["release_date"],
                movie_data["original_language"],
                movie_data["poster_path"],
                Rate(movie_data["vote_average"], movie_data["vote_count"], "TMDB"),
                movie_data["id"],
                movie_set,
            )
        )

    return movies
