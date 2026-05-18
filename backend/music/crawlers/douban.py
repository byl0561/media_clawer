"""Douban Top 250 album scraper. Parsing rules unchanged."""
import bs4

from core import conf
from core.http import http_get_with_cache
from music.models import DoubanAlbum, Rate


def crawl_douban_250(cache: bool = True) -> list:
    albums = []

    for x in range(10):
        url = "https://music.douban.com/top250?start=" + str(x * 25)
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
