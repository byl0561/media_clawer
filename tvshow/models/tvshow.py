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


class TvShow:
    def get_titles(self) -> list[str]:
        return []

    def get_years(self) -> list[int]:
        return []

    def get_rate(self) -> Rate or None:
        return None

    def get_season(self, season: int) -> Season or None:
        return None

    def to_dict(self):
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


class LocalTvShow(TvShow):
    def __init__(self,
                 title: str,
                 original_title: str,
                 alias: list[str],
                 year: int,
                 poster: str,
                 tmdb_rate: Rate,
                 tmdb_id: int,
                 seasons: list[Season]):
        self.title = title
        self.original_title = original_title
        self.alias = alias
        self.year = year
        self.poster = poster
        self.tmdb_rate = tmdb_rate
        self.tmdb_id = tmdb_id
        self.seasons = {season.num: season for season in seasons}
        self.max_season = seasons[-1].num

    def get_titles(self) -> list[str]:
        titles = [self.title, self.original_title]
        titles.extend(self.alias)
        return titles

    def get_years(self) -> list[int]:
        return [self.year, self.get_season(self.max_season).get_year()]

    def get_rate(self) -> Rate:
        return self.tmdb_rate

    def get_season(self, season: int) -> Season or None:
        return self.seasons.get(season)


class LocalSeason(Season):
    def __init__(self, num: int, name: str, episodes: list[Episode]):
        super().__init__(num, name)
        self.episodes = {episode.num: episode for episode in episodes}
        self.max_episode = episodes[-1].num
        self.min_episode = episodes[0].num

    def get_episode(self, episode_num: int) -> Episode or None:
        return self.episodes.get(episode_num)

    def get_max_episode_num(self) -> int:
        return self.max_episode

    def get_year(self) -> int:
        return self.get_episode(self.min_episode).get_year()


class LocalEpisode(Episode):
    def __init__(self, num: int, name: str, date: str, run_minus: int):
        super().__init__(num, name)
        self.date = date
        self.run_minus = run_minus

    def get_year(self) -> int:
        return int(self.date[:4])
