import os
import traceback
import xml.etree.ElementTree as ET

from tvshow.models.tvshow import *


def crawl_local(tv_show_folder: str) -> list[LocalTvShow]:
    tv_shows = []

    for root, dirs, files in os.walk(tv_show_folder):
        for file in files:
            if file == 'tvshow.nfo':
                nfo_path = os.path.join(root, file)
                try:
                    tree = ET.parse(nfo_path)
                    root_element = tree.getroot()
                    title = root_element.find('title').text
                    original_title = root_element.find('originaltitle').text
                    year = int(root_element.find('year').text)
                    poster = root_element.find('thumb').text
                    tmdb_score = float(root_element.find('rating').text) if root_element.find('rating') is not None else float(root_element.find("./ratings/rating[@name='themoviedb']/value").text)
                    tmdb_votes = int(root_element.find('votes').text) if root_element.find('votes') is not None else int(root_element.find("./ratings/rating[@name='themoviedb']/votes").text)
                    tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)

                    num_2_season_name = dict()
                    for child in root_element:
                        if child.tag == 'namedseason':
                            num_2_season_name[int(child.attrib['number'])] = child.text

                    season_num_2_episodes = dict()
                    for child, dirs, files in os.walk(root):
                        for file in files:
                            if file != 'tvshow.nfo' and file != 'season.nfo' and file.endswith('.nfo'):
                                nfo_path = os.path.join(child, file)
                                try:
                                    tree = ET.parse(nfo_path)
                                    season_num = int(tree.find('season').text)
                                    episode_num = int(tree.find('episode').text)
                                    episode_title = tree.find('title').text
                                    episode_date = tree.find('premiered').text
                                    run_minus = int(tree.find('runtime').text)

                                    episodes = season_num_2_episodes.get(season_num, [])
                                    episodes.append(LocalEpisode(episode_num, episode_title, episode_date, run_minus))
                                    season_num_2_episodes[season_num] = episodes
                                except Exception as e:
                                    traceback.print_exc()
                                    print(e)
                                    print(nfo_path)

                    seasons = list()
                    for season_num, episodes in season_num_2_episodes.items():
                        episodes = sorted(episodes, key=lambda x: x.num)
                        seasons.append(LocalSeason(season_num, num_2_season_name.get(season_num), episodes))

                    seasons = sorted(seasons, key=lambda x: x.num)
                    tv_shows.append(LocalTvShow(title, original_title, year, poster,
                                                Rate(tmdb_score, tmdb_votes, 'TMDB'), tmdb_id,
                                                seasons))
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    print(nfo_path)
    return tv_shows
