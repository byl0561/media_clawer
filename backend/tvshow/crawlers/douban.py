"""Douban doulist scraper. Parsing rules unchanged (incl. robust cookie parse)."""
import bs4

from core import conf
from core.http import http_get_with_cache
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


def crawl_dou_list(url: str, cache: bool = True) -> list:
    tv_shows = []

    cookies = parse_cookie(conf.DOUBAN_COOKIE)
    for x in range(get_dou_list_total_page(url, cache=cache)):
        page_url = url + "?start=" + str(x * 25) + "&sort=seq&playable=0&sub_type="
        res = http_get_with_cache(
            page_url,
            cookies=cookies,
            headers={"User-Agent": conf.USER_AGENT},
            cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
            sleep_s=0,
            need_cache=cache,
        )
        if res is None:
            continue

        bs = bs4.BeautifulSoup(res, "html.parser")
        bs = bs.find("div", class_="article")
        for item in bs.find_all("div", class_="doulist-item"):
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
                DoubanTvShow(
                    title, year, country, style, poster, link, Rate(score, votes, "豆瓣")
                )
            )

    return tv_shows


def get_dou_list_total_page(url: str, cache: bool = True) -> int:
    res = http_get_with_cache(
        url,
        headers={"User-Agent": conf.USER_AGENT},
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        sleep_s=0,
        need_cache=cache,
    )
    if res is None:
        return 0

    bs = bs4.BeautifulSoup(res, "html.parser")
    paginator = bs.find("div", class_="paginator")
    max_number = 1
    for page_number in paginator.find_all("a"):
        number = page_number.get_text().strip()
        if number.isdigit():
            max_number = max(max_number, int(number))
    return max_number
