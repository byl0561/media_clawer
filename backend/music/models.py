"""Music album domain value objects (no Django ORM; crawled + cached)."""
from typing import List, Optional

from core.types import Rate

__all__ = ["Rate", "Album", "DoubanAlbum", "LocalAlbum"]


class Album:
    """Common read interface implemented by every album source."""

    def get_titles(self) -> List[str]:
        return []

    def get_artist(self) -> Optional[str]:
        return None

    def get_year(self) -> int:
        return -1

    def get_rate(self) -> Optional[Rate]:
        return None

    def get_poster(self) -> Optional[str]:
        return None

    def get_link(self) -> Optional[str]:
        return None


class DoubanAlbum(Album):
    def __init__(
        self,
        title: str,
        alias: Optional[str],
        artist: str,
        year: int,
        style: str,
        poster: str,
        link: str,
        douban_rate: Rate,
    ):
        self.title = title
        self.alias = alias
        self.artist = artist
        self.year = year
        self.style = style
        self.poster = poster
        self.link = link
        self.douban_rate = douban_rate

    def get_titles(self) -> List[str]:
        titles = [self.title]
        if self.alias is not None:
            titles.append(self.alias)
        return titles

    def get_artist(self) -> Optional[str]:
        return self.artist

    def get_year(self) -> int:
        return self.year

    def get_rate(self) -> Optional[Rate]:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return self.link


class LocalAlbum(Album):
    def __init__(
        self,
        title: str,
        alias: List[str],
        artist: str,
        year: int,
        poster: Optional[str],
    ):
        self.title = title
        self.alias = alias
        self.artist = artist
        self.year = year
        self.poster = poster

    def get_titles(self) -> List[str]:
        return [self.title, *self.alias]

    def get_artist(self) -> Optional[str]:
        return self.artist

    def get_year(self) -> int:
        return self.year

    def get_poster(self) -> Optional[str]:
        return self.poster
