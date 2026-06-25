"""Douban Top 250 movie scraper. Parsing rules unchanged; fetches all 10 pages concurrently."""
import asyncio
import re
from typing import List

import bs4

from core import conf
from core.http import async_http_get_with_cache
from movie.models import DoubanMovie, Rate

_URL_BASE = "https://movie.douban.com/top250?start={}&filter="


def _parse_page(html: str) -> List[DoubanMovie]:
    movies = []
    bs = bs4.BeautifulSoup(html, "html.parser")
    grid = bs.find("ol", class_="grid_view")
    if grid is None:
        return movies
    for item in grid.find_all("li"):
        title = []
        for t1 in item.find_all("span", class_="title"):
            for t2 in t1.get_text().split("/"):
                t2 = t2.strip()
                if len(t2) > 0:
                    title.append(t2)
        alias = []
        for al in item.find("span", class_="other").get_text().split("/"):
            al = al.strip()
            if len(al) > 0:
                alias.append(al)
        link = item.find("div", class_="hd").find("a").attrs["href"]
        year_country_style = (
            item.find("div", class_="bd")
            .find("p", class_="")
            .get_text()
            .strip()
            .split("\n")[1]
            .replace('"', "")
            .split("/")
        )
        year = int(re.sub(r"\([^)]*\)", "", year_country_style[0].strip()))
        country = year_country_style[1].strip().split(" ")
        style = year_country_style[2].strip().split(" ")
        poster = item.find("div", class_="pic").find("img").get("src").strip()
        score = float(item.find("span", class_="rating_num").get_text().strip())
        votes = int(
            item.find("div", class_="bd")
            .find("div", class_="")
            .select_one("span:last-child")
            .get_text()
            .replace("人评价", "")
            .strip()
        )
        movies.append(
            DoubanMovie(
                title,
                alias,
                year,
                country,
                style,
                poster,
                link,
                Rate(score, votes, "豆瓣电影"),
            )
        )
    return movies


async def crawl_douban_250(cache: bool = True) -> list:
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
    movies = []
    for html in responses:
        if html:
            movies += _parse_page(html)
    return movies
