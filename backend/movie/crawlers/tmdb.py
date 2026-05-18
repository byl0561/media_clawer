"""TMDB collection ("movie set") lookup. Parsing rules unchanged."""
import json

from core import conf
from core.http import http_get_with_cache
from movie.models import MovieSet, Rate, TmdbMovie


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
