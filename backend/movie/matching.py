"""Movie similarity rules (logic identical to the original ``utils.common``).

The plain "missing" pass uses the shared :func:`core.matching.find_missing`
kernel; the collection-aware "extra" pass stays movie-specific.
"""
from core.matching import find_missing, title_ratio
from movie.models import Movie


def movie_similarity(mv1: Movie, mv2: Movie) -> bool:
    if abs(mv1.get_year() - mv2.get_year()) > 2:
        return False
    for name1 in mv1.get_titles():
        for name2 in mv2.get_titles():
            if title_ratio(name1, name2) > 0.9:
                return True
    return False


def get_missing_movies(target_movies: list, compare_movies: list) -> list:
    return find_missing(target_movies, compare_movies, movie_similarity)


def get_extra_movies(target_movies: list, compare_movies: list) -> list:
    extra_movies = []
    existing_movie_collections = set()

    for compare_movie in compare_movies:
        found = False
        for target_movie in target_movies:
            if movie_similarity(target_movie, compare_movie):
                found = True
                collection_name = compare_movie.get_collection_name()
                if collection_name is not None:
                    existing_movie_collections.add(collection_name)
                break
        if not found:
            extra_movies.append(compare_movie)

    extra_movies_with_unknown_collection = []
    for extra_movie in extra_movies:
        collection_name = extra_movie.get_collection_name()
        if collection_name is None or collection_name not in existing_movie_collections:
            extra_movies_with_unknown_collection.append(extra_movie)

    return extra_movies_with_unknown_collection
