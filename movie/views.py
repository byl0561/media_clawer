import time

from django.http import JsonResponse

from constant import movie_folder
from movie.utils.local_movie import *
from movie.utils.douban_movie import *
from movie.utils.tmdb_movie import *
from movie.utils.common import *


def diff_douban_250(request):
    douban_250_movie = crawl_douban_250()
    local_movie = crawl_local(movie_folder)
    missing_movies = get_missing_movies(douban_250_movie, local_movie)
    extra_movies = get_extra_movies(douban_250_movie, local_movie)
    retained_extra_movie_set_names = set([extra_movie.get_collection_name() for extra_movie in extra_movies
                                          if is_retained(extra_movie)])

    return JsonResponse({
        'missing_movies': [missing_movie.to_dict() for missing_movie in missing_movies],
        'extra_movies': [extra_movie.to_dict() for extra_movie in extra_movies
                         if not is_retained(extra_movie) and
                         (extra_movie.get_collection_name() is None
                          or extra_movie.get_collection_name() not in retained_extra_movie_set_names)],
    })


def is_retained(movie: Movie) -> bool:
    return movie.get_rate().score > 7.5 and movie.get_rate().votes > 500


def complete_local_movie_collection(request):
    local_movie = crawl_local(movie_folder)

    existing_movie_sets = {}
    for movie in local_movie:
        tmdb_set_id = movie.tmdb_set.id
        if tmdb_set_id is None:
            continue
        if tmdb_set_id not in existing_movie_sets:
            existing_movie_sets[tmdb_set_id] = set()
        existing_movie_sets.get(tmdb_set_id).add(movie.tmdb_id)

    resp_dict = {}
    for tmdb_set_id, tmdb_ids in existing_movie_sets.items():
        time.sleep(0.2)
        tmdb_movies_in_set = get_movies_in_set(tmdb_set_id)
        missing_movies = []
        for tmdb_movie in tmdb_movies_in_set:
            if tmdb_movie.id not in tmdb_ids and legal_movie(tmdb_movie):
                missing_movies.append(tmdb_movie)
        if len(missing_movies) > 0:
            resp_dict[missing_movies[0].move_set.name] = [missing_movie.to_dict() for missing_movie in missing_movies]

    return JsonResponse(resp_dict)


def legal_movie(movie: Movie) -> bool:
    return (0 < movie.get_year() < int(datetime.now().year) or
            (movie.get_year() == int(datetime.now().year) and movie.get_rate().score > 0))
