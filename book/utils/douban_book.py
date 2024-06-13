import re

import requests
import bs4

from constant import user_agent
from book.models.book import DoubanBook, Rate


def crawl_douban_250() -> list[DoubanBook]:
    albums = []

    for x in range(10):
        url = 'https://book.douban.com/top250?start=' + str(x * 25)
        res = requests.get(url, headers={
            'User-Agent': user_agent,
        })
        bs = bs4.BeautifulSoup(res.text, 'html.parser')
        bs = bs.find('div', class_="indent")
        for item in bs.find_all('table'):
            title = item.find('div', class_="pl2").find('a').contents[0].strip()
            alias = item.find('div', class_="pl2").find('a').find('span').get_text().replace(':', '').strip() if (
                    item.find('div', class_="pl2").find('a').find('span') is not None) else None
            author = item.find('p', class_="pl").get_text().strip().split(' / ')[0]
            author = re.sub(r'\[[^]]*]', '', author)
            author = re.sub(r'\([^]]*\)', '', author)
            author = re.sub(r'（[^]]*）', '', author)
            author = re.sub(r'【[^]]*】', '', author)
            noises = ['文', '主编', '著', '编订', '口述']
            for noise in noises:
                author = author.replace(' ' + noise, '').strip()
            author = author.strip()
            year = int(item.find('p', class_="pl").get_text().strip().split(' / ')[-2][:4])
            poster = item.find('img').get('src').strip()
            score = float(
                item.find('div', class_='star clearfix').find('span', class_='rating_nums').get_text().strip())
            votes = int(
                item.find('div', class_='star clearfix').find('span', class_='pl').get_text().replace('人评价',
                                                                                                      '').replace('(',
                                                                                                                  '').replace(
                    ')', '').strip())
            albums.append(DoubanBook(title, alias, author, year,poster, Rate(score, votes, '豆瓣图书')))

    return albums
