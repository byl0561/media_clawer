"""Movie domain value objects.

Plain data classes (not Django ORM models — the project keeps no database;
everything is crawled live and cached in Redis). ``Rate`` now comes from
:mod:`core.types`; presentation moved to :mod:`movie.serializers`.
"""
from datetime import datetime
from typing import List, Optional

from core.conf import TMDB_IMAGE_PATH, TMDB_MOVIE_PATH
from core.types import Rate

__all__ = ["Rate", "MovieSet", "Movie", "DoubanMovie", "LocalMovie", "TmdbMovie"]


class MovieSet:
    def __init__(self, set_id: Optional[int], name: Optional[str], set_type: str):
        self.set_id = set_id
        self.name = name
        self.set_type = set_type


class Movie:
    """Common read interface implemented by every movie source."""

    def get_titles(self) -> List[str]:
        return []

    def get_year(self) -> int:
        return -1

    def get_collection_name(self) -> Optional[str]:
        return None

    def get_rate(self) -> Optional[Rate]:
        return None

    def get_poster(self) -> Optional[str]:
        return None

    def get_link(self) -> Optional[str]:
        return None


class DoubanMovie(Movie):
    def __init__(
        self,
        title: List[str],
        alias: List[str],
        year: int,
        country: List[str],
        style: List[str],
        poster: str,
        link: str,
        douban_rate: Rate,
    ):
        self.title = title
        self.alias = alias
        self.year = year
        self.country = country
        self.style = style
        self.poster = poster
        self.link = link
        self.douban_rate = douban_rate

    def get_titles(self) -> List[str]:
        return [*self.title, *self.alias]

    def get_year(self) -> int:
        return self.year

    def get_rate(self) -> Rate:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return self.link


class LocalMovie(Movie):
    def __init__(
        self,
        title: str,
        original_title: str,
        year: int,
        country: List[str],
        poster: Optional[str],
        tmdb_rate: Rate,
        tmdb_id: int,
        tmdb_set: MovieSet,
        alias: Optional[List[str]] = None,
    ):
        self.title = title
        self.original_title = original_title
        self.year = year
        self.country = country
        self.poster = poster
        self.tmdb_rate = tmdb_rate
        self.tmdb_id = tmdb_id
        self.tmdb_set = tmdb_set
        self.alias = alias or []

    def get_titles(self) -> List[str]:
        return [self.title, self.original_title, *self.alias]

    def get_year(self) -> int:
        return self.year

    def get_collection_name(self) -> Optional[str]:
        return self.tmdb_set.name if self.tmdb_set is not None else None

    def get_rate(self) -> Rate:
        return self.tmdb_rate

    def get_poster(self) -> Optional[str]:
        return self.poster

    def get_link(self) -> str:
        return f"{TMDB_MOVIE_PATH}/{self.tmdb_id}"


class TmdbMovie(Movie):
    def __init__(
        self,
        title: str,
        original_title: str,
        date: Optional[str],
        language: str,
        poster: Optional[str],
        rate: Rate,
        tmdb_id: int,
        move_set: MovieSet,
    ):
        self.title = title
        self.original_title = original_title
        self.date = date
        self.language = language
        self.poster = (TMDB_IMAGE_PATH + poster) if poster is not None else None
        self.rate = rate
        self.tmdb_id = tmdb_id
        self.move_set = move_set

    def get_titles(self) -> List[str]:
        return [self.title, self.original_title]

    def get_year(self) -> int:
        return int(
            datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else 0
        )

    def get_date(self) -> str:
        return self.date

    def get_collection_name(self) -> Optional[str]:
        return self.move_set.name if self.move_set is not None else None

    def get_rate(self) -> Rate:
        return self.rate

    def get_poster(self) -> Optional[str]:
        return self.poster

    def get_link(self) -> str:
        return f"{TMDB_MOVIE_PATH}/{self.tmdb_id}"
