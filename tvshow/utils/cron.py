from constant import tv_folder, anime_folder
from tvshow.utils.bangumi_tv_show import crawl_bangumi_tv_show_80
from tvshow.utils.douban_tv_show import crawl_dou_list
from tvshow.utils.local_tv_show import crawl_local
from tvshow.utils.tmdb_tv_show import get_tmdb_tv_show, get_tmdb_tv_show_season


def cronjob():
    crawl_dou_list('https://www.douban.com/doulist/116238969/', cache=False)
    crawl_dou_list('https://www.douban.com/doulist/113919174/', cache=False)
    crawl_bangumi_tv_show_80(cache=False)

    flush_tmdb(tv_folder)
    flush_tmdb(anime_folder)


def flush_tmdb(folder):
    local_tv_shows = crawl_local(folder)
    for local_tv_show in local_tv_shows:
        get_tmdb_tv_show(local_tv_show.tmdb_id)

        all_seasons = local_tv_show.map_season_max_episode().keys()
        for season_num in all_seasons:
            get_tmdb_tv_show_season(local_tv_show.tmdb_id, season_num)
