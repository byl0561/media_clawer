"""Local TV/anime library scanner (tinyMediaManager ``tvshow.nfo``).

Parsing rules unchanged; I/O plumbing shared via :mod:`core`.
"""
import glob
import os
import re
import xml.etree.ElementTree as ET

from core import conf, scanning
from core.local_config import read_config
from core.media_probe import VIDEO_EXTS
from tvshow.models import LocalEpisode, LocalSeason, LocalShadowSeason, LocalTvShow, Rate

# Season folder naming: tmm uses "Specials" for season 0, MoviePilot/Plex
# both use "Season N" (or "Season 0" for specials). The subtitle-gap surface
# uses this to find season folders that exist on disk but contain no video.
_SEASON_DIR_RE = re.compile(r"^(?:Specials|Season\s+(\d+))$")


def file_filter(file: str) -> bool:
    return file == "tvshow.nfo"


def process_file(path: str):
    root, file = os.path.split(path)
    if not file_filter(file):
        return None

    tree = ET.parse(os.path.join(root, file))
    root_element = tree.getroot()
    title = root_element.find("title").text
    original_title = (
        root_element.find("originaltitle").text
        if root_element.find("originaltitle") is not None
        else title
    )
    year = int(root_element.find("year").text)
    tmdb_score = (
        float(root_element.find("rating").text)
        if root_element.find("rating") is not None
        else float(root_element.find("./ratings/rating[@name='themoviedb']/value").text)
    )
    # MoviePilot 有的版本只写顶层 <rating>，没有 <votes>，也没有 tmm 的 <ratings> 嵌套块。
    # votes 完全缺失时记 0，避免整份 NFO 因此被跳过。
    flat_votes = root_element.find("votes")
    tmm_votes = root_element.find("./ratings/rating[@name='themoviedb']/votes")
    if flat_votes is not None:
        tmdb_votes = int(flat_votes.text)
    elif tmm_votes is not None:
        tmdb_votes = int(tmm_votes.text)
    else:
        tmdb_votes = 0
    tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)

    poster = None
    cover_files = glob.glob(os.path.join(glob.escape(root), "poster.*"))
    if len(cover_files) > 0:
        poster = cover_files[0]
        if poster.startswith(conf.TV_ROOT):
            poster = "/v1/tv-shows/poster/" + poster.replace(conf.TV_ROOT, "")
        elif poster.startswith(conf.ANIME_ROOT):
            poster = "/v1/anime/poster/" + poster.replace(conf.ANIME_ROOT, "")

    # Per-folder user config (aliases for fuzzy match + per-season
    # ``checked_episode`` cutoffs that suppress outstanding-episode gaps).
    # On first read, legacy ``alias.txt`` and ``Season N/checked_episode.txt``
    # files in this folder are migrated into the JSON and deleted.
    config = read_config(root)
    alias = list(config.get("aliases") or [])

    shadow_episodes = []
    for season_str, season_cfg in (config.get("seasons") or {}).items():
        try:
            num = int(season_str)
        except (TypeError, ValueError):
            continue
        if not isinstance(season_cfg, dict):
            continue
        checked = season_cfg.get("checked_episode")
        if not isinstance(checked, int):
            continue
        name = "Specials" if num == 0 else f"Season {num}"
        shadow_episodes.append(LocalShadowSeason(num, name, checked))

    num_2_season_name = {}
    for child in root_element:
        if child.tag == "namedseason":
            num_2_season_name[int(child.attrib["number"])] = child.text

    # Dedup by (season, episode) so a split-into-parts episode (one NFO per
    # part, e.g., `... - S06E23-PART1 - 求婚记.nfo` + `...-PART2-...nfo`) is
    # counted once. The previous skip-anything-with-"PART" filter dropped
    # episodes that only ship with PART NFOs (no aggregate NFO).
    season_num_2_episodes: dict = {}
    seen: set = set()
    for child, _dirs, files in os.walk(root):
        for file in files:
            if file == "tvshow.nfo" or file == "season.nfo" or not file.endswith(".nfo"):
                continue
            nfo_path = os.path.join(child, file)
            tree = ET.parse(nfo_path)
            season_num = int(tree.find("season").text)
            episode_num = int(tree.find("episode").text)
            if (season_num, episode_num) in seen:
                continue
            seen.add((season_num, episode_num))
            # Locate the matching video file (same basename, different ext)
            # so the subtitle probe can hit it directly without walking again.
            base = os.path.splitext(nfo_path)[0]
            video_path = None
            for ext in VIDEO_EXTS:
                candidate = base + ext
                if os.path.exists(candidate):
                    video_path = candidate
                    break
            episode_title = tree.find("title").text
            episode_date = (
                tree.find("premiered").text
                if tree.find("premiered") is not None
                else (
                    tree.find("aired").text
                    if tree.find("aired") is not None
                    else None
                )
            )
            # MoviePilot 的剧集 nfo 不写 <runtime>；缺失记 0，
            # 该字段只是透传到模型字段，前端没有依赖。
            runtime_el = tree.find("runtime")
            run_minus = int(runtime_el.text) if runtime_el is not None else 0

            episodes = season_num_2_episodes.get(season_num, [])
            episodes.append(
                LocalEpisode(
                    episode_num, episode_title, episode_date, run_minus,
                    video_path=video_path,
                )
            )
            season_num_2_episodes[season_num] = episodes

    seasons = []
    for season_num, episodes in season_num_2_episodes.items():
        episodes = sorted(episodes, key=lambda e: e.num)
        seasons.append(
            LocalSeason(season_num, num_2_season_name.get(season_num), episodes)
        )

    seasons = sorted(seasons, key=lambda s: s.num)

    # Season folders that exist on disk but have no video at all — the show
    # was scraped + a season folder created, but the episodes never landed.
    # Seasons with at least one real episode are handled by the per-episode
    # subtitle check and excluded here.
    empty_seasons = []
    try:
        entries = os.listdir(root)
    except OSError:
        entries = []
    for entry in entries:
        sub = os.path.join(root, entry)
        if not os.path.isdir(sub):
            continue
        m = _SEASON_DIR_RE.match(entry)
        if not m:
            continue
        num = 0 if entry == "Specials" else int(m.group(1))
        if num in season_num_2_episodes:
            continue
        try:
            sub_entries = os.listdir(sub)
        except OSError:
            continue
        if any(
            os.path.splitext(name)[1].lower() in VIDEO_EXTS for name in sub_entries
        ):
            continue
        empty_seasons.append(num)

    return LocalTvShow(
        title,
        original_title,
        alias,
        year,
        poster,
        Rate(tmdb_score, tmdb_votes, "TMDB"),
        tmdb_id,
        seasons,
        shadow_episodes,
        path=root,
        empty_seasons=empty_seasons,
    )


def crawl_local(root: str) -> list:
    return scanning.scan_files(root, file_filter, process_file)
