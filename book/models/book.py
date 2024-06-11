class Rate:
    def __init__(self, score: float, votes: int, type: str):
        self.score = score
        self.votes = votes
        self.type = type


class Book:
    def get_titles(self) -> list[str]:
        return []

    def get_author(self) -> str or None:
        return None

    def get_rate(self) -> Rate or None:
        return None

    def to_dict(self) -> dict:
        return {
            'title': self.get_titles()[0],
            'author': self.get_author(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None
        }


class DoubanBook(Book):
    def __init__(self,
                 title: str,
                 sub_title: str,
                 author: str,
                 year: int,
                 poster: str,
                 douban_rate: Rate):
        self.title = title
        self.sub_title = sub_title
        self.author = author
        self.year = year
        self.poster = poster
        self.douban_rate = douban_rate

    def get_titles(self) -> list[str]:
        title = [self.title]
        if self.sub_title is not None:
            title.append(self.sub_title)
        return title

    def get_author(self) -> str or None:
        return self.author

    def get_year(self) -> int:
        return self.year

    def get_rate(self) -> Rate or None:
        return self.douban_rate

class LocalBook(Book):
    def __init__(self,
                 title: str,
                 author: str):
        self.title = title
        self.author = author

    def get_titles(self) -> list[str]:
        return [self.title]

    def get_author(self) -> str or None:
        return self.author
