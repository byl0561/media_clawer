class Rate:
    def __init__(self, score: float, votes: int, type: str):
        self.score = score
        self.votes = votes
        self.type = type

class Season:
    def __init__(self, num: int):
        self.num = num


class Episode:
    def __init__(self, num: int):
        self.num = num


class TvShow:
    def get_titles(self) -> list[str]:
        return []

    def get_year(self) -> list[int]:
        return []

    def get_rate(self) -> Rate or None:
        return None

    def to_dict(self):
        return {
            'title': self.get_titles()[0],
            'year': self.get_year(),
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

    def get_year(self) -> list[int]:
        return [self.year]

    def get_rate(self) -> Rate:
        return self.douban_rate