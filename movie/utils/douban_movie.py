
import requests
import bs4
import re
from movie.models.movie import DoubanMovie, Rate


def crawl_douban_250() -> list[DoubanMovie]:
    movies = []

    for x in range(10):
        url = 'https://movie.douban.com/top250?start=' + str(x * 25) + '&filter='
        res = requests.get(url, headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66'
        })
        bs = bs4.BeautifulSoup(res.text, 'html.parser')
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
            movies.append(DoubanMovie(title, alias, year, country, style, poster, Rate(score, votes)))

    return movies