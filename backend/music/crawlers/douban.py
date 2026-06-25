"""Douban Top 250 album scraper. Parsing rules unchanged; pages fetched concurrently."""
import asyncio
from typing import List

import bs4

from core import conf
from core.http import async_http_get_with_cache
from music.models import DoubanAlbum, Rate

_URL_BASE = "https://music.douban.com/top250?start={}"


def _parse_page(html: str) -> List[DoubanAlbum]:
    albums = []
    bs = bs4.BeautifulSoup(html, "html.parser")
    container = bs.find("div", class_="indent")
    if container is None:
        return albums
    for item in container.find_all("table"):
        pl2 = item.find("div", class_="pl2")
        anchor = pl2.find("a")
        title = anchor.contents[0].strip()
        link = anchor.attrs["href"]
        alias = (
            anchor.find("span").get_text().strip()
            if anchor.find("span") is not None
            else None
        )
        pl = pl2.find("p", class_="pl").get_text().strip().split(" / ")
        artist = pl[0]
        year = int(pl[1][:4])
        style = pl[-1]
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
        albums.append(
            DoubanAlbum(
                title,
                alias,
                artist,
                year,
                style,
                poster,
                link,
                Rate(score, votes, "豆瓣音乐"),
            )
        )
    return albums


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
    albums = []
    for html in responses:
        if html:
            albums += _parse_page(html)
    return albums
