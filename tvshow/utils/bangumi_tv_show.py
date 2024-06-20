import re
from datetime import datetime

import utils
from constant import user_agent
from tvshow.models.tvshow import BangumiTvShow, Rate
import requests
import bs4


def crawl_bangumi_tv_show_80() -> list[BangumiTvShow]:
    tv_shows = []
    tv_show_names = set()

    page = 0
    while True:
        if check_max_size(tv_shows):
            break
        page += 1
        url = 'https://bangumi.tv/anime/browser/tv/?sort=rank&page=' + str(page)
        res = utils.http_get_with_cache(url, headers={
            'User-Agent': user_agent,
        }, cache_ttl_m=60 * 24 * 7, sleep_s=0)
        if res is None:
            continue

        bs = bs4.BeautifulSoup(res, 'html.parser')
        bs = bs.find('ul', class_="browserFull")
        for item in bs.find_all('li', class_="item"):
            if check_max_size(tv_shows):
                break

            title_index = 0
            title_split_strs = item.find('a', class_="l").get_text().strip().split(' ')
            for index, title_split_str in enumerate(title_split_strs):
                if len(title_split_str) > 1:
                    title_index = index
                    break

            title = item.find('a', class_="l").get_text().strip().split(' ')[title_index]
            title = trim_title(title)
            origin_title = item.find('small', class_="grey").get_text().strip().split(' ')[title_index] if item.find('small', class_="grey") is not None else None
            match = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', item.find('p', class_="info tip").get_text().strip())
            if match is None:
                continue
            date = match.group()
            poster = item.find('span', class_="image").find('img').get('src').strip()
            score = float(item.find('p', class_="rateInfo").find('small', class_='fade').get_text().strip())
            votes = int(item.find('p', class_="rateInfo").find('span', class_='tip_j').get_text().replace('人评分)',
                                                                                                          '').replace(
                '(', '').strip())
            anime = BangumiTvShow(title, origin_title, date, poster, Rate(score, votes, 'Bangumi'))

            titles = anime.get_titles()
            duplicated = False
            for title in titles:
                if title in tv_show_names:
                    duplicated = True

            if duplicated or not check(anime):
                continue

            tv_shows.append(anime)
            tv_show_names = tv_show_names.union(set(titles))

    return tv_shows


def check_max_size(tv_shows: list[BangumiTvShow]) -> bool:
    return len(tv_shows) > 80


def check(anime: BangumiTvShow) -> bool:
    if anime.get_years()[0] < 2009:
        return False

    timestamp = datetime.strptime(anime.get_date(), "%Y年%m月%d日")
    today = datetime.today()
    delta = today - timestamp
    if delta.days <= 90:
        return False

    rate = anime.get_rate()
    if rate.votes < 2000:
        return False

    long_shows = ['死神', '银魂']
    for title in anime.get_titles():
        if title in long_shows:
            return False

    return True


def trim_title(title: str or None) -> str or None:
    if title is None:
        return None

    replace_titles = {
        '物语': '物语系列',
        'BanG': "BanG Dream! It's MyGO!!!!!",
        '辉夜大小姐想让我告白': '辉夜大小姐想让我告白',
        '爆漫王': '爆漫王',
        'GIRLS': 'GIRLS BAND CRY',
        '86': '86-不存在的战区-',
        'NOMAD': 'MEGALO BOX',
        'MEGALO': 'MEGALO BOX',
        '为美好的世界献上祝福！': '为美好的世界献上祝福！',
        '寄生兽': '寄生兽：生命的准则',
        '钢之炼金术师': '钢之炼金术师 FULLMETAL ALCHEMIST',
        '少女☆歌剧': '少女☆歌剧 Revue Starlight',
        'TIGER': 'TIGER & BUNNY',
    }
    for key, value in replace_titles.items():
        if key in title:
            title = value
            return title

    remove_strs = ["'", '°']
    for remove_str in remove_strs:
        title = title.replace(remove_str, '')
    title = title.rstrip('0123456789')
    return title