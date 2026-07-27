"""Bangumi anime ranking scrapers.

Two sources feed the anime diff and are merged by :func:`crawl_bangumi_anime`:

* the ranked browser pages (batched 5 per request round), and
* curated index lists (``/index/{id}``), whose markup carries neither a
  rating nor a Chinese title, so every entry is completed through the public
  subject API.

Both paths end up in the same :func:`check` gate, so the year / airing-delay /
vote / exclude rules stay identical across sources.
"""
import asyncio
import json
import re
from datetime import datetime
from typing import List, Optional, Tuple

import bs4

from core import conf
from core.http import async_http_get_with_cache
from core.matching import title_excluded
from tvshow.matching import combine_tv_show
from tvshow.models import BangumiTvShow, Rate

_MAX_PAGES = 30
_BATCH_SIZE = 5

# Curated index lists merged into the ranked browser results.
_INDEX_URLS = ["https://bangumi.tv/index/55040?cat=2"]

_SUBJECT_API = "https://api.bgm.tv/v0/subjects"
_SUBJECT_CONCURRENCY = 5
# Index lists mix films in with TV series. The local anime library is a TV
# library (scanned from tvshow.nfo), so a film could never match anything and
# would sit in "missing" forever.
_EXCLUDED_PLATFORMS = {"剧场版"}


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


def _parse_index_page(html: str) -> List[Tuple[int, Optional[str]]]:
    """Pull ``(subject_id, poster)`` out of an index list page.

    Index markup has no ``rateInfo`` / ``small.grey``, so everything else has
    to come from the subject API.
    """
    entries: List[Tuple[int, Optional[str]]] = []
    bs = bs4.BeautifulSoup(html, "html.parser")
    container = bs.find("ul", class_="browserFull")
    if container is None:
        return entries
    for item in container.find_all("li", class_="item"):
        link = item.find("a", class_="l")
        if link is None:
            continue
        try:
            subject_id = int(link.get("href").split("/")[-1])
        except (AttributeError, TypeError, ValueError):
            continue
        image = item.find("span", class_="image")
        img = image.find("img") if image is not None else None
        src = img.get("src") if img is not None else None
        entries.append((subject_id, src.strip() if src else None))
    return entries


def _protocol_relative(url: Optional[str]) -> Optional[str]:
    """BangumiTvShow prepends ``https:`` itself, so hand it a //-relative URL."""
    if url is None:
        return None
    return url[len("https:"):] if url.startswith("https:") else url


def _cn_date(iso_date: Optional[str]) -> Optional[str]:
    """Convert the API's ``2011-04-06`` into the ``2011年4月6日`` the model parses."""
    if not iso_date:
        return None
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    except ValueError:
        return None
    return f"{parsed.year}年{parsed.month}月{parsed.day}日"


async def _fetch_subject(
    subject_id: int, poster: Optional[str], cache: bool, sem: asyncio.Semaphore
) -> Optional[BangumiTvShow]:
    async with sem:
        raw = await async_http_get_with_cache(
            f"{_SUBJECT_API}/{subject_id}",
            headers={"User-Agent": conf.USER_AGENT},
            cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
            need_cache=cache,
        )
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if data.get("platform") in _EXCLUDED_PLATFORMS:
        return None

    date = _cn_date(data.get("date"))
    if date is None:
        return None

    name = data.get("name") or ""
    name_cn = data.get("name_cn") or ""
    title = trim_title(name_cn or name)
    if not title:
        return None
    origin_title = name if name_cn and name != name_cn else None

    if poster is None:
        poster = _protocol_relative((data.get("images") or {}).get("large"))
    if poster is None:
        return None

    rating = data.get("rating") or {}
    rate = Rate(
        float(rating.get("score") or 0), int(rating.get("total") or 0), "Bangumi"
    )
    return BangumiTvShow(subject_id, title, origin_title, date, poster, rate)


async def crawl_bangumi_index(
    url: str, cache: bool = True, exclude_titles: Optional[List[str]] = None
) -> List[BangumiTvShow]:
    """Fetch one curated index list, completing each entry via the subject API."""
    html = await async_http_get_with_cache(
        url,
        headers={"User-Agent": conf.USER_AGENT},
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        need_cache=cache,
    )
    if html is None:
        return []

    entries = _parse_index_page(html)
    sem = asyncio.Semaphore(_SUBJECT_CONCURRENCY)
    animes = await asyncio.gather(
        *[_fetch_subject(sid, poster, cache, sem) for sid, poster in entries]
    )

    tv_shows: List[BangumiTvShow] = []
    seen_names: set = set()
    for anime in animes:
        if anime is None or not check(anime, exclude_titles or []):
            continue
        titles = anime.get_titles()
        if any(t in seen_names for t in titles):
            continue
        tv_shows.append(anime)
        seen_names.update(titles)
    return tv_shows


async def crawl_bangumi_anime(
    cache: bool = True, exclude_titles: Optional[List[str]] = None
) -> List[BangumiTvShow]:
    """Union of the ranked browser list and every curated index list."""
    browser_shows, *index_lists = await asyncio.gather(
        crawl_bangumi_tv_show_80(cache=cache, exclude_titles=exclude_titles),
        *[
            crawl_bangumi_index(url, cache=cache, exclude_titles=exclude_titles)
            for url in _INDEX_URLS
        ],
    )

    combined = list(browser_shows)
    for index_shows in index_lists:
        combined = combine_tv_show(combined, index_shows)
    return combined


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
