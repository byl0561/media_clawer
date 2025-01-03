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

    def get_poster(self) -> str or None:
        return None

    def get_link(self) -> str or None:
        return None

    def to_dict(self) -> dict:
        return {
            'title': self.get_titles()[0],
            'author': self.get_author(),
            'score': self.get_rate().score if self.get_rate() is not None else None,
            'votes': self.get_rate().votes if self.get_rate() is not None else None,
            'poster': self.get_poster(),
            'link': self.get_link(),
        }


class DoubanBook(Book):
    def __init__(self,
                 title: str,
                 sub_title: str,
                 author: str,
                 year: int,
                 poster: str,
                 link: str,
                 douban_rate: Rate):
        self.title = title
        self.sub_title = sub_title
        self.author = author
        self.year = year
        self.poster = poster
        self.link = link
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

    def get_poster(self) -> str:
        return self.poster

    def get_link(self) -> str:
        return self.link


class LocalBook(Book):
    def __init__(self,
                 title: str,
                 alias: list[str],
                 author: str,
                 poster: str, ):
        self.titles = title.split('_')
        self.alias = alias
        self.author = author
        self.poster = poster

    def get_titles(self) -> list[str]:
        titles = []
        titles.extend(self.titles)
        titles.extend(self.alias)
        return titles

    def get_author(self) -> str:
        return self.author

    def get_poster(self) -> str:
        return self.poster
