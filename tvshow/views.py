from django.http import JsonResponse

from tvshow.utils.douban_tv_show import *


def diff_douban_tv_show_100(request):
    douban_100_tv_show = crawl_dou_list('https://www.douban.com/doulist/116238969/')

    return JsonResponse({
        'missing_tv_show': [missing_show.to_dict() for missing_show in douban_100_tv_show],
    })
