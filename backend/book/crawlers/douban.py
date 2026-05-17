"""Douban Top 250 book scraper.

Parsing rules unchanged, including the robust ``extract_year`` (the year
column position varies; scan from the end for a 19xx/20xx segment).
"""
import re
from typing import List, Optional

import bs4

from core import conf
from core.http import http_get_with_cache
from book.models import DoubanBook, Rate


def extract_year(pl_parts: List[str]) -> Optional[int]:
    for seg in reversed(pl_parts):
        match = re.search(r"(19|20)\d{2}", seg)
        if match:
            return int(match.group(0))
    return None


def crawl_douban_250(cache: bool = True) -> list:
    books = []

    for x in range(10):
        url = "https://book.douban.com/top250?start=" + str(x * 25)
        res = http_get_with_cache(
            url,
            headers={"User-Agent": conf.USER_AGENT},
            cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
            sleep_s=0,
            need_cache=cache,
        )
        if res is None:
            continue

        bs = bs4.BeautifulSoup(res, "html.parser")
        bs = bs.find("div", class_="indent")
        for item in bs.find_all("table"):
            anchor = item.find("div", class_="pl2").find("a")
            title = anchor.contents[0].strip()
            link = anchor.attrs["href"]
            alias = (
                anchor.find("span").get_text().replace(":", "").strip()
                if anchor.find("span") is not None
                else None
            )
            author = item.find("p", class_="pl").get_text().strip().split(" / ")[0]
            author = re.sub(r"\[[^]]*]", "", author)
            author = re.sub(r"\([^]]*\)", "", author)
            author = re.sub(r"（[^]]*）", "", author)
            author = re.sub(r"【[^]]*】", "", author)
            for noise in ["文", "主编", "著", "编订", "口述"]:
                author = author.replace(" " + noise, "").strip()
            author = author.strip()
            year = extract_year(
                item.find("p", class_="pl").get_text().strip().split(" / ")
            )
            poster = item.find("img").get("src").strip()
            score = float(
                item.find("div", class_="star clearfix")
                .find("span", class_="rating_nums")
                .get_text()
                .strip()
            )
            votes = int(
                item.find("div", class_="star clearfix")
                .find("span", class_="pl")
                .get_text()
                .replace("人评价", "")
                .replace("(", "")
                .replace(")", "")
                .strip()
            )

            book = DoubanBook(
                title, alias, author, year, poster, link, Rate(score, votes, "豆瓣图书")
            )
            if not check(book):
                continue
            books.append(book)

    return books


def check(book: DoubanBook) -> bool:
    young_books = ["中国少年儿童百科全书", "十万个为什么"]
    for title in book.get_titles():
        for young_book in young_books:
            if title in young_book or young_book in title:
                return False
    return True
