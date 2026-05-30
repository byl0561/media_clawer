"""TV/anime diff use-cases (logic moved out of the old ``tvshow.views``).

The diff is recomputed on every request; only the upstream Douban/Bangumi/
TMDB responses stay cached (via :mod:`core.http`), kept warm by cron. ``tv``
and ``anime`` share this module because the anime endpoints have always been
served by this app against the anime library root.

``local_gaps`` merges the old season-missing and episode-missing endpoints:
one local scan + one ``get_tmdb_tv_show`` per show (instead of two passes),
returning both whole-missing seasons and behind-on-episodes seasons.
"""
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Tuple

from core import conf
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.local_config import add_aliases, set_season_checked
from tvshow.crawlers.bangumi import crawl_bangumi_tv_show_80
from tvshow.crawlers.douban import crawl_dou_list
from tvshow.crawlers.local import crawl_local, process_file
from tvshow.crawlers.tmdb import get_tmdb_tv_show, get_tmdb_tv_show_season
from tvshow.matching import combine_tv_show, get_missing_tv_shows
from tvshow.models import TvShow
from tvshow.serializers import TvShowSerializer

_DOULIST_ALL = "https://www.douban.com/doulist/116238969/"
_DOULIST_RECENT = "https://www.douban.com/doulist/113919174/"

_LIBRARY_ROOT = {"tv": conf.TV_ROOT, "anime": conf.ANIME_ROOT}


def _is_retained_tv_show(tv_show: TvShow) -> bool:
    rate = tv_show.get_rate()
    # 200 votes ≈ TMDB /tv/top_rated lower tail; tighter than /movie/top_rated's
    # 300 because TV samples themselves are smaller.
    return rate.score > 7.5 and rate.votes > 200


def _is_retained_anime(tv_show: TvShow) -> bool:
    rate = tv_show.get_rate()
    # Same 300-vote floor as movies. TMDB anime tends to score lower than
    # Bangumi/MAL even for genre staples, so 7.5 is already lenient.
    return rate.score > 7.5 and rate.votes > 300


def _enrich_local_shows(shows: list) -> None:
    """Replace each local show's TMDB rate with live ``/tv/{id}``.

    MoviePilot's ``tvshow.nfo`` omits ``<votes>`` (parser defaults to 0) and
    even tmm's is a scrape-time snapshot that drifts from current TMDB. The
    retention check rides current-TMDB, so we always pull fresh — cache-hit
    on the warm path since :func:`refresh_all`'s :func:`_flush_tmdb` pre-
    warms ``/tv/{id}`` per show.
    """
    for show in shows:
        tmdb_show = get_tmdb_tv_show(show.tmdb_id)
        if tmdb_show is None:
            continue
        show.tmdb_rate = tmdb_show.get_rate()


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
    local_shows = crawl_local(conf.TV_ROOT)
    _enrich_local_shows(local_shows)
    return _diff(douban_tv_shows, local_shows, _is_retained_tv_show)


def anime_diff() -> dict:
    bangumi_shows = crawl_bangumi_tv_show_80()
    if not bangumi_shows:
        raise UpstreamUnavailable()
    local_shows = crawl_local(conf.ANIME_ROOT)
    _enrich_local_shows(local_shows)
    return _diff(bangumi_shows, local_shows, _is_retained_anime)


def _season_ref(season) -> dict:
    rate = getattr(season, "rate", None)
    return {
        "num": season.num,
        "name": season.name,
        "poster": getattr(season, "poster", None),
        "score": round(rate.score, 1) if rate is not None and rate.score > 0 else None,
    }


