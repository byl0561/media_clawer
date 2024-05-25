from django.http import JsonResponse

from constant import tv_folder
from tvshow.utils.douban_tv_show import *
from tvshow.utils.local_tv_show import *
from tvshow.utils.common import *


def diff_douban_tv_show_100(request):
    douban_100_tv_show_all = crawl_dou_list('https://www.douban.com/doulist/116238969/')
    douban_100_tv_show_2014_2024 = crawl_dou_list('https://www.douban.com/doulist/113919174/')
    douban_tv_shows = combine_tv_show(douban_100_tv_show_all, douban_100_tv_show_2014_2024)
    local_tv_shows = crawl_local(tv_folder)

    missing_tv_shows = get_missing_tv_shows(douban_tv_shows, local_tv_shows)
    extra_tv_shows = get_missing_tv_shows(local_tv_shows, douban_tv_shows)

    return JsonResponse({
        'missing_tv_show': [missing_show.to_dict() for missing_show in missing_tv_shows],
        'extra_tv_shows': [extra_show.to_dict() for extra_show in extra_tv_shows
                           if not is_retained(extra_show)],
    })


def is_retained(tv_show: TvShow) -> bool:
    return False
    # return movie.get_rate().score > 7.5 and movie.get_rate().votes > 500