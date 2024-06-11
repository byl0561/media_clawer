import requests
import bs4

from constant import user_agent
from music.models.music import DoubanAlbum, Rate


def crawl_douban_250() -> list[DoubanAlbum]:
    albums = []

    for x in range(10):
        url = 'https://music.douban.com/top250?start=' + str(x * 25)
        res = requests.get(url, headers={
            'User-Agent': user_agent,
        })
        bs = bs4.BeautifulSoup(res.text, 'html.parser')
        bs = bs.find('div', class_="indent")
        for item in bs.find_all('table'):
            title = item.find('div', class_="pl2").find('a').get_text().strip()
            alias = item.find('div', class_="pl2").find('a').find('img').find('span').get_text().strip() if (
                    item.find('div', class_="pl2").find('a').find('img').find('span') is not None) else None
            artist = item.find('div', class_="pl2").find('p', class_="pl").get_text().strip().split(' / ')[0]
            year = int(item.find('div', class_="pl2").find('p', class_="pl").get_text().strip().split(' / ')[1][:4])
            style = item.find('div', class_="pl2").find('p', class_="pl").get_text().strip().split(' / ')[-1]
            poster = item.find('img').get('src').strip()
            score = float(
                item.find('div', class_='star clearfix').find('span', class_='rating_nums').get_text().strip())
            votes = int(
                item.find('div', class_='star clearfix').find('span', class_='pl').get_text().replace('人评价',
                                                                                                      '').replace('(',
                                                                                                                  '').replace(
                    ')', '').strip())
            albums.append(DoubanAlbum(title, alias, artist, year, style, poster, Rate(score, votes, '豆瓣音乐')))

    return albums
