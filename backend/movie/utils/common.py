import difflib

from movie.models.movie import *


def movie_similarity(mv1: Movie, mv2: Movie) -> bool:
    mv1_names = mv1.get_titles()
    mv1_year = mv1.get_year()

    mv2_names = mv2.get_titles()
    mv2_year = mv2.get_year()

    if abs(mv1_year - mv2_year) > 2:
        return False

    for mv1_name in mv1_names:
        for mv2_name in mv2_names:
            if difflib.SequenceMatcher(None, mv1_name, mv2_name).ratio() > 0.9:
                return True

    return False


def get_missing_movies(target_movies: list[Movie], compare_movies: list[Movie]) -> list[Movie]:
    missing_movies = []

    for target_movie in target_movies:
        found = False
        for compare_movie in compare_movies:
            if movie_similarity(target_movie, compare_movie):
                found = True
                break
        if not found:
            missing_movies.append(target_movie)

    return missing_movies


def get_extra_movies(target_movies: list[Movie], compare_movies: list[Movie]) -> list[Movie]:
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
