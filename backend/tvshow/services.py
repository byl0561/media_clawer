"""TV/anime diff use-cases — fully async."""
import asyncio
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Tuple

from core import conf
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.local_config import (
    add_aliases,
    read_config,
    read_root_excludes,
    set_season_checked,
    set_season_subtitle_checked,
)
from core.matching import drop_excluded
from core.media_probe import async_has_subtitle
from tvshow.crawlers.bangumi import crawl_bangumi_tv_show_80
from tvshow.crawlers.douban import crawl_dou_list
from tvshow.crawlers.local import crawl_local, process_file
from tvshow.crawlers.tmdb import get_tmdb_tv_show, get_tmdb_tv_show_season
from tvshow.matching import combine_tv_show, get_missing_tv_shows
from tvshow.models import TvShow

_DOULIST_ALL = "https://www.douban.com/doulist/116238969/"
_DOULIST_RECENT = "https://www.douban.com/doulist/113919174/"

_LIBRARY_ROOT = {"tv": conf.TV_ROOT, "anime": conf.ANIME_ROOT}

_ANIME_DEFAULT_EXCLUDES = ["死神", "银魂", "航海王", "瑞克和莫蒂"]


def _anime_excludes() -> List[str]:
    return _ANIME_DEFAULT_EXCLUDES + read_root_excludes(conf.ANIME_ROOT)


def _is_retained_tv_show(tv_show: TvShow) -> bool:
    rate = tv_show.get_rate()
    return rate.score > 7.5 and rate.votes > 200


def _is_retained_anime(tv_show: TvShow) -> bool:
    rate = tv_show.get_rate()
    return rate.score > 7.5 and rate.votes > 300


async def _enrich_local_shows(
    shows: list,
    sink=None,
    pct_start: int = 0,
    pct_end: int = 100,
) -> None:
    sem = asyncio.Semaphore(5)
    total = len(shows)
    done = 0

    async def enrich_one(show):
        nonlocal done
        async with sem:
            tmdb_show = await get_tmdb_tv_show(show.tmdb_id)
        if tmdb_show is not None:
            show.tmdb_rate = tmdb_show.get_rate()
        done += 1
        if sink is not None and total > 0:
            pct = pct_start + done * (pct_end - pct_start) // total
            await sink.report(f"正在匹配元数据 {done}/{total}", pct)

    await asyncio.gather(*[enrich_one(s) for s in shows])


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


def _show_to_dict(obj) -> dict:
    titles = obj.get_titles()
    rate = obj.get_rate()
    return {
        "title": titles[0] if titles else "",
        "score": round(rate.score, 1) if rate is not None else None,
        "votes": rate.votes if rate is not None else None,
        "poster": obj.get_poster(),
        "link": obj.get_link(),
        "year": obj.get_years(),
        "tmdb_id": getattr(obj, "tmdb_id", None),
    }


def _shows(tv_shows) -> list:
    return [_show_to_dict(s) for s in tv_shows]


def _diff(source_shows, local_shows, is_retained) -> dict:
    return {
        "missing": _shows(get_missing_tv_shows(source_shows, local_shows)),
        "extra": _shows(
            [s for s in get_missing_tv_shows(local_shows, source_shows) if not is_retained(s)]
        ),
    }


async def tv_diff(sink=None) -> dict:
    if sink:
        await sink.report("正在爬取豆瓣剧集榜单…", 5)
    loop = asyncio.get_running_loop()
    douban_tv_shows_lists = await asyncio.gather(
        crawl_dou_list(_DOULIST_ALL),
        crawl_dou_list(_DOULIST_RECENT),
    )
    douban_tv_shows = combine_tv_show(*douban_tv_shows_lists)
    if not douban_tv_shows:
        raise UpstreamUnavailable()
    douban_tv_shows = drop_excluded(douban_tv_shows, read_root_excludes(conf.TV_ROOT))

    if sink:
        await sink.report("正在扫描本地剧集库…", 35)
    local_shows = await loop.run_in_executor(None, crawl_local, conf.TV_ROOT)
    await _enrich_local_shows(local_shows, sink=sink, pct_start=40, pct_end=90)

    return _diff(douban_tv_shows, local_shows, _is_retained_tv_show)


