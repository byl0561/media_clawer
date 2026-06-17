"""Bangumi anime ranking scraper. Parsing/curation rules unchanged."""
import re
from datetime import datetime

import bs4

from core import conf
from core.http import http_get_with_cache
from core.matching import title_excluded
from tvshow.models import BangumiTvShow, Rate


_MAX_PAGES = 30
_MAX_CONSECUTIVE_FAILURES = 5


def crawl_bangumi_tv_show_80(cache: bool = True, exclude_titles=None) -> list:
    """Scrape the Bangumi anime rank pages until we collect 80 entries.

    ``exclude_titles`` is the caller-supplied ignore list (built-in long-show
    defaults + ``<ANIME_ROOT>/.mediaclawer.json``); matching anime are skipped
    *during* collection so they don't eat slots in the 80-entry budget.

    Stops on three conditions to avoid the runaway-loop case that used to
    drive page numbers into the hundreds when Bangumi's TLS flapped:

    1. 80 anime collected (the original happy path);
    2. ``_MAX_PAGES`` hit — if the curation filters reject too much we'd
       otherwise scan indefinitely;
    3. ``_MAX_CONSECUTIVE_FAILURES`` upstream errors in a row — when
       Bangumi is down, retrying every page just floods their server
       and our logs.
    """
    excludes = exclude_titles or []
    tv_shows = []
    tv_show_names = set()

    page = 0
    failures = 0
    while not check_max_size(tv_shows) and page < _MAX_PAGES:
        page += 1
        url = "https://bangumi.tv/anime/browser/tv/?sort=rank&page=" + str(page)
        res = http_get_with_cache(
            url,
            headers={"User-Agent": conf.USER_AGENT},
            cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
            sleep_s=0,
            need_cache=cache,
        )
        if res is None:
            failures += 1
            if failures >= _MAX_CONSECUTIVE_FAILURES:
                break
            continue
        failures = 0

        bs = bs4.BeautifulSoup(res, "html.parser")
        bs = bs.find("ul", class_="browserFull")
        for item in bs.find_all("li", class_="item"):
            if check_max_size(tv_shows):
                break

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
                item.find("small", class_="grey").get_text().strip().split(" ")[
                    title_index
                ]
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

            titles = anime.get_titles()
            duplicated = any(t in tv_show_names for t in titles)
            if duplicated or not check(anime, excludes):
                continue

            tv_shows.append(anime)
            tv_show_names = tv_show_names.union(set(titles))

    return tv_shows


def check_max_size(tv_shows: list) -> bool:
    return len(tv_shows) > 80


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
    """Generic normalisation of a scraped Bangumi rank title.

    Only library-agnostic cleanup lives here now: strip stray ``'`` / ``°`` and
    a trailing season number (``进击的巨人3`` -> ``进击的巨人``) so the fuzzy
    matcher sees a stable stem.

    Per-title canonicalisation (the old hand-maintained ``物语`` -> ``物语系列``
    style map) is intentionally gone — bind the truncated rank title as an
    ``aliases`` entry on the owned show's ``.mediaclawer.json`` (UI: the bind
    dialog) instead, which does the same job without a redeploy.
    """
    if title is None:
        return None

    for remove_str in ["'", "°"]:
        title = title.replace(remove_str, "")
    return title.rstrip("0123456789")
