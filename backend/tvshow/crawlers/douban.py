"""Douban doulist scraper. Parsing rules unchanged; pages fetched concurrently."""
import asyncio
from typing import List

import bs4

from core import conf
from core.http import async_http_get_with_cache
from tvshow.models import DoubanTvShow, Rate


def parse_cookie(raw: str) -> dict:
    cookies = {}
    for pair in raw.split("; "):
        pair = pair.strip()
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        cookies[key] = value
    return cookies


def _parse_total_pages(html: str) -> int:
    bs = bs4.BeautifulSoup(html, "html.parser")
    paginator = bs.find("div", class_="paginator")
    if paginator is None:
        return 1
    max_number = 1
    for page_number in paginator.find_all("a"):
        number = page_number.get_text().strip()
        if number.isdigit():
            max_number = max(max_number, int(number))
    return max_number


def _parse_page(html: str) -> List[DoubanTvShow]:
    tv_shows = []
    bs = bs4.BeautifulSoup(html, "html.parser")
    article = bs.find("div", class_="article")
    if article is None:
        return tv_shows
    for item in article.find_all("div", class_="doulist-item"):
        if item.find("div", class_="title") is None:
            continue
        title = item.find("div", class_="title").get_text().strip().split(" ")[0]
        link = item.find("div", class_="title").find("a").attrs["href"]
        abstract = item.find("div", class_="abstract").get_text().strip().split("\n")
        year = int(abstract[8].replace("年份:", "").strip())
        country = abstract[6].replace("制片国家/地区:", "").strip()
        style = abstract[4].replace("类型:", "").strip().split(" / ")
        poster = item.find("div", class_="post").find("img").get("src").strip()
        score = float(item.find("span", class_="rating_nums").get_text().strip())
        votes = int(
            item.find("div", class_="rating")
            .select_one("span:last-child")
            .get_text()
            .replace("人评价)", "")
            .replace("(", "")
            .strip()
        )
        tv_shows.append(
            DoubanTvShow(title, year, country, style, poster, link, Rate(score, votes, "豆瓣"))
        )
    return tv_shows


async def crawl_dou_list(url: str, cache: bool = True) -> list:
    cookies = parse_cookie(conf.DOUBAN_COOKIE)
    headers = {"User-Agent": conf.USER_AGENT}

    # Fetch first page to learn total page count
    first_html = await async_http_get_with_cache(
        url,
        cookies=cookies,
        headers=headers,
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        need_cache=cache,
    )
    if first_html is None:
        return []

    total_pages = _parse_total_pages(first_html)

    # Fetch remaining pages concurrently (page 0 already done)
    remaining_urls = [
        url + "?start=" + str(x * 25) + "&sort=seq&playable=0&sub_type="
        for x in range(1, total_pages)
    ]
    page0_url = url + "?start=0&sort=seq&playable=0&sub_type="

    # Re-fetch page 0 with proper query params to get show entries
    responses = await asyncio.gather(*[
        async_http_get_with_cache(
            u,
            cookies=cookies,
            headers=headers,
            cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
            need_cache=cache,
        )
        for u in [page0_url] + remaining_urls
    ])

    tv_shows = []
    for html in responses:
        if html:
            tv_shows += _parse_page(html)
    return tv_shows
