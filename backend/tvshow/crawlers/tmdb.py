"""TMDB TV show / season lookup. Parsing rules unchanged."""
import json
from datetime import datetime
from typing import Optional

from core import conf
from core.http import http_get_with_cache
from tvshow.models import Rate, TmdbEpisode, TmdbSeason, TmdbTvShow


def get_tmdb_tv_show(tv_show_id: int, cache: bool = True) -> Optional[TmdbTvShow]:
    url = (
        f"https://api.themoviedb.org/3/tv/{tv_show_id}"
        f"?api_key={conf.TMDB_API_KEY}&language=zh-CN"
    )
    res = http_get_with_cache(
        url,
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        sleep_s=0.2,
        need_cache=cache,
        retry=True,
    )
    if res is None:
        return None

    data = json.loads(res)
    seasons = []
    for s in data["seasons"]:
        season_rate = None
        if s.get("vote_average") is not None:
            season_rate = Rate(s["vote_average"], s.get("vote_count") or 0, "TMDB")
        seasons.append(
            TmdbSeason(
                s["season_number"],
                s["name"],
                s["air_date"],
                [],
                poster=s.get("poster_path"),
                rate=season_rate,
            )
        )
    seasons = sorted(seasons, key=lambda s: s.num)
    return TmdbTvShow(
        data["name"],
        data["original_name"],
        [
            int(
                datetime.strptime(data["first_air_date"], "%Y-%m-%d").year
                if len(data["first_air_date"]) > 0
                else 0
            ),
            int(
                datetime.strptime(data["last_air_date"], "%Y-%m-%d").year
                if len(data["last_air_date"]) > 0
                else 0
            ),
        ],
        data["original_language"],
        data["poster_path"],
        Rate(data["vote_average"], data["vote_count"], "TMDB"),
        data["id"],
        seasons,
    )


def get_tmdb_tv_show_season(
    tv_show_id: int, season_num: int, cache: bool = True
) -> Optional[TmdbSeason]:
    url = (
        f"https://api.themoviedb.org/3/tv/{tv_show_id}/season/{season_num}"
        f"?api_key={conf.TMDB_API_KEY}&language=zh-CN"
    )
    res = http_get_with_cache(
        url,
        cache_ttl_m=conf.SOURCE_CACHE_TTL_MINUTES,
        sleep_s=0.2,
        need_cache=cache,
        retry=True,
    )
    if res is None:
        return None

    data = json.loads(res)
    episodes = [
        TmdbEpisode(e["episode_number"], e["name"], e["air_date"], e["runtime"])
        for e in data["episodes"]
    ]
    episodes = sorted(episodes, key=lambda e: e.num)
    return TmdbSeason(season_num, data["name"], data["air_date"], episodes)
