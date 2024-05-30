from django.http import JsonResponse
import time

from tvshow.utils.douban_tv_show import *
from tvshow.utils.local_tv_show import *
from tvshow.utils.tmdb_tv_show import *
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
    return tv_show.get_rate().score > 8.0 and tv_show.get_rate().votes > 50


def find_lost_local_season(request):
    local_tv_shows = crawl_local(tv_folder)
    missing = {}
    for local_tv_show in local_tv_shows:
        time.sleep(0.2)
        tmdb_tv_show = get_tmdb_tv_show(local_tv_show.tmdb_id)
        if tmdb_tv_show is None:
            continue

        missing_seasons = []
        for tmdb_season in tmdb_tv_show.list_seasons():
            if local_tv_show.get_season(tmdb_season.num) is None and legal_season(tmdb_season):
                missing_seasons.append(tmdb_season.to_dict())

        if len(missing_seasons) > 0:
            missing[local_tv_show.get_titles()[0]] = missing_seasons

    return JsonResponse(missing)


def legal_season(season: TmdbSeason) -> bool:
    date_str = season.get_date()
    if date_str is None or len(date_str) == 0:
        return False

    timestamp = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.today()
    delta = today - timestamp
    return delta.days > 90
