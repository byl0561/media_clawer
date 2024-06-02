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


def find_lost_local_episode(request):
    local_tv_shows = crawl_local(tv_folder)
    missing = {}

    for local_tv_show in local_tv_shows:
        season_2_max_episode = local_tv_show.map_season_max_episode()

        missing_seasons = []
        for season_num, max_episode in season_2_max_episode.items():
            time.sleep(0.2)
            tmdb_tv_show_season = get_tmdb_tv_show_season(local_tv_show.tmdb_id, season_num)
            if tmdb_tv_show_season.get_max_episode_num() <= max_episode:
                continue

            missing_max_episode = -1
            for tmdb_episode in tmdb_tv_show_season.list_episodes():
                if tmdb_episode.num > max_episode and legal_episode(tmdb_episode):
                    missing_max_episode = max(missing_max_episode, tmdb_episode.num)

            if missing_max_episode > max_episode:
                missing_seasons.append({
                    'season_num': season_num,
                    'season_name': tmdb_tv_show_season.name,
                    'local_max_episode': max_episode,
                    'remote_max_episode': missing_max_episode,
                })

        if len(missing_seasons) > 0:
            missing[local_tv_show.get_titles()[0]] = missing_seasons

    return JsonResponse(missing)


def legal_episode(episode: TmdbEpisode) -> bool:
    date_str = episode.get_date()
    if date_str is None or len(date_str) == 0:
        return False

    timestamp = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.today()
    return timestamp < today


def diff_bangumi_tv_anime_100(request):
    # douban_100_tv_show_all = crawl_dou_list('https://www.douban.com/doulist/116238969/')
    # douban_100_tv_show_2014_2024 = crawl_dou_list('https://www.douban.com/doulist/113919174/')
    # douban_tv_shows = combine_tv_show(douban_100_tv_show_all, douban_100_tv_show_2014_2024)
    local_animates = crawl_local(tv_folder)

    # missing_tv_shows = get_missing_tv_shows(douban_tv_shows, local_tv_shows)
    # extra_tv_shows = get_missing_tv_shows(local_tv_shows, douban_tv_shows)

    return JsonResponse([local_anime.to_dict() for local_anime in local_animates], safe=False)
