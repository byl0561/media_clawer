"""Bangumi anime ranking scraper. Parsing/curation rules unchanged."""
import re
from datetime import datetime

import bs4

from core import conf
from core.http import http_get_with_cache
from tvshow.models import BangumiTvShow, Rate


_MAX_PAGES = 30
_MAX_CONSECUTIVE_FAILURES = 5


def crawl_bangumi_tv_show_80(cache: bool = True) -> list:
    """Scrape the Bangumi anime rank pages until we collect 80 entries.

    Stops on three conditions to avoid the runaway-loop case that used to
    drive page numbers into the hundreds when Bangumi's TLS flapped:

    1. 80 anime collected (the original happy path);
    2. ``_MAX_PAGES`` hit — if the curation filters reject too much we'd
       otherwise scan indefinitely;
    3. ``_MAX_CONSECUTIVE_FAILURES`` upstream errors in a row — when
       Bangumi is down, retrying every page just floods their server
       and our logs.
    """
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
            if duplicated or not check(anime):
                continue

            tv_shows.append(anime)
            tv_show_names = tv_show_names.union(set(titles))

    return tv_shows


def check_max_size(tv_shows: list) -> bool:
    return len(tv_shows) > 80


def check(anime: BangumiTvShow) -> bool:
    if anime.get_years()[0] < 2009:
        return False

    delta = datetime.today() - datetime.strptime(anime.get_date(), "%Y年%m月%d日")
    if delta.days <= 90:
        return False

    if anime.get_rate().votes < 2000:
        return False

    long_shows = ["死神", "银魂", "航海王"]
    for title in anime.get_titles():
        if get_main_title(title) in long_shows:
            return False

    return True


def get_main_title(title: str) -> str:
    if not title:
        return ""
    index = title.find("：")
    if index == -1:
        return title
    return title[:index]


def trim_title(title):
    if title is None:
        return None

    replace_titles = {
        "物语": "物语系列",
        "BanG": "BanG Dream! It's MyGO!!!!!",
        "辉夜大小姐想让我告白": "辉夜大小姐想让我告白",
        "爆漫王": "爆漫王",
        "GIRLS": "GIRLS BAND CRY",
        "86": "86-不存在的战区-",
        "NOMAD": "MEGALO BOX",
        "MEGALO": "MEGALO BOX",
        "为美好的世界献上祝福！": "为美好的世界献上祝福！",
        "寄生兽": "寄生兽：生命的准则",
        "钢之炼金术师": "钢之炼金术师 FULLMETAL ALCHEMIST",
        "少女☆歌剧": "少女☆歌剧 Revue Starlight",
        "TIGER": "TIGER & BUNNY",
    }
    for key, value in replace_titles.items():
        if key in title:
            return value

    for remove_str in ["'", "°"]:
        title = title.replace(remove_str, "")
    return title.rstrip("0123456789")
