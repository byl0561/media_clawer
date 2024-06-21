import bs4
import re
import utils.request_utils as request_utils

from constant import user_agent
from movie.models.movie import DoubanMovie, Rate


def crawl_douban_250() -> list[DoubanMovie]:
    movies = []

    for x in range(10):
        url = 'https://movie.douban.com/top250?start=' + str(x * 25) + '&filter='
        res = request_utils.http_get_with_cache(url, headers={
            'User-Agent': user_agent,
        }, cache_ttl_m=60 * 24 * 7, sleep_s=0)
        if res is None:
            continue

        bs = bs4.BeautifulSoup(res, 'html.parser')
        bs = bs.find('ol', class_="grid_view")
        for item in bs.find_all('li'):
            title = []
            for t1 in item.find_all('span', class_='title'):
                for t2 in t1.get_text().split('/'):
                    t2 = t2.strip()
                    if len(t2) > 0:
                        title.append(t2)
            alias = []
            for al in item.find('span', class_='other').get_text().split('/'):
                al = al.strip()
                if len(al) > 0:
                    alias.append(al)
            year_country_style = item.find('div', class_='bd').find('p', class_='').get_text().strip().split('\n')[
                1].replace('"', '').split('/')
            year = int(re.sub(r'\([^)]*\)', '', year_country_style[0].strip()))
            country = year_country_style[1].strip().split(' ')
            style = year_country_style[2].strip().split(' ')
            poster = item.find('div', class_='pic').find('img').get('src').strip()
            score = float(item.find('span', class_='rating_num').get_text().strip())
            votes = int(
                item.find('div', class_='star').select_one('span:last-child').get_text().replace('人评价', '').strip())
            movies.append(DoubanMovie(title, alias, year, country, style, poster, Rate(score, votes, '豆瓣电影')))

    return movies