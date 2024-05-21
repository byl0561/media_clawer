import os

from movie.models.movie import LocalMovie, Rate, MovieSet
import xml.etree.ElementTree as ET


def crawl_local(movie_folder: str) -> list[LocalMovie]:
    movies = []

    for root, dirs, files in os.walk(movie_folder):
        for file in files:
            if file == 'movie.nfo':
                nfo_path = os.path.join(root, file)
                tree = ET.parse(nfo_path)
                root_element = tree.getroot()
                title = root_element.find('title').text
                original_title = root_element.find('originaltitle').text
                year = int(root_element.find('year').text)
                country_list = [country.text for country in root_element.findall('country')]
                poster = root_element.find('thumb').text
                tmdb_score = float(root_element.find("./ratings/rating[@name='themoviedb']/value").text)
                tmdb_votes = int(root_element.find("./ratings/rating[@name='themoviedb']/votes").text)
                tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)
                tmdb_set_id = int(root_element.find("./uniqueid[@type='tmdbSet']").text) if root_element.find(
                    "./uniqueid[@type='tmdbSet']") is not None else None
                tmdb_set_name = root_element.find('./set/name').text if root_element.find(
                    './set/name') is not None else None
                movies.append(LocalMovie(title, original_title, year, country_list, poster,
                                         Rate(tmdb_score, tmdb_votes, 'TMDB'), tmdb_id,
                                         MovieSet(tmdb_set_id, tmdb_set_name, 'TMDB')))

    return movies
