"""Local TV/anime library scanner (tinyMediaManager ``tvshow.nfo``).

Parsing rules unchanged; I/O plumbing shared via :mod:`core`.
"""
import glob
import os
import xml.etree.ElementTree as ET

from core import conf, scanning
from tvshow.models import LocalEpisode, LocalSeason, LocalShadowSeason, LocalTvShow, Rate


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

    alias = []
    if os.path.exists(os.path.join(root, "alias.txt")):
        with open(os.path.join(root, "alias.txt"), "r") as f:
            alias = f.read().splitlines()

    num_2_season_name = {}
    for child in root_element:
        if child.tag == "namedseason":
            num_2_season_name[int(child.attrib["number"])] = child.text

    season_num_2_episodes = {}
    shadow_episodes = []
    for child, _dirs, files in os.walk(root):
        for file in files:
            if file != "tvshow.nfo" and file != "season.nfo" and file.endswith(".nfo"):
                if "PART" in file or "part" in file:
                    continue
                tree = ET.parse(os.path.join(child, file))
                season_num = int(tree.find("season").text)
                episode_num = int(tree.find("episode").text)
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
                    LocalEpisode(episode_num, episode_title, episode_date, run_minus)
                )
                season_num_2_episodes[season_num] = episodes

            elif file == "checked_episode.txt":
                with open(os.path.join(child, "checked_episode.txt"), "r") as f:
                    checked_episode = int(f.readline())
                season_folder_name = child.split("/")[-1]

                # tmm 默认用 "Specials" 命名第 0 季；MoviePilot 默认用 "Season 0"。
                # 两者都规范化为 Specials 语义，保持下游展示一致。
                if season_folder_name in ("Specials", "Season 0"):
                    shadow_episodes.append(
                        LocalShadowSeason(0, "Specials", checked_episode)
                    )
                else:
                    season_num = int(season_folder_name.replace("Season ", ""))
                    shadow_episodes.append(
                        LocalShadowSeason(
                            season_num, season_folder_name, checked_episode
                        )
                    )

    seasons = []
    for season_num, episodes in season_num_2_episodes.items():
        episodes = sorted(episodes, key=lambda e: e.num)
        seasons.append(
            LocalSeason(season_num, num_2_season_name.get(season_num), episodes)
        )

    seasons = sorted(seasons, key=lambda s: s.num)
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
    )


def crawl_local(root: str) -> list:
    return scanning.scan_files(root, file_filter, process_file)
