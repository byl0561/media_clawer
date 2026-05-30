"""TV show / anime domain value objects (no Django ORM; crawled + cached).

Logic is unchanged from the original ``models/tvshow.py`` except: ``Rate``
comes from :mod:`core.types`, ``str or None`` hints are real ``Optional``s,
``to_dict`` moved to serializers, and the empty-season ``[-1]`` indexing is
guarded so a partially-scraped local show can't 500 the endpoint.
"""
from datetime import datetime
from typing import Dict, List, Optional

from core.conf import BANGUMI_ANIME_PATH, TMDB_IMAGE_PATH, TMDB_TV_PATH
from core.types import Rate

__all__ = [
    "Rate",
    "Episode",
    "Season",
    "TvShow",
    "DoubanTvShow",
    "BangumiTvShow",
    "LocalEpisode",
    "LocalSeason",
    "LocalShadowSeason",
    "LocalTvShow",
    "TmdbEpisode",
    "TmdbSeason",
    "TmdbTvShow",
]


class Episode:
    def __init__(self, num: int, name: str):
        self.num = num
        self.name = name

    def get_year(self) -> int:
        return -1


class Season:
    def __init__(self, num: int, name: str):
        self.num = num
        self.name = name

    def get_episode(self, episode_num: int) -> Optional[Episode]:
        return None

    def get_max_episode_num(self) -> int:
        return -1

    def get_year(self) -> int:
        return -1

    def list_episodes(self) -> Optional[List[Episode]]:
        return None


class TvShow:
    """Common read interface implemented by every TV/anime source."""

    def get_titles(self) -> List[str]:
        return []

    def get_years(self) -> List[int]:
        return []

    def get_rate(self) -> Optional[Rate]:
        return None

    def get_season(self, season: int) -> Optional[Season]:
        return None

    def list_seasons(self) -> Optional[List[Season]]:
        return None

    def get_poster(self) -> Optional[str]:
        return None

    def get_link(self) -> Optional[str]:
        return None


class DoubanTvShow(TvShow):
    def __init__(
        self,
        title: str,
        year: int,
        country: str,
        style: List[str],
        poster: str,
        link: str,
        douban_rate: Rate,
    ):
        self.title = title
        self.year = year
        self.country = country
        self.style = style
        self.poster = poster
        self.link = link
        self.douban_rate = douban_rate

    def get_titles(self) -> List[str]:
        return [self.title]

    def get_years(self) -> List[int]:
        return [self.year, self.year]

    def get_rate(self) -> Rate:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return self.link


class BangumiTvShow(TvShow):
    def __init__(
        self,
        bangumi_id: int,
        title: str,
        origin_title: Optional[str],
        date: str,
        poster: str,
        bangumi_rate: Rate,
    ):
        self.bangumi_id = bangumi_id
        self.title = title
        self.origin_title = origin_title
        self.date = date
        self.poster = "https:" + poster
        self.bangumi_rate = bangumi_rate

    def get_titles(self) -> List[str]:
        titles = [self.title]
        if self.origin_title is not None:
            titles.append(self.origin_title)
        return titles

    def get_years(self) -> List[int]:
        year = int(
            datetime.strptime(self.date, "%Y年%m月%d日").year
            if len(self.date) > 0
            else -1
        )
        return [year, year]

    def get_date(self) -> str:
        return self.date

    def get_rate(self) -> Rate:
        return self.bangumi_rate

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return f"{BANGUMI_ANIME_PATH}/{self.bangumi_id}"


class LocalEpisode(Episode):
    def __init__(self, num: int, name: str, date: Optional[str], run_minus: int):
        super().__init__(num, name)
        self.date = date
        self.run_minus = run_minus

    def get_year(self) -> int:
        if self.date is None:
            return -1
        return int(
            datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else -1
        )


class LocalSeason(Season):
    def __init__(self, num: int, name: str, episodes: List[LocalEpisode]):
        super().__init__(num, name)
        self.episodes = {episode.num: episode for episode in episodes}
        self.max_episode = episodes[-1].num if len(episodes) > 0 else 0
        self.min_episode = episodes[0].num if len(episodes) > 0 else 0

    def get_episode(self, episode_num: int) -> Optional[LocalEpisode]:
        return self.episodes.get(episode_num)

    def get_max_episode_num(self) -> int:
        return self.max_episode

    def get_year(self) -> int:
        if len(self.episodes) == 0:
            return -1
        return self.get_episode(self.min_episode).get_year()

    def list_episodes(self) -> Optional[List[LocalEpisode]]:
        return list(self.episodes.values())


