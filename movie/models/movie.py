class Rate:
    def __init__(self, score: float, votes: int, type: str):
        self.score = score
        self.votes = votes
        self.type = type


class MovieSet:
    def __init__(self, id: int, name: str, type: str):
        self.id = id
        self.name = name
        self.type = type


class Movie:
    def get_titles(self) -> list[str]:
        return []

    def get_year(self) -> int:
        return -1

    def get_collection_name(self) -> str or None:
        return None

    def get_rate(self) -> Rate or None:
        return None

    def to_dict(self):
        return {
            'title': self.get_titles()[0],
            'year': self.get_year(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None
        }


class DoubanMovie(Movie):
    def __init__(self,
                 title: list[str],
                 alias: list[str],
                 year: int,
                 country: list[str],
                 style: list[str],
                 poster: str,
                 douban_rate: Rate):
        self.title = title
        self.alias = alias
        self.year = year
        self.country = country
        self.style = style
        self.poster = poster
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

    def get_collection_name(self) -> str:
        return self.tmdb_set.name if self.tmdb_set is not None else None

    def get_rate(self) -> Rate:
        return self.tmdb_rate


class TmdbMovie(Movie):
    def __init__(self,
                 title: str,
                 original_title: str,
                 year: int,
                 language: str,
                 poster: str,
                 rate: Rate,
                 id: int,
                 move_set: MovieSet):
        self.title = title
        self.original_title = original_title
        self.year = year
        self.language = language
        self.poster = poster
        self.rate = rate
        self.id = id
        self.move_set = move_set

    def get_titles(self) -> list[str]:
        return [self.title, self.original_title]

    def get_year(self) -> int:
        return self.year

    def get_collection_name(self) -> str:
        return self.move_set.name if self.move_set is not None else None

    def get_rate(self) -> Rate:
        return self.rate
