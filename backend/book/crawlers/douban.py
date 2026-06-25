"""Douban Top 250 book scraper.

Parsing rules unchanged, including the robust ``extract_year`` (the year
column position varies; scan from the end for a 19xx/20xx segment).
Pages are fetched concurrently.
"""
import asyncio
import re
from typing import List, Optional

import bs4

from core import conf
from core.http import async_http_get_with_cache
from core.matching import title_excluded
from book.models import DoubanBook, Rate

_URL_BASE = "https://book.douban.com/top250?start={}"


def extract_year(pl_parts: List[str]) -> Optional[int]:
    for seg in reversed(pl_parts):
        match = re.search(r"(19|20)\d{2}", seg)
        if match:
            return int(match.group(0))
    return None


def _parse_page(html: str, excludes: List[str]) -> List[DoubanBook]:
    books = []
    bs = bs4.BeautifulSoup(html, "html.parser")
    container = bs.find("div", class_="indent")
    if container is None:
        return books
    for item in container.find_all("table"):
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
        book = DoubanBook(title, alias, author, year, poster, link, Rate(score, votes, "豆瓣图书"))
        if title_excluded(book.get_titles(), excludes):
            continue
        books.append(book)
    return books


async def crawl_douban_250(cache: bool = True, exclude_titles=None) -> list:
    excludes = exclude_titles or []
    urls = [_URL_BASE.format(x * 25) for x in range(10)]
    responses = await asyncio.gather(*[
        async_http_get_with_cache(
            u,
            headers={"User-Agent": conf.USER_AGENT},
            cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
            need_cache=cache,
        )
        for u in urls
    ])
    books = []
    for html in responses:
        if html:
            books += _parse_page(html, excludes)
    return books
