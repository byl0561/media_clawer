class Rate:
    def __init__(self, score: float, votes: int):
        self.score = score
        self.votes = votes


class MovieSet:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class Movie:
    def get_titles(self) -> list[str]:
        return []

    def get_year(self) -> int:
        return -1

    def get_collection_name(self) -> str:
        return None

    def to_dict(self):
        return {'title': self.get_titles()[0], 'year': self.get_year()}


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
