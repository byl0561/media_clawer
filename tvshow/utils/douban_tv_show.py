from constant import user_agent, douban_cookie
from tvshow.models.tvshow import DoubanTvShow, Rate
import requests
import bs4


def crawl_dou_list(url: str) -> list[DoubanTvShow]:
    tv_shows = []

    for x in range(get_dou_list_total_page(url)):
        page_url = url + '?start=' + str(x * 25) + '&sort=seq&playable=0&sub_type='
        cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in douban_cookie.split('; ')}
        res = requests.get(page_url, cookies=cookies, headers={
            'User-Agent': user_agent,
        })
        bs = bs4.BeautifulSoup(res.text, 'html.parser')
        bs = bs.find('div', class_="article")
        for item in bs.find_all('div', class_="doulist-item"):
            title = item.find('div', class_="title").get_text().strip().split(' ')[0]
            abstract = item.find('div', class_="abstract").get_text().strip().split('\n')
            year = int(abstract[8].replace('年份:', '').strip())
            country = abstract[6].replace('制片国家/地区:', '').strip()
            style = abstract[4].replace('类型:', '').strip().split(' / ')
            poster = item.find('div', class_='post').find('img').get('src').strip()
            score = float(item.find('span', class_='rating_nums').get_text().strip())
            votes = int(
                item.find('div', class_='rating').select_one('span:last-child').get_text()
                .replace('人评价)', '').replace('(', '').strip())
            tv_shows.append(DoubanTvShow(title, year, country, style, poster, Rate(score, votes, '豆瓣')))

    return tv_shows


def get_dou_list_total_page(url: str) -> int:
    res = requests.get(url, headers={
        'User-Agent': user_agent,
    })
    bs = bs4.BeautifulSoup(res.text, 'html.parser')
    paginator = bs.find('div', class_='paginator')
    page_numbers = paginator.find_all('a')
    max_number = 1
    for page_number in page_numbers:
        number = page_number.get_text().strip()
        if number.isdigit():
            max_number = int(number) if max_number < int(number) else max_number
    return max_number
