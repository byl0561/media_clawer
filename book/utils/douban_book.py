import re
import bs4
import utils.request_utils as request_utils

from constant import user_agent
from book.models.book import DoubanBook, Rate


def crawl_douban_250(cache=True) -> list[DoubanBook]:
    books = []

    for x in range(10):
        url = 'https://book.douban.com/top250?start=' + str(x * 25)
        res = request_utils.http_get_with_cache(url, headers={
            'User-Agent': user_agent,
        }, cache_ttl_m=60 * 24 * 7, sleep_s=0, need_cache=cache)
        if res is None:
            continue

        bs = bs4.BeautifulSoup(res, 'html.parser')
        bs = bs.find('div', class_="indent")
        for item in bs.find_all('table'):
            title = item.find('div', class_="pl2").find('a').contents[0].strip()
            link = item.find('div', class_="pl2").find('a').attrs['href']
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

            book = DoubanBook(title, alias, author, year, poster, link, Rate(score, votes, '豆瓣图书'))
            if not check(book):
                continue
            books.append(book)

    return books


def check(book: DoubanBook) -> bool:
    young_books = ['中国少年儿童百科全书', '十万个为什么']
    for title in book.get_titles():
        if title in young_books:
            return False
    return True
