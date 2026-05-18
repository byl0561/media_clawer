"""Book domain value objects (no Django ORM; crawled + cached)."""
from typing import List, Optional

from core.types import Rate

__all__ = ["Rate", "Book", "DoubanBook", "LocalBook"]


class Book:
    """Common read interface implemented by every book source."""

    def get_titles(self) -> List[str]:
        return []

    def get_author(self) -> Optional[str]:
        return None

    def get_rate(self) -> Optional[Rate]:
        return None

    def get_poster(self) -> Optional[str]:
        return None

    def get_link(self) -> Optional[str]:
        return None


class DoubanBook(Book):
    def __init__(
        self,
        title: str,
        sub_title: Optional[str],
        author: str,
        year: Optional[int],
        poster: str,
        link: str,
        douban_rate: Rate,
    ):
        self.title = title
        self.sub_title = sub_title
        self.author = author
        self.year = year
        self.poster = poster
        self.link = link
        self.douban_rate = douban_rate

    def get_titles(self) -> List[str]:
        titles = [self.title]
        if self.sub_title is not None:
            titles.append(self.sub_title)
        return titles

    def get_author(self) -> Optional[str]:
        return self.author

    def get_year(self) -> Optional[int]:
        return self.year

    def get_rate(self) -> Optional[Rate]:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return self.link


class LocalBook(Book):
    def __init__(
        self,
        title: str,
        alias: List[str],
        author: str,
        poster: Optional[str],
    ):
        self.titles = title.split("_")
        self.alias = alias
        self.author = author
        self.poster = poster

    def get_titles(self) -> List[str]:
        return [*self.titles, *self.alias]

    def get_author(self) -> str:
        return self.author

    def get_poster(self) -> Optional[str]:
        return self.poster
