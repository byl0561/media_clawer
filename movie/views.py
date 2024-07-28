import mimetypes

from django.http import JsonResponse, Http404, HttpResponse

from movie.utils.local_movie import *
from movie.utils.douban_movie import *
from movie.utils.tmdb_movie import *
from movie.utils.common import *
from utils.file_utils import read_image_file


def diff_douban_250(request):
    douban_250_movies = crawl_douban_250()
    local_movies = crawl_local(movie_folder)
    missing_movies = get_missing_movies(douban_250_movies, local_movies)
    extra_movies = get_extra_movies(douban_250_movies, local_movies)
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
    local_movies = crawl_local(movie_folder)

    existing_movie_sets = {}
    for movie in local_movies:
        tmdb_set_id = movie.tmdb_set.id
        if tmdb_set_id is None:
            continue
        if tmdb_set_id not in existing_movie_sets:
            existing_movie_sets[tmdb_set_id] = set()
        existing_movie_sets.get(tmdb_set_id).add(movie.tmdb_id)

    resp_dict = {}
    for tmdb_set_id, tmdb_ids in existing_movie_sets.items():
        tmdb_movies_in_set = get_tmdb_movies_in_set(tmdb_set_id)
        missing_movies = []
        for tmdb_movie in tmdb_movies_in_set:
            if tmdb_movie.id not in tmdb_ids and legal_movie(tmdb_movie):
                missing_movies.append(tmdb_movie)
        if len(missing_movies) > 0:
            resp_dict[missing_movies[0].move_set.name] = [missing_movie.to_dict() for missing_movie in missing_movies]

    return JsonResponse(resp_dict)


def legal_movie(movie: TmdbMovie) -> bool:
    date_str = movie.get_date()
    if len(date_str) == 0:
        return False

    timestamp = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.today()
    delta = today - timestamp
    return delta.days > 90


def get_poster(request, image_path):
    full_path = os.path.join(movie_folder, image_path)
    if not os.path.splitext(full_path)[0].endswith('poster'):
        raise Http404()

    data = read_image_file(full_path)
    if data is None:
        raise Http404()

    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    return HttpResponse(data, content_type=mime_type)
