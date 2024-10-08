from datetime import datetime
from constant import tmdb_image_path, tmdb_movie_path


class Rate:
    def __init__(self, score: float, votes: int, type: str):
        self.score = score
        self.votes = votes
        self.type = type


class MovieSet:
    def __init__(self, set_id: int, name: str, set_type: str):
        self.set_id = set_id
        self.name = name
        self.set_type = set_type


class Movie:
    def get_titles(self) -> list[str]:
        return []

    def get_year(self) -> int:
        return -1

    def get_collection_name(self) -> str or None:
        return None

    def get_rate(self) -> Rate or None:
        return None

    def get_poster(self) -> str or None:
        return None

    def get_link(self) -> str or None:
        return None

    def to_dict(self) -> dict:
        return {
            'title': self.get_titles()[0],
            'year': self.get_year(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None,
            'poster': self.get_poster(),
            'link': self.get_link(),
        }


class DoubanMovie(Movie):
    def __init__(self,
                 title: list[str],
                 alias: list[str],
                 year: int,
                 country: list[str],
                 style: list[str],
                 poster: str,
                 link: str,
                 douban_rate: Rate):
        self.title = title
        self.alias = alias
        self.year = year
        self.country = country
        self.style = style
        self.poster = poster
        self.link = link
        self.douban_rate = douban_rate

    def get_titles(self) -> list[str]:
        douban_movie_names = []
        douban_movie_names.extend(self.title)
        douban_movie_names.extend(self.alias)
        return douban_movie_names

    def get_year(self) -> int:
        return self.year

    def get_rate(self) -> Rate:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return self.link


class LocalMovie(Movie):
    def __init__(self,
                 title: str,
                 original_title: str,
                 year: int,
                 country: list[str],
                 poster: str,
                 tmdb_rate: Rate,
                 tmdb_id: int,
                 tmdb_set: MovieSet):
        self.title = title
        self.original_title = original_title
        self.year = year
        self.country = country
        self.poster = poster
        self.tmdb_rate = tmdb_rate
        self.tmdb_id = tmdb_id
        self.tmdb_set = tmdb_set

    def get_titles(self) -> list[str]:
        return [self.title, self.original_title]

    def get_year(self) -> int:
        return self.year

    def get_collection_name(self) -> str or None:
        return self.tmdb_set.name if self.tmdb_set is not None else None

    def get_rate(self) -> Rate:
        return self.tmdb_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return f'{tmdb_movie_path}/{self.tmdb_id}'


class TmdbMovie(Movie):
    def __init__(self,
                 title: str,
                 original_title: str,
                 date: str or None,
                 language: str,
                 poster: str,
                 rate: Rate,
                 tmdb_id: int,
                 move_set: MovieSet):
        self.title = title
        self.original_title = original_title
        self.date = date
        self.language = language
        self.poster = (tmdb_image_path + poster) if poster is not None else None
        self.rate = rate
        self.tmdb_id = tmdb_id
        self.move_set = move_set

    def get_titles(self) -> list[str]:
        return [self.title, self.original_title]

    def get_year(self) -> int:
        return int(datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else 0)

    def get_date(self) -> str:
        return self.date

    def get_collection_name(self) -> str or None:
        return self.move_set.name if self.move_set is not None else None

    def get_rate(self) -> Rate:
        return self.rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return f'{tmdb_movie_path}/{self.tmdb_id}'
