import glob
import os
import re
import xml.etree.ElementTree as ET

from constant import movie_folder
from movie.models.movie import LocalMovie, Rate, MovieSet
from utils import file_utils


def file_filter(file: str) -> bool:
    return file == 'movie.nfo'


def process_file(path: str):
    root, file = os.path.split(path)

    if not file_filter(file):
        return None

    nfo_path = os.path.join(root, file)
    tree = ET.parse(nfo_path)
    root_element = tree.getroot()
    title = root_element.find('title').text
    original_title = root_element.find('originaltitle').text if root_element.find('originaltitle') is not None else title
    year = int(re.search(r'\((\d{4})\)', root.split('/')[-1]).group(1))
    country_list = [country.text for country in root_element.findall('country')]
    tmdb_score = float(root_element.find("./ratings/rating[@name='themoviedb']/value").text)
    tmdb_votes = int(root_element.find("./ratings/rating[@name='themoviedb']/votes").text)
    tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)
    tmdb_set_id = int(root_element.find("./uniqueid[@type='tmdbSet']").text) if root_element.find(
        "./uniqueid[@type='tmdbSet']") is not None else None
    tmdb_set_name = root_element.find('./set/name').text if root_element.find(
        './set/name') is not None else (
        root_element.find('set').text if root_element.find('set') is not None else None)

    poster = None
    pattern = os.path.join(glob.escape(root), 'poster.*')
    cover_files = glob.glob(pattern)
    if len(cover_files) > 0:
        poster = cover_files[0].replace(movie_folder, '')
        poster = f'/movie/poster/{poster}'
    return LocalMovie(title, original_title, year, country_list, poster,
                      Rate(tmdb_score, tmdb_votes, 'TMDB'), tmdb_id,
                      MovieSet(tmdb_set_id, tmdb_set_name, 'TMDB'))


def crawl_local(movie_folder: str) -> list[LocalMovie]:
    return file_utils.mapping_file_to_object(movie_folder, file_filter, process_file)
