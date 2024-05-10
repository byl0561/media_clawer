import requests

from datetime import datetime
from movie.models.movie import TmdbMovie, Rate, MovieSet

api_key = '5fbd35ed322e13ad05b558f6956b0393'


def get_movies_in_set(movie_set_id: int) -> list[TmdbMovie]:
    url = f'https://api.themoviedb.org/3/collection/{movie_set_id}?api_key={api_key}&language=zh-CN'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        movie_set = MovieSet(data['id'], data['name'], 'TMDB')
        movie_datas = data['parts']
        movies = []
        for movie_data in movie_datas:
            movie = TmdbMovie(movie_data['title'],
                              movie_data['original_title'],
                              int(datetime.strptime(movie_data['release_date'], "%Y-%m-%d").year if len(movie_data['release_date']) > 0 else 0),
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