class LocalShadowSeason(Season):
    def __init__(self, num: int, name: str, checked_max_episode: int):
        super().__init__(num, name)
        self.checked_max_episode = checked_max_episode

    def get_max_episode_num(self) -> int:
        return self.checked_max_episode


class LocalTvShow(TvShow):
    def __init__(
        self,
        title: str,
        original_title: str,
        alias: List[str],
        year: int,
        poster: Optional[str],
        tmdb_rate: Rate,
        tmdb_id: int,
        seasons: List[LocalSeason],
        shadow_seasons: List[LocalShadowSeason],
        path: Optional[str] = None,
    ):
        self.title = title
        self.original_title = original_title
        self.alias = alias
        self.year = year
        self.poster = poster
        self.tmdb_rate = tmdb_rate
        self.tmdb_id = tmdb_id
        self.seasons = {season.num: season for season in seasons}
        self.max_season = seasons[-1].num if seasons else 0
        self.shadow_seasons = {season.num: season for season in shadow_seasons}
        # Absolute path of the show folder (where .mediaclawer.json lives).
        self.path = path

    def get_titles(self) -> List[str]:
        return [self.title, self.original_title, *self.alias]

    def get_years(self) -> List[int]:
        last_season = self.get_season(self.max_season)
        return [self.year, last_season.get_year() if last_season else self.year]

    def get_rate(self) -> Rate:
        return self.tmdb_rate

    def get_season(self, season: int) -> Optional[Season]:
        res = self.seasons.get(season)
        if res is not None:
            return res
        return self.shadow_seasons.get(season)

    def list_seasons(self) -> List[LocalSeason]:
        return list(self.seasons.values())

    def map_season_max_episode(self) -> Dict[int, int]:
        season_max_episode: Dict[int, int] = {}
        for season in self.seasons.values():
            season_max_episode[season.num] = season.get_max_episode_num()
        for season in self.shadow_seasons.values():
            season_max_episode[season.num] = max(
                season.get_max_episode_num(), season_max_episode.get(season.num, 0)
            )
        return season_max_episode

    def get_poster(self) -> Optional[str]:
        return self.poster

    def get_link(self) -> str:
        return f"{TMDB_TV_PATH}/{self.tmdb_id}"


class TmdbEpisode(Episode):
    def __init__(self, num: int, name: str, date: str, run_minus: int):
        super().__init__(num, name)
        self.date = date
        self.run_minus = run_minus

    def get_year(self) -> int:
        return int(
            datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else 0
        )

    def get_date(self) -> str:
        return self.date


class TmdbSeason(Season):
    def __init__(
        self,
        num: int,
        name: str,
        date: Optional[str],
        episodes: List[TmdbEpisode],
        poster: Optional[str] = None,
        rate: Optional[Rate] = None,
    ):
        super().__init__(num, name)
        self.date = date
        self.episodes = {episode.num: episode for episode in episodes}
        self.max_episode = episodes[-1].num if len(episodes) > 0 else 0
        self.min_episode = episodes[0].num if len(episodes) > 0 else 0
        self.poster = (TMDB_IMAGE_PATH + poster) if poster else None
        self.rate = rate

    def get_episode(self, episode_num: int) -> Optional[TmdbEpisode]:
        return self.episodes.get(episode_num)

    def get_max_episode_num(self) -> int:
        return self.max_episode

    def get_year(self) -> int:
        return int(
            datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else 0
        )

    def list_episodes(self) -> Optional[List[TmdbEpisode]]:
        return list(self.episodes.values())

    def get_date(self) -> Optional[str]:
        return self.date


class TmdbTvShow(TvShow):
    def __init__(
        self,
        title: str,
        original_title: str,
        years: List[int],
        language: str,
        poster: str,
        rate: Rate,
        tmdb_id: int,
        seasons: List[TmdbSeason],
    ):
        self.title = title
        self.original_title = original_title
        self.language = language
        self.years = years
        self.poster = TMDB_IMAGE_PATH + poster
        self.rate = rate
        self.tmdb_id = tmdb_id
        self.seasons = {season.num: season for season in seasons}
        self.max_season = seasons[-1].num if seasons else 0

    def get_titles(self) -> List[str]:
        return [self.title, self.original_title]

    def get_years(self) -> List[int]:
        return self.years

    def get_rate(self) -> Rate:
        return self.rate

    def get_season(self, season: int) -> Optional[TmdbSeason]:
        return self.seasons.get(season)

    def list_seasons(self) -> List[TmdbSeason]:
        return list(self.seasons.values())

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return f"{TMDB_TV_PATH}/{self.tmdb_id}"