async def anime_diff(sink=None) -> dict:
    if sink:
        await sink.report("正在爬取 Bangumi 动漫榜单…", 5)
    loop = asyncio.get_running_loop()
    bangumi_shows = await crawl_bangumi_tv_show_80(exclude_titles=_anime_excludes())
    if not bangumi_shows:
        raise UpstreamUnavailable()

    if sink:
        await sink.report("正在扫描本地动漫库…", 35)
    local_shows = await loop.run_in_executor(None, crawl_local, conf.ANIME_ROOT)
    await _enrich_local_shows(local_shows, sink=sink, pct_start=40, pct_end=90)

    return _diff(bangumi_shows, local_shows, _is_retained_anime)


def _season_ref(season) -> dict:
    rate = getattr(season, "rate", None)
    return {
        "num": season.num,
        "name": season.name,
        "poster": getattr(season, "poster", None),
        "score": round(rate.score, 1) if rate is not None and rate.score > 0 else None,
    }


async def series_gaps(library: str, sink=None) -> list:
    if sink:
        await sink.report("正在扫描本地剧集库…", 5)
    loop = asyncio.get_running_loop()
    local_shows = await loop.run_in_executor(None, crawl_local, _LIBRARY_ROOT[library])

    sem = asyncio.Semaphore(5)
    total = len(local_shows)
    done = 0

    async def process_show(local_tv_show):
        nonlocal done
        async with sem:
            tmdb_tv_show = await get_tmdb_tv_show(local_tv_show.tmdb_id)

        result = None
        if tmdb_tv_show is not None:
            tmdb_seasons_by_num = {s.num: s for s in tmdb_tv_show.list_seasons()}

            missing_seasons = [
                _season_ref(s)
                for s in tmdb_tv_show.list_seasons()
                if local_tv_show.get_season(s.num) is None and _legal_season(s)
            ]

            season_episode_map = local_tv_show.map_season_episodes()

            async def check_incomplete(season_num, present_eps):
                async with sem:
                    tmdb_season = await get_tmdb_tv_show_season(
                        local_tv_show.tmdb_id, season_num
                    )
                if tmdb_season is None:
                    return None
                aired_missing = [
                    e.num
                    for e in tmdb_season.list_episodes()
                    if e.num not in present_eps and _legal_episode(e)
                ]
                if not aired_missing:
                    return None
                return {
                    "season_num": season_num,
                    "season_name": tmdb_season.name,
                    "local_max_episode": max(present_eps) if present_eps else 0,
                    "remote_max_episode": max(aired_missing),
                    "missing_count": len(aired_missing),
                }

            incomplete_results = await asyncio.gather(*[
                check_incomplete(num, eps) for num, eps in season_episode_map.items()
            ])
            incomplete_seasons = [r for r in incomplete_results if r is not None]

            if missing_seasons or incomplete_seasons:
                local_seasons = []
                for num in sorted(local_tv_show.seasons.keys()):
                    tmdb_season = tmdb_seasons_by_num.get(num)
                    if tmdb_season is None:
                        continue
                    local_seasons.append(_season_ref(tmdb_season))

                result = {
                    "show": _show_to_dict(tmdb_tv_show),
                    "local_seasons": local_seasons,
                    "missing_seasons": missing_seasons,
                    "incomplete_seasons": incomplete_seasons,
                }

        done += 1
        if sink is not None and total > 0:
            pct = 8 + done * 87 // total
            await sink.report(f"正在分析续集 {done}/{total}", pct)
        return result

    results = await asyncio.gather(*[process_show(s) for s in local_shows])
    return [r for r in results if r is not None]


async def _flush_tmdb(root: str) -> None:
    loop = asyncio.get_running_loop()
    local_shows = await loop.run_in_executor(None, crawl_local, root)
    sem = asyncio.Semaphore(5)

    async def flush_show(show):
        async with sem:
            await get_tmdb_tv_show(show.tmdb_id, cache=False)
        season_nums = list(show.map_season_max_episode().keys())

        async def flush_season(num):
            async with sem:
                await get_tmdb_tv_show_season(show.tmdb_id, num, cache=False)

        await asyncio.gather(*[flush_season(n) for n in season_nums])

    await asyncio.gather(*[flush_show(s) for s in local_shows])


