class Rate:
    def __init__(self, score: float, votes: int, type: str):
        self.score = score
        self.votes = votes
        self.type = type


class Album:
    def get_titles(self) -> list[str]:
        return []

    def get_artist(self) -> str or None:
        return None

    def get_year(self) -> int:
        return -1

    def get_rate(self) -> Rate or None:
        return None

    def get_poster(self) -> str or None:
        return None

    def to_dict(self) -> dict:
        return {
            'title': self.get_titles()[0],
            'artist': self.get_artist(),
            'year': self.get_year(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None,
            'poster': self.get_poster(),
        }


class DoubanAlbum(Album):
    def __init__(self,
                 title: str,
                 alias: str,
                 artist: str,
                 year: int,
                 style: str,
                 poster: str,
                 douban_rate: Rate):
        self.title = title
        self.alias = alias
        self.artist = artist
        self.year = year
        self.style = style
        self.poster = poster
        self.douban_rate = douban_rate

    def get_titles(self) -> list[str]:
        title = [self.title]
        if self.alias is not None:
            title.append(self.alias)
        return title

    def get_artist(self) -> str or None:
        return self.artist

    def get_year(self) -> int:
        return self.year

    def get_rate(self) -> Rate or None:
        return self.douban_rate

    def get_poster(self) -> str:
        return self.poster


class LocalAlbum(Album):
    def __init__(self,
                 title: str,
                 alias: list[str],
                 artist: str,
                 year: int):
        self.title = title
        self.alias = alias
        self.artist = artist
        self.year = year

    def get_titles(self) -> list[str]:
        titles = [self.title]
        titles.extend(self.alias)
        return titles

    def get_artist(self) -> str or None:
        return self.artist

    def get_year(self) -> int:
        return self.year
