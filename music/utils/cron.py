from music.utils.douban_music import crawl_douban_250


def cronjob():
    crawl_douban_250(cache=False)
