import requests
from constant import *
from movie.models.movie import TmdbMovie, Rate, MovieSet


def get_tmdb_movies_in_set(movie_set_id: int) -> list[TmdbMovie]:
    url = f'https://api.themoviedb.org/3/collection/{movie_set_id}?api_key={tmdb_api_key}&language=zh-CN'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        movie_set = MovieSet(data['id'], data['name'], 'TMDB')
        movie_datas = data['parts']
        movies = []
        for movie_data in movie_datas:
            movie = TmdbMovie(movie_data['title'],
                              movie_data['original_title'],
                              movie_data['release_date'],
                              movie_data['original_language'],
                              movie_data['poster_path'],
                              Rate(movie_data['vote_average'], movie_data['vote_count'], 'TMDB'),
                              movie_data['id'],
                              movie_set)
            movies.append(movie)

        return movies
    else:
        print('Failed to fetch data')
        return []
