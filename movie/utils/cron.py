from constant import movie_folder
from movie.utils.douban_movie import crawl_douban_250
from movie.utils.local_movie import crawl_local
from movie.utils.tmdb_movie import get_tmdb_movies_in_set


def cronjob():
    crawl_douban_250(cache=False)

    flush_tmdb(movie_folder)


def flush_tmdb(folder):
    local_movies = crawl_local(folder)
    existing_movie_sets = set()
    for movie in local_movies:
        tmdb_set_id = movie.tmdb_set.id
        if tmdb_set_id is None:
            continue
        existing_movie_sets.add(tmdb_set_id)

    for tmdb_set_id in existing_movie_sets:
        get_tmdb_movies_in_set(tmdb_set_id, cache=False)
