import logging
from book.utils.douban_book import crawl_douban_250

logger = logging.getLogger()

def cronjob():
    logger.warning('book cronjob start')
    try:
        crawl_douban_250(cache=False)
        logger.warning('book cronjob succeed')
    except Exception as e:
        logger.error('book cronjob failed')
        logger.error(e)
