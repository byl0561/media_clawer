import time

from django.http import JsonResponse

from movie.utils.local_movie import *
from movie.utils.douban_movie import *
from movie.utils.tmdb_movie import *
from movie.utils.common import *

movie_folder = '/Volumes/Movie/'


# Create your views here.

def diff_douban_250(request):
    douban_250_movie = crawl_douban_250()
    local_movie = crawl_local()
    missing_movies = get_missing_movies(douban_250_movie, local_movie)
    extra_movies = get_extra_movies(douban_250_movie, local_movie)
    return JsonResponse({
        'missing_movies': [missing_movie.to_dict() for missing_movie in missing_movies],
        'extra_movies': [extra_movie.to_dict() for extra_movie in extra_movies]
    })


def complete_local_movie_collection(request):
    local_movie = crawl_local()

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
        time.sleep(0.5)
        tmdb_movies_in_set = get_movies_in_set(tmdb_set_id)
        missing_movies = []
        for tmdb_movie in tmdb_movies_in_set:
            if tmdb_movie.id not in tmdb_ids and 0 < tmdb_movie.year <= int(datetime.now().year):
                missing_movies.append(tmdb_movie)
        if len(missing_movies) > 0:
            resp_dict[missing_movies[0].move_set.name] = [missing_movie.to_dict() for missing_movie in missing_movies]

    return JsonResponse(resp_dict)
