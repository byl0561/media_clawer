"""TV/anime diff use-cases (logic moved out of the old ``tvshow.views``).

The diff is recomputed on every request; only the upstream Douban/Bangumi/
TMDB responses stay cached (via :mod:`core.http`), kept warm by cron. ``tv``
and ``anime`` share this module because the anime endpoints have always been
served by this app against the anime library root.

``local_gaps`` merges the old season-missing and episode-missing endpoints:
one local scan + one ``get_tmdb_tv_show`` per show (instead of two passes),
returning both whole-missing seasons and behind-on-episodes seasons.
"""
from datetime import datetime

from core import conf
from core.exceptions import UpstreamUnavailable
from tvshow.crawlers.bangumi import crawl_bangumi_tv_show_80
from tvshow.crawlers.douban import crawl_dou_list
from tvshow.crawlers.local import crawl_local
from tvshow.crawlers.tmdb import get_tmdb_tv_show, get_tmdb_tv_show_season
from tvshow.matching import combine_tv_show, get_missing_tv_shows
from tvshow.models import TvShow
from tvshow.serializers import SeasonSerializer, TvShowSerializer

_DOULIST_ALL = "https://www.douban.com/doulist/116238969/"
_DOULIST_RECENT = "https://www.douban.com/doulist/113919174/"

_LIBRARY_ROOT = {"tv": conf.TV_ROOT, "anime": conf.ANIME_ROOT}


def _is_retained_tv_show(tv_show: TvShow) -> bool:
    rate = tv_show.get_rate()
    return rate.score > 8.0 and rate.votes > 50


def _is_retained_anime(tv_show: TvShow) -> bool:
    rate = tv_show.get_rate()
    return rate.score > 8.5 and rate.votes > 500


def _legal_season(season) -> bool:
    date_str = season.get_date()
    if date_str is None or len(date_str) == 0:
        return False
    delta = datetime.today() - datetime.strptime(date_str, "%Y-%m-%d")
    return delta.days > 90


def _legal_episode(episode) -> bool:
    date_str = episode.get_date()
    if date_str is None or len(date_str) == 0:
        return False
    return datetime.strptime(date_str, "%Y-%m-%d") < datetime.today()


def _shows(tv_shows) -> list:
    return TvShowSerializer(tv_shows, many=True).data


def _diff(source_shows, local_shows, is_retained) -> dict:
    return {
        "missing": _shows(get_missing_tv_shows(source_shows, local_shows)),
        "extra": _shows(
            [s for s in get_missing_tv_shows(local_shows, source_shows) if not is_retained(s)]
        ),
    }


def tv_diff() -> dict:
    douban_tv_shows = combine_tv_show(
        crawl_dou_list(_DOULIST_ALL), crawl_dou_list(_DOULIST_RECENT)
    )
    if not douban_tv_shows:
        raise UpstreamUnavailable()
    return _diff(douban_tv_shows, crawl_local(conf.TV_ROOT), _is_retained_tv_show)


def anime_diff() -> dict:
    bangumi_shows = crawl_bangumi_tv_show_80()
    if not bangumi_shows:
        raise UpstreamUnavailable()
    return _diff(bangumi_shows, crawl_local(conf.ANIME_ROOT), _is_retained_anime)


def local_gaps(library: str) -> list:
    """Local shows that are missing whole seasons and/or behind on episodes.

    -> [{"show": <show>, "missing_seasons": [{num,name}],
         "incomplete_seasons": [{season_num,season_name,
                                 local_max_episode,remote_max_episode}]}]
    """
    result = []
    for local_tv_show in crawl_local(_LIBRARY_ROOT[library]):
        tmdb_tv_show = get_tmdb_tv_show(local_tv_show.tmdb_id)
        if tmdb_tv_show is None:
            continue

        missing_seasons = [
            SeasonSerializer(tmdb_season).data
            for tmdb_season in tmdb_tv_show.list_seasons()
            if local_tv_show.get_season(tmdb_season.num) is None
            and _legal_season(tmdb_season)
        ]

        incomplete_seasons = []
        for season_num, max_episode in local_tv_show.map_season_max_episode().items():
            tmdb_season = get_tmdb_tv_show_season(local_tv_show.tmdb_id, season_num)
            if tmdb_season is None or tmdb_season.get_max_episode_num() <= max_episode:
                continue

            missing_max_episode = -1
            for tmdb_episode in tmdb_season.list_episodes():
                if tmdb_episode.num > max_episode and _legal_episode(tmdb_episode):
                    missing_max_episode = max(missing_max_episode, tmdb_episode.num)

            if missing_max_episode > max_episode:
                incomplete_seasons.append(
                    {
                        "season_num": season_num,
                        "season_name": tmdb_season.name,
                        "local_max_episode": max_episode,
                        "remote_max_episode": missing_max_episode,
                    }
                )

        if missing_seasons or incomplete_seasons:
            result.append(
                {
                    "show": TvShowSerializer(tmdb_tv_show).data,
                    "missing_seasons": missing_seasons,
                    "incomplete_seasons": incomplete_seasons,
                }
            )
    return result


def _flush_tmdb(root: str) -> None:
    for local_tv_show in crawl_local(root):
        get_tmdb_tv_show(local_tv_show.tmdb_id, cache=False)
        for season_num in local_tv_show.map_season_max_episode():
            get_tmdb_tv_show_season(local_tv_show.tmdb_id, season_num, cache=False)


def refresh_all() -> None:
    """Repopulate the upstream Douban / Bangumi / TMDB caches (used by cron)."""
    crawl_dou_list(_DOULIST_ALL, cache=False)
    crawl_dou_list(_DOULIST_RECENT, cache=False)
    crawl_bangumi_tv_show_80(cache=False)
    _flush_tmdb(conf.TV_ROOT)
    _flush_tmdb(conf.ANIME_ROOT)
