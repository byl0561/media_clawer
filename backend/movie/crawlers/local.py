"""Local movie library scanner (tinyMediaManager ``movie.nfo`` files).

Parsing rules unchanged; only the I/O plumbing (process pool, config) is now
shared via :mod:`core`.
"""
import glob
import os
import re
import xml.etree.ElementTree as ET

from core import conf, scanning
from movie.models import LocalMovie, MovieSet, Rate


def file_filter(file: str) -> bool:
    return file == "movie.nfo"


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
    year = int(re.search(r"\((\d{4})\)", root.split("/")[-1]).group(1))
    country_list = [country.text for country in root_element.findall("country")]
    tmdb_score = float(
        root_element.find("./ratings/rating[@name='themoviedb']/value").text
    )
    tmdb_votes = int(
        root_element.find("./ratings/rating[@name='themoviedb']/votes").text
    )
    tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)
    tmdb_set_id = (
        int(root_element.find("./uniqueid[@type='tmdbSet']").text)
        if root_element.find("./uniqueid[@type='tmdbSet']") is not None
        else None
    )
    tmdb_set_name = (
        root_element.find("./set/name").text
        if root_element.find("./set/name") is not None
        else (
            root_element.find("set").text
            if root_element.find("set") is not None
            else None
        )
    )

    poster = None
    cover_files = glob.glob(os.path.join(glob.escape(root), "poster.*"))
    if len(cover_files) > 0:
        poster = cover_files[0].replace(conf.MOVIE_ROOT, "")
        poster = f"/movie/poster/{poster}"

    return LocalMovie(
        title,
        original_title,
        year,
        country_list,
        poster,
        Rate(tmdb_score, tmdb_votes, "TMDB"),
        tmdb_id,
        MovieSet(tmdb_set_id, tmdb_set_name, "TMDB"),
    )


def crawl_local(root: str) -> list:
    return scanning.scan_files(root, file_filter, process_file)
