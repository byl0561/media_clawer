import logging
from music.utils.douban_music import crawl_douban_250

logger = logging.getLogger()

def cronjob():
    logger.warning('music cronjob start')
    try:
        crawl_douban_250(cache=False)
        logger.warning('music cronjob succeed')
    except Exception as e:
        logger.error('music cronjob failed')
        logger.error(e)