def series_gaps(library: str) -> list:
    """Per-show snapshot of local + missing + incomplete seasons.

    Each entry returns enough for the frontend's left-stack / right-tile
    layout:

      [{
          "show": <show>,                    # TMDB show w/ poster + score
          "local_seasons":    [{num, name, poster}, ...],  # what user has
          "missing_seasons":  [{num, name, poster}, ...],  # whole seasons gone
          "incomplete_seasons": [...]                       # behind-on-episodes
      }, ...]

    Posters for both lists come from TMDB seasons (matched by season number);
    local NFOs don't carry per-season images. Shows with nothing missing or
    behind are dropped — there's nothing to surface.
    """
    result = []
    for local_tv_show in crawl_local(_LIBRARY_ROOT[library]):
        tmdb_tv_show = get_tmdb_tv_show(local_tv_show.tmdb_id)
        if tmdb_tv_show is None:
            continue

        tmdb_seasons_by_num = {s.num: s for s in tmdb_tv_show.list_seasons()}

        missing_seasons = [
            _season_ref(s)
            for s in tmdb_tv_show.list_seasons()
            if local_tv_show.get_season(s.num) is None and _legal_season(s)
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

        if not missing_seasons and not incomplete_seasons:
            continue

        local_seasons = []
        for num in sorted(local_tv_show.seasons.keys()):
            tmdb_season = tmdb_seasons_by_num.get(num)
            if tmdb_season is None:
                continue
            local_seasons.append(_season_ref(tmdb_season))

        result.append(
            {
                "show": TvShowSerializer(tmdb_tv_show).data,
                "local_seasons": local_seasons,
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


# --- Ignore (skip-marker) management ------------------------------------
# A per-season ``checked_episode`` cutoff in the show's ``.mediaclawer.json``
# suppresses that season (shadow season) and every episode <= the cutoff
# from the gap list. These endpoints let the UI write that cutoff per season.


def _find_show_dir(root: str, tmdb_id: int) -> Optional[str]:
    """Directory of the ``tvshow.nfo`` whose tmdb ``uniqueid`` == ``tmdb_id``."""
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


def _gap_seasons(library: str, tmdb_id: int) -> Tuple[Optional[str], str, list]:
    """Locate the show and list its still-missing seasons + episode choices.

    Returns ``(show_dir, title, seasons)``; ``show_dir`` is ``None`` when no
    local ``tvshow.nfo`` matches ``tmdb_id``. The offered episodes mirror the
    gap rules in :func:`local_gaps` exactly — only TMDB ``_legal_episode``s
    beyond what is already present or already checked — so selecting a
    season's latest offered episode precisely closes that season's gap.
    """
    root = _LIBRARY_ROOT[library]
    show_dir = _find_show_dir(root, tmdb_id)
    if show_dir is None:
        return None, "", []

    try:
        local_tv_show = process_file(os.path.join(show_dir, "tvshow.nfo"))
    except (ET.ParseError, ValueError, TypeError, AttributeError):
        local_tv_show = None
    tmdb_tv_show = get_tmdb_tv_show(tmdb_id)
    if local_tv_show is None or tmdb_tv_show is None:
        return show_dir, "", []

    season_max = local_tv_show.map_season_max_episode()
    candidates = set(season_max)
    for tmdb_season in tmdb_tv_show.list_seasons():
        if local_tv_show.get_season(tmdb_season.num) is None and _legal_season(
            tmdb_season
        ):
            candidates.add(tmdb_season.num)

    seasons = []
    for num in sorted(candidates):
        tmdb_season = get_tmdb_tv_show_season(tmdb_id, num)
        if tmdb_season is None:
            continue
        local_max = season_max.get(num, 0)
        missing = [
            e
            for e in tmdb_season.list_episodes()
            if e.num > local_max and _legal_episode(e)
        ]
        if not missing:
            continue
        seasons.append(
            {
                "season_num": num,
                "season_name": tmdb_season.name,
                "local_max_episode": local_max,
                "latest_episode": max(e.num for e in missing),
                "episodes": [
                    {"num": e.num, "name": e.name, "date": e.get_date() or None}
                    for e in missing
                ],
            }
        )
    return show_dir, tmdb_tv_show.get_titles()[0], seasons


def ignore_options(library: str, tmdb_id: int) -> dict:
    """Seasons/episodes the user may choose to ignore (opened on demand)."""
    show_dir, title, seasons = _gap_seasons(library, tmdb_id)
    if show_dir is None:
        raise ShowNotFound()
    return {"title": title, "seasons": seasons}


def ignore_apply(library: str, tmdb_id: int, selections: list) -> dict:
    """Persist per-season ``checked_episode`` cutoffs to the show's JSON.

    ``selections`` is ``[{"season_num": int, "episode": int}, ...]``.
    ``fully_ignored`` is true iff every still-missing season was selected at
    or beyond its latest offered episode — the frontend uses it to close the
    poster without waiting for a rescan.
    """
    show_dir, _title, gap_seasons = _gap_seasons(library, tmdb_id)
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


# --- Alias bind (manual chinese-title supplement) -----------------------
# The "最新" tab lists ranked items missing locally. When the rank list is
# in chinese but a local nfo's <title> is in the original language (TMDB has
# no chinese translation for the item), text-similarity match in
# tvshow.matching can't connect the two. The bind endpoints let the user say
# "this rank item is actually that local show", and we append the rank
# title as an alias so future scans find the match without code changes.


def alias_targets(library: str) -> list:
    """All local shows usable as bind targets for a missing rank item.

    -> [{tmdb_id, title, year, poster}]. Sorted by title for stable UI.
    """
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
    """Append ``aliases`` to the show's ``.mediaclawer.json``.

    -> ``{bound: bool, added: int}``. ``added`` is the dedup'd count; bind
    is idempotent so re-clicking the same rank item is a no-op.
    """
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
