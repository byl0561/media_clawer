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

    def to_dict(self) -> dict:
        return {
            'title': self.get_titles()[0],
            'year': self.get_years(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None
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


class LocalEpisode(Episode):
    def __init__(self, num: int, name: str, date: str, run_minus: int):
        super().__init__(num, name)
        self.date = date
        self.run_minus = run_minus

    def get_year(self) -> int:
        return int(self.date[:4])


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
                 shadow_seasons: list[LocalShadowSeason],):
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


class TmdbSeason(Season):
    def __init__(self,
                 num: int,
                 name: str,
                 date: str or None):
        super().__init__(num, name)
        self.date = date

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
        self.poster = poster
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
