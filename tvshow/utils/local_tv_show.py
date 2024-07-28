import glob
import os
import xml.etree.ElementTree as ET

from constant import tv_folder, anime_folder
from tvshow.models.tvshow import *
from utils import file_utils


def file_filter(file: str) -> bool:
    return file == 'tvshow.nfo'


def process_file(path: str):
    root, file = os.path.split(path)

    if not file_filter(file):
        return None

    nfo_path = os.path.join(root, file)
    tree = ET.parse(nfo_path)
    root_element = tree.getroot()
    title = root_element.find('title').text
    original_title = root_element.find('originaltitle').text
    year = int(root_element.find('year').text)
    tmdb_score = float(root_element.find('rating').text) if root_element.find('rating') is not None else float(
        root_element.find("./ratings/rating[@name='themoviedb']/value").text)
    tmdb_votes = int(root_element.find('votes').text) if root_element.find('votes') is not None else int(
        root_element.find("./ratings/rating[@name='themoviedb']/votes").text)
    tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)

    poster = None
    pattern = os.path.join(glob.escape(root), 'poster.*')
    cover_files = glob.glob(pattern)
    if len(cover_files) > 0:
        poster = cover_files[0]
        if poster.startswith(tv_folder):
            poster = poster.replace(tv_folder, '')
            poster = f'/tv/poster/{poster}'
        elif poster.startswith(anime_folder):
            poster = poster.replace(anime_folder, '')
            poster = f'/anime/poster/{poster}'

    alias = []
    if os.path.exists(os.path.join(root, 'alias.txt')):
        with open(os.path.join(root, 'alias.txt'), 'r') as f:
            alias = f.readlines()

    num_2_season_name = dict()
    for child in root_element:
        if child.tag == 'namedseason':
            num_2_season_name[int(child.attrib['number'])] = child.text

    season_num_2_episodes = dict()
    shadow_episodes = list()
    for child, dirs, files in os.walk(root):
        for file in files:
            if file != 'tvshow.nfo' and file != 'season.nfo' and file.endswith('.nfo'):
                if 'PART' in file or 'part' in file:
                    continue
                nfo_path = os.path.join(child, file)
                tree = ET.parse(nfo_path)
                season_num = int(tree.find('season').text)
                episode_num = int(tree.find('episode').text)
                episode_title = tree.find('title').text
                episode_date = tree.find('premiered').text if tree.find('premiered') is not None else (
                    tree.find('aired').text if tree.find('aired') is not None else None)
                run_minus = int(tree.find('runtime').text)

                episodes = season_num_2_episodes.get(season_num, [])
                episodes.append(LocalEpisode(episode_num, episode_title, episode_date, run_minus))
                season_num_2_episodes[season_num] = episodes

            elif file == 'checked_episode.txt':
                checked_episode = 0
                with open(os.path.join(child, 'checked_episode.txt'), 'r') as f:
                    checked_episode = int(f.readline())
                season_folder_name = child.split('/')[-1]

                if season_folder_name == 'Specials':
                    shadow_episodes.append(LocalShadowSeason(0, 'Specials', checked_episode))
                else:
                    season_num = int(season_folder_name.replace('Season ', ''))
                    shadow_episodes.append(LocalShadowSeason(season_num, season_folder_name, checked_episode))

    seasons = list()
    for season_num, episodes in season_num_2_episodes.items():
        episodes = sorted(episodes, key=lambda x: x.num)
        seasons.append(LocalSeason(season_num, num_2_season_name.get(season_num), episodes))

    seasons = sorted(seasons, key=lambda x: x.num)
    return LocalTvShow(title, original_title, alias, year, poster,
                                Rate(tmdb_score, tmdb_votes, 'TMDB'), tmdb_id,
                                seasons, shadow_episodes)


def crawl_local(tv_show_folder: str) -> list[LocalTvShow]:
    return file_utils.mapping_file_to_object(tv_show_folder, file_filter, process_file)
