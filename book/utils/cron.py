from book.utils.douban_book import crawl_douban_250


def cronjob():
    crawl_douban_250(cache=False)