async def refresh_all() -> None:
    """Repopulate the upstream Douban / Bangumi / TMDB caches (used by cron)."""
    await asyncio.gather(
        crawl_dou_list(_DOULIST_ALL, cache=False),
        crawl_dou_list(_DOULIST_RECENT, cache=False),
        crawl_bangumi_tv_show_80(cache=False, exclude_titles=_anime_excludes()),
    )
    await asyncio.gather(
        _flush_tmdb(conf.TV_ROOT),
        _flush_tmdb(conf.ANIME_ROOT),
    )


def _find_show_dir(root: str, tmdb_id: int) -> Optional[str]:
    base = os.path.realpath(root)
    if not os.path.isdir(base):
        return None
    for current, _dirs, files in os.walk(base):
        if "tvshow.nfo" not in files:
            continue
        try:
            tree = ET.parse(os.path.join(current, "tvshow.nfo"))
            node = tree.getroot().find("./uniqueid[@type='tmdb']")
            if node is not None and node.text and int(node.text) == tmdb_id:
                return current
        except (ET.ParseError, ValueError, TypeError):
            continue
    return None


async def _gap_seasons(library: str, tmdb_id: int) -> Tuple[Optional[str], str, list]:
    root = _LIBRARY_ROOT[library]
    show_dir = _find_show_dir(root, tmdb_id)
    if show_dir is None:
        return None, "", []

    try:
        local_tv_show = process_file(os.path.join(show_dir, "tvshow.nfo"))
    except (ET.ParseError, ValueError, TypeError, AttributeError):
        local_tv_show = None

    tmdb_tv_show = await get_tmdb_tv_show(tmdb_id)
    if local_tv_show is None or tmdb_tv_show is None:
        return show_dir, "", []

    present_per_season = local_tv_show.map_season_episodes()
    candidates = set(present_per_season)
    list_seasons_by_num = {s.num: s for s in tmdb_tv_show.list_seasons()}
    for tmdb_season in tmdb_tv_show.list_seasons():
        if local_tv_show.get_season(tmdb_season.num) is None and _legal_season(tmdb_season):
            candidates.add(tmdb_season.num)

    async def get_season_detail(num):
        return num, await get_tmdb_tv_show_season(tmdb_id, num)

    season_detail_pairs = await asyncio.gather(*[get_season_detail(n) for n in sorted(candidates)])
    season_details = dict(season_detail_pairs)

    seasons = []
    for num in sorted(candidates):
        present_eps = present_per_season.get(num, set())
        local_max = max(present_eps) if present_eps else 0
        detail = season_details.get(num)

        aired = (
            [
                e
                for e in detail.list_episodes()
                if e.num not in present_eps and _legal_episode(e)
            ]
            if detail is not None
            else []
        )
        if aired:
            seasons.append(
                {
                    "season_num": num,
                    "season_name": detail.name,
                    "local_max_episode": local_max,
                    "latest_episode": max(e.num for e in aired),
                    "episodes": [
                        {"num": e.num, "name": e.name, "date": e.get_date() or None}
                        for e in aired
                    ],
                }
            )
            continue

        synth_max = 0
        if detail is not None:
            synth_max = max((e.num for e in detail.list_episodes()), default=0)
        list_season = list_seasons_by_num.get(num)
        if synth_max <= 0 and list_season is not None:
            synth_max = list_season.episode_count
        if synth_max <= local_max:
            continue
        seasons.append(
            {
                "season_num": num,
                "season_name": (detail or list_season).name,
                "local_max_episode": local_max,
                "latest_episode": synth_max,
                "episodes": [{"num": synth_max, "name": "整季", "date": None}],
            }
        )
    return show_dir, tmdb_tv_show.get_titles()[0], seasons


async def ignore_options(library: str, tmdb_id: int) -> dict:
    show_dir, title, seasons = await _gap_seasons(library, tmdb_id)
    if show_dir is None:
        raise ShowNotFound()
    return {"title": title, "seasons": seasons}


