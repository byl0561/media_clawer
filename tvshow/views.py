from django.http import JsonResponse

from constant import tv_folder
from tvshow.utils.douban_tv_show import *
from tvshow.utils.local_tv_show import *


def diff_douban_tv_show_100(request):
    #douban_100_tv_show = crawl_dou_list('https://www.douban.com/doulist/116238969/')
    local_tv_show = crawl_local(tv_folder)

    return JsonResponse({
        'missing_tv_show': [missing_show.to_dict() for missing_show in local_tv_show],
    })
