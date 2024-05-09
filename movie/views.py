from django.http import JsonResponse

from movie.utils.local_movie import *
from movie.utils.douban_movie import *
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
