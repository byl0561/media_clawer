"""Bangumi anime ranking scraper. Pages are batched concurrently (5 per batch)."""
import asyncio
import re
from datetime import datetime
from typing import List, Optional

import bs4

from core import conf
from core.http import async_http_get_with_cache
from core.matching import title_excluded
from tvshow.models import BangumiTvShow, Rate

_MAX_PAGES = 30
_BATCH_SIZE = 5


def _parse_page(html: str, exclude_titles: List[str]) -> List[BangumiTvShow]:
    items_out = []
    bs = bs4.BeautifulSoup(html, "html.parser")
    container = bs.find("ul", class_="browserFull")
    if container is None:
        return items_out
    for item in container.find_all("li", class_="item"):
        title_index = 0
        title_split_strs = item.find("a", class_="l").get_text().strip().split(" ")
        for index, title_split_str in enumerate(title_split_strs):
            if len(title_split_str) > 1:
                title_index = index
                break

        title = item.find("a", class_="l").get_text().strip().split(" ")[title_index]
        title = trim_title(title)
        id = int(item.find("a", class_="l").get("href").split("/")[-1])
        origin_title = (
            item.find("small", class_="grey").get_text().strip().split(" ")[title_index]
            if item.find("small", class_="grey") is not None
            else None
        )
        match = re.search(
            r"\d{4}年\d{1,2}月\d{1,2}日",
            item.find("p", class_="info tip").get_text().strip(),
        )
        if match is None:
            continue
        date = match.group()
        poster = item.find("span", class_="image").find("img").get("src").strip()
        score = float(
            item.find("p", class_="rateInfo")
            .find("small", class_="fade")
            .get_text()
            .strip()
        )
        votes = int(
            item.find("p", class_="rateInfo")
            .find("span", class_="tip_j")
            .get_text()
            .replace("人评分)", "")
            .replace("(", "")
            .strip()
        )
        anime = BangumiTvShow(
            id, title, origin_title, date, poster, Rate(score, votes, "Bangumi")
        )
        if check(anime, exclude_titles):
            items_out.append(anime)
    return items_out


async def crawl_bangumi_tv_show_80(
    cache: bool = True, exclude_titles: Optional[List[str]] = None
) -> list:
    """Fetch Bangumi rank pages in batches of 5 until 80 unique entries collected."""
    excludes = exclude_titles or []
    tv_shows: List[BangumiTvShow] = []
    seen_names: set = set()

    for batch_start in range(0, _MAX_PAGES, _BATCH_SIZE):
        page_nums = range(batch_start + 1, min(batch_start + _BATCH_SIZE + 1, _MAX_PAGES + 1))
        urls = [
            f"https://bangumi.tv/anime/browser/tv/?sort=rank&page={p}"
            for p in page_nums
        ]
        htmls = await asyncio.gather(*[
            async_http_get_with_cache(
                u,
                headers={"User-Agent": conf.USER_AGENT},
                cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
                need_cache=cache,
            )
            for u in urls
        ])

        batch_had_results = False
        for html in htmls:
            if html is None:
                continue
            for anime in _parse_page(html, excludes):
                titles = anime.get_titles()
                if any(t in seen_names for t in titles):
                    continue
                tv_shows.append(anime)
                seen_names.update(titles)
                batch_had_results = True
                if len(tv_shows) >= 80:
                    return tv_shows[:80]

        # Stop early if the whole batch returned nothing (Bangumi may be down)
        if not batch_had_results and all(h is None for h in htmls):
            break

    return tv_shows[:80]



def check(anime: BangumiTvShow, exclude_titles=None) -> bool:
    if anime.get_years()[0] < 2009:
        return False

    delta = datetime.today() - datetime.strptime(anime.get_date(), "%Y年%m月%d日")
    if delta.days <= 90:
        return False

    if anime.get_rate().votes < 2000:
        return False

    if title_excluded(anime.get_titles(), exclude_titles or []):
        return False

    return True


def trim_title(title):
    """Normalise a scraped Bangumi rank title (strip noise, trailing season digits)."""
    if title is None:
        return None
    for remove_str in ["'", "°"]:
        title = title.replace(remove_str, "")
    return title.rstrip("0123456789")
