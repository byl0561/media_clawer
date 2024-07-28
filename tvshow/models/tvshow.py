from datetime import datetime
from constant import tmdb_image_path


class Rate:
    def __init__(self, score: float, votes: int, type: str):
        self.score = score
        self.votes = votes
        self.type = type


class Episode:
    def __init__(self,
                 num: int,
                 name: str):
        self.num = num
        self.name = name

    def get_year(self) -> int:
        return -1


class Season:
    def __init__(self,
                 num: int,
                 name: str):
        self.num = num
        self.name = name

    def get_episode(self, episode_num: int) -> Episode or None:
        return None

    def get_max_episode_num(self) -> int:
        return -1

    def get_year(self) -> int:
        return -1

    def list_episodes(self) -> list[Episode] or None:
        return None

    def to_dict(self) -> dict:
        return {
            'num': self.num,
            'name': self.name,
        }


class TvShow:
    def get_titles(self) -> list[str]:
        return []

    def get_years(self) -> list[int]:
        return []

    def get_rate(self) -> Rate or None:
        return None

    def get_season(self, season: int) -> Season or None:
        return None

    def list_seasons(self) -> list[Season] or None:
        return None

    def get_poster(self) -> str or None:
        return None

    def to_dict(self) -> dict:
        return {
            'title': self.get_titles()[0],
            'year': self.get_years(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None,
            'poster': self.get_poster(),
        }


class DoubanTvShow(TvShow):
    def __init__(self,
                 title: str,
                 year: int,
                 country: str,
                 style: list[str],
                 poster: str,
                 douban_rate: Rate):
        self.title = title
        self.year = year
        self.country = country
        self.style = style
        self.poster = poster
        self.douban_rate = douban_rate

    def get_titles(self) -> list[str]:
        return [self.title]

    def get_years(self) -> list[int]:
        return [self.year, self.year]

    def get_rate(self) -> Rate:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster


class BangumiTvShow(TvShow):
    def __init__(self,
                 title: str,
                 origin_title: str or None,
                 date: str,
                 poster: str,
                 bangumi_rate: Rate):
        self.title = title
        self.origin_title = origin_title
        self.date = date
        self.poster = 'https:' + poster
        self.bangumi_rate = bangumi_rate

    def get_titles(self) -> list[str]:
        titles = [self.title]
        if self.origin_title is not None:
            titles.append(self.origin_title)
        return titles

    def get_years(self) -> list[int]:
        year = int(datetime.strptime(self.date, "%Y年%m月%d日").year if len(self.date) > 0 else -1)
        return [year, year]

    def get_date(self) -> str:
        return self.date

    def get_rate(self) -> Rate:
        return self.bangumi_rate

    def get_poster(self) -> str:
        return self.poster


class LocalEpisode(Episode):
    def __init__(self, num: int, name: str, date: str or None, run_minus: int):
        super().__init__(num, name)
        self.date = date
        self.run_minus = run_minus

    def get_year(self) -> int:
        if self.date is None:
            return -1
        return int(datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else -1)


class LocalSeason(Season):
    def __init__(self, num: int, name: str, episodes: list[LocalEpisode]):
        super().__init__(num, name)
        self.episodes = {episode.num: episode for episode in episodes}
        self.max_episode = episodes[-1].num if len(episodes) > 0 else 0
        self.min_episode = episodes[0].num if len(episodes) > 0 else 0

    def get_episode(self, episode_num: int) -> LocalEpisode or None:
        return self.episodes.get(episode_num)

    def get_max_episode_num(self) -> int:
        return self.max_episode

    def get_year(self) -> int:
        if len(self.episodes) == 0:
            return -1
        return self.get_episode(self.min_episode).get_year()

    def list_episodes(self) -> list[LocalEpisode] or None:
        return list(self.episodes.values())


class LocalShadowSeason(Season):
    def __init__(self, num: int, name: str, checked_max_episode: int):
        super().__init__(num, name)
        self.checked_max_episode = checked_max_episode

    def get_max_episode_num(self) -> int:
        return self.checked_max_episode


class LocalTvShow(TvShow):
    def __init__(self,
                 title: str,
                 original_title: str,
                 alias: list[str],
                 year: int,
                 poster: str,
                 tmdb_rate: Rate,
                 tmdb_id: int,
                 seasons: list[LocalSeason],
                 shadow_seasons: list[LocalShadowSeason], ):
        self.title = title
        self.original_title = original_title
        self.alias = alias
        self.year = year
        self.poster = poster
        self.tmdb_rate = tmdb_rate
        self.tmdb_id = tmdb_id
        self.seasons = {season.num: season for season in seasons}
        self.max_season = seasons[-1].num
        self.shadow_seasons = {season.num: season for season in shadow_seasons}

    def get_titles(self) -> list[str]:
        titles = [self.title, self.original_title]
        titles.extend(self.alias)
        return titles

    def get_years(self) -> list[int]:
        return [self.year, self.get_season(self.max_season).get_year()]

    def get_rate(self) -> Rate:
        return self.tmdb_rate

    def get_season(self, season: int) -> LocalSeason or LocalShadowSeason or None:
        res = self.seasons.get(season)
        if res is not None:
            return res
        return self.shadow_seasons.get(season)

    def list_seasons(self) -> list[LocalSeason]:
        return list(self.seasons.values())

    def map_season_max_episode(self) -> dict[int, int]:
        season_max_episode = {}
        for season in self.seasons.values():
            season_max_episode[season.num] = season.get_max_episode_num()
        for season in self.shadow_seasons.values():
            season_max_episode[season.num] = max(season.get_max_episode_num(), season_max_episode.get(season.num, 0))
        return season_max_episode

    def get_poster(self) -> str:
        return self.poster


class TmdbEpisode(Episode):
    def __init__(self, num: int, name: str, date: str, run_minus: int):
        super().__init__(num, name)
        self.date = date
        self.run_minus = run_minus

    def get_year(self) -> int:
        return int(datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else 0)

    def get_date(self) -> str:
        return self.date


class TmdbSeason(Season):
    def __init__(self,
                 num: int,
                 name: str,
                 date: str or None,
                 episodes: list[TmdbEpisode], ):
        super().__init__(num, name)
        self.date = date
        self.episodes = {episode.num: episode for episode in episodes}
        self.max_episode = episodes[-1].num if len(episodes) > 0 else 0
        self.min_episode = episodes[0].num if len(episodes) > 0 else 0

    def get_episode(self, episode_num: int) -> TmdbEpisode or None:
        return self.episodes.get(episode_num)

    def get_max_episode_num(self) -> int:
        return self.max_episode

    def get_year(self) -> int:
        return int(datetime.strptime(self.date, "%Y-%m-%d").year if len(self.date) > 0 else 0)

    def list_episodes(self) -> list[TmdbEpisode] or None:
        return list(self.episodes.values())

    def get_date(self) -> str:
        return self.date


class TmdbTvShow(TvShow):
    def __init__(self,
                 title: str,
                 original_title: str,
                 years: list[int],
                 language: str,
                 poster: str,
                 rate: Rate,
                 id: int,
                 seasons: list[TmdbSeason]):
        self.title = title
        self.original_title = original_title
        self.language = language
        self.years = years
        self.poster = tmdb_image_path + poster
        self.rate = rate
        self.id = id
        self.seasons = {season.num: season for season in seasons}
        self.max_season = seasons[-1].num

    def get_titles(self) -> list[str]:
        return [self.title, self.original_title]

    def get_years(self) -> list[int]:
        return self.years

    def get_rate(self) -> Rate:
        return self.rate

    def get_season(self, season: int) -> TmdbSeason or None:
        return self.seasons.get(season)

    def list_seasons(self) -> list[TmdbSeason]:
        return list(self.seasons.values())

    def get_poster(self) -> str:
        return self.poster