async def ignore_apply(library: str, tmdb_id: int, selections: list) -> dict:
    show_dir, _title, gap_seasons = await _gap_seasons(library, tmdb_id)
    if show_dir is None:
        raise ShowNotFound()

    chosen = {int(s["season_num"]): int(s["episode"]) for s in selections}
    fully_ignored = bool(gap_seasons) and all(
        g["season_num"] in chosen and chosen[g["season_num"]] >= g["latest_episode"]
        for g in gap_seasons
    )

    for season_num, episode in chosen.items():
        if episode < 0:
            continue
        set_season_checked(show_dir, season_num, episode)

    return {"fully_ignored": fully_ignored}


def _read_subtitle_cutoffs(folder: str) -> dict:
    cfg = read_config(folder) if folder else {}
    out: dict = {}
    for k, v in (cfg.get("seasons") or {}).items():
        try:
            num = int(k)
        except (TypeError, ValueError):
            continue
        if not isinstance(v, dict):
            continue
        cutoff = v.get("subtitle_checked_episode")
        if isinstance(cutoff, int):
            out[num] = cutoff
    return out


async def warm_subtitle_cache() -> None:
    await asyncio.gather(subtitle_gaps("tv"), subtitle_gaps("anime"))


async def subtitle_gaps(library: str, sink=None) -> list:
    if sink:
        await sink.report("正在扫描本地剧集库…", 5)
    loop = asyncio.get_running_loop()
    local_shows = await loop.run_in_executor(None, crawl_local, _LIBRARY_ROOT[library])

    tmdb_sem = asyncio.Semaphore(5)
    ffprobe_sem = asyncio.Semaphore(8)
    total = len(local_shows)
    done = 0

    async def process_show(local_tv_show):
        nonlocal done
        async with tmdb_sem:
            tmdb_tv_show = await get_tmdb_tv_show(local_tv_show.tmdb_id)

        result = None
        if tmdb_tv_show is not None:
            cutoffs = _read_subtitle_cutoffs(local_tv_show.path or "")
            tmdb_seasons_by_num = {s.num: s for s in tmdb_tv_show.list_seasons()}

            async def check_season(num, local_season):
                cutoff = cutoffs.get(num, 0)

                async def check_ep(ep):
                    if ep.num <= cutoff or not ep.video_path:
                        return None
                    if await async_has_subtitle(ep.video_path, ffprobe_sem):
                        return None
                    return ep.num

                missing_eps = [
                    r for r in await asyncio.gather(*[check_ep(ep) for ep in local_season.episodes.values()])
                    if r is not None
                ]
                if not missing_eps:
                    return None
                tmdb_season = tmdb_seasons_by_num.get(num)
                return {
                    "num": num,
                    "name": tmdb_season.name if tmdb_season else f"第 {num} 季",
                    "poster": tmdb_season.poster if tmdb_season else None,
                    "score": (
                        round(tmdb_season.rate.score, 1)
                        if tmdb_season and tmdb_season.rate and tmdb_season.rate.score > 0
                        else None
                    ),
                    "missing_count": len(missing_eps),
                    "max_missing_episode": max(missing_eps),
                }

            season_results = await asyncio.gather(*[
                check_season(num, local_season)
                for num, local_season in local_tv_show.seasons.items()
            ])
            gap_seasons = [s for s in season_results if s is not None]

            for num in local_tv_show.empty_seasons:
                if cutoffs.get(num, 0) > 0:
                    continue
                tmdb_season = tmdb_seasons_by_num.get(num)
                expected = tmdb_season.episode_count if tmdb_season else 0
                gap_seasons.append(
                    {
                        "num": num,
                        "name": tmdb_season.name if tmdb_season else f"第 {num} 季",
                        "poster": tmdb_season.poster if tmdb_season else None,
                        "score": (
                            round(tmdb_season.rate.score, 1)
                            if tmdb_season and tmdb_season.rate and tmdb_season.rate.score > 0
                            else None
                        ),
                        "missing_count": expected,
                        "max_missing_episode": expected,
                    }
                )

            if gap_seasons:
                gap_seasons.sort(key=lambda s: s["num"])
                result = {
                    "show": _show_to_dict(tmdb_tv_show),
                    "seasons": gap_seasons,
                }

        done += 1
        if sink is not None and total > 0:
            pct = 8 + done * 87 // total
            await sink.report(f"正在检测字幕 {done}/{total}", pct)
        return result

    results = await asyncio.gather(*[process_show(s) for s in local_shows])
    return [r for r in results if r is not None]


async def subtitle_ignore_options(library: str, tmdb_id: int) -> dict:
    root = _LIBRARY_ROOT[library]
    show_dir = _find_show_dir(root, tmdb_id)
    if show_dir is None:
        raise ShowNotFound()

    try:
        local_tv_show = process_file(os.path.join(show_dir, "tvshow.nfo"))
    except (ET.ParseError, ValueError, TypeError, AttributeError):
        local_tv_show = None
    tmdb_tv_show = await get_tmdb_tv_show(tmdb_id)
    if local_tv_show is None or tmdb_tv_show is None:
        return {"title": "", "seasons": []}

    cutoffs = _read_subtitle_cutoffs(show_dir)
    tmdb_seasons_by_num = {s.num: s for s in tmdb_tv_show.list_seasons()}
    ffprobe_sem = asyncio.Semaphore(4)

    seasons = []
    for num in sorted(local_tv_show.seasons.keys()):
        local_season = local_tv_show.seasons[num]
        cutoff = cutoffs.get(num, 0)

        async def _ep_missing(ep, _cutoff=cutoff):
            if ep.num <= _cutoff or not ep.video_path:
                return None
            if await async_has_subtitle(ep.video_path, ffprobe_sem):
                return None
            return ep.num

        ep_results = await asyncio.gather(*(_ep_missing(ep) for ep in local_season.episodes.values()))
        missing_eps = sorted(r for r in ep_results if r is not None)
        if not missing_eps:
            continue
        tmdb_season = tmdb_seasons_by_num.get(num)
        episode_entries = []
        for ep_num in missing_eps:
            ep = local_season.episodes.get(ep_num)
            episode_entries.append(
                {
                    "num": ep_num,
                    "name": (ep.name if ep else "") or f"第 {ep_num} 集",
                    "date": (ep.date or None) if ep else None,
                }
            )
        seasons.append(
            {
                "season_num": num,
                "season_name": tmdb_season.name if tmdb_season else f"第 {num} 季",
                "local_max_episode": cutoff,
                "latest_episode": missing_eps[-1],
                "episodes": episode_entries,
            }
        )

    return {"title": tmdb_tv_show.get_titles()[0], "seasons": seasons}


async def subtitle_ignore_apply(library: str, tmdb_id: int, selections: list) -> dict:
    root = _LIBRARY_ROOT[library]
    show_dir = _find_show_dir(root, tmdb_id)
    if show_dir is None:
        raise ShowNotFound()

    chosen = {int(s["season_num"]): int(s["episode"]) for s in selections}
    options = await subtitle_ignore_options(library, tmdb_id)
    fully_ignored = bool(options["seasons"]) and all(
        g["season_num"] in chosen and chosen[g["season_num"]] >= g["latest_episode"]
        for g in options["seasons"]
    )

    for season_num, episode in chosen.items():
        if episode < 0:
            continue
        set_season_subtitle_checked(show_dir, season_num, episode)

    return {"fully_ignored": fully_ignored}


def alias_targets(library: str) -> list:
    targets = []
    for local in crawl_local(_LIBRARY_ROOT[library]):
        targets.append(
            {
                "tmdb_id": local.tmdb_id,
                "title": local.title,
                "year": local.year,
                "poster": local.get_poster(),
            }
        )
    targets.sort(key=lambda x: x["title"] or "")
    return targets


def alias_bind(library: str, tmdb_id: int, aliases: List[str]) -> dict:
    root = _LIBRARY_ROOT[library]
    show_dir = _find_show_dir(root, tmdb_id)
    if show_dir is None:
        raise ShowNotFound()

    base = os.path.realpath(root)
    target = os.path.realpath(show_dir)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()

    added = add_aliases(target, aliases)
    return {"bound": True, "added": added}